"""Copy YOUR pages from your own old laptop database into the shared Supabase database.
   Run it from the project folder, with your .env in place (so Django talks to Supabase).

   python tools/push_my_pages.py --from db_mine_backup.sqlite3 --who sabah            -> PREVIEW, changes nothing
   python tools/push_my_pages.py --from db_mine_backup.sqlite3 --who sabah --apply    -> does it

   It NEVER deletes anything.
   * A row that exists in your file but not in Supabase is ADDED (events, cards, pins, photos...).
   * A row that exists in both is left alone, EXCEPT on pages that belong to you (see --who):
     there your version wins, but a filled-in value is never replaced by a blank one.
   * Rows are matched by slug / name, never by id number."""
import os, sys, json, argparse, datetime
from decimal import Decimal

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
import django
django.setup()
from django.apps import apps
from django.conf import settings
from django.db import connections, transaction, models as dj

PRESETS = {
    'aliyah':   ['experience:category=food'],
    'tisha':    ['destination:region=west'],
    'sabah':    ['experience:category=nature', 'destination:region=north'],
    'mithili':  ['experience:category=culture', 'destination:region=south'],
    'haya':     ['destination:region=east'],
    'nusaibah': [],
}
SKIP_MODELS = {'booking', 'payment'}

ap = argparse.ArgumentParser()
ap.add_argument('--from', dest='src', required=True, help='your old database file, e.g. db_mine_backup.sqlite3')
ap.add_argument('--who', default='', help='your first name: ' + ', '.join(sorted(PRESETS)))
ap.add_argument('--own', action='append', default=[], help='extra page you own, e.g. experience:category=food')
ap.add_argument('--apply', action='store_true')
ap.add_argument('--allow-sqlite', action='store_true', help=argparse.SUPPRESS)
args = ap.parse_args()
APPLY = args.apply

src_path = os.path.abspath(args.src)
if not os.path.exists(src_path):
    sys.exit('STOP: cannot find ' + src_path)
default_cfg = settings.DATABASES['default']
if 'sqlite' in default_cfg['ENGINE'] and not args.allow_sqlite:
    sys.exit('STOP: this laptop is NOT connected to Supabase (is the .env file next to manage.py?). Nothing was done.')
if 'sqlite' in default_cfg['ENGINE'] and os.path.abspath(str(default_cfg['NAME'])) == src_path:
    sys.exit('STOP: the source file is the same database as the target. Nothing was done.')
who = args.who.strip().lower()
if who and who not in PRESETS:
    sys.exit('STOP: --who must be one of: ' + ', '.join(sorted(PRESETS)))
rules = []
for spec in PRESETS.get(who, []) + args.own:
    m, rest = spec.split(':', 1)
    fk, sub = rest.split('=', 1)
    rules.append((m.strip().lower(), fk.strip(), sub.strip().lower()))

cfg = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': src_path}
cfg = connections.configure_settings({'default': {'ENGINE': 'django.db.backends.dummy'}, 'mine': cfg})['mine']
connections.settings['mine'] = cfg
try:
    connections['mine'].ensure_connection()
except Exception as e:
    sys.exit('STOP: cannot open ' + src_path + ': ' + repr(e))

print('Target (shared database):', default_cfg.get('HOST') or default_cfg.get('NAME'))
print('Source (your old file)  :', src_path)
print('Your pages (may be changed):', [r[0] + ' where ' + r[1] + ' contains "' + r[2] + '"' for r in rules] or 'none - add-only')
print('')

def plain_fields(M):
    out = []
    for f in M._meta.concrete_fields:
        if f.is_relation or f.primary_key:
            continue
        if getattr(f, 'auto_now', False) or getattr(f, 'auto_now_add', False):
            continue
        out.append(f)
    return out

def fk_fields(M):
    return [f for f in M._meta.concrete_fields if f.is_relation]

def has_slug(M):
    return any(f.name == 'slug' for f in M._meta.fields)

def norm(v):
    if v is None:
        return None
    if hasattr(v, 'storage'):
        return v.name or ''
    if isinstance(v, Decimal):
        return format(v.normalize(), 'f')
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    return v

def blank(v):
    return v is None or v == '' or (isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0) or str(v) in ('0', '0.0', '0.00', '0.000000')

def read_rows(M, db):
    fks = fk_fields(M)
    qs = M.objects.using(db).all()
    if fks:
        qs = qs.select_related(*[f.name for f in fks])
    rows = []
    for obj in qs:
        py = {f.name: (f.value_from_object(obj)) for f in plain_fields(M)}
        cmp_ = {k: norm(v) for k, v in py.items()}
        link = {}
        for f in fks:
            t = getattr(obj, f.name)
            link[f.name] = None if t is None else t.slug
        if has_slug(M):
            key = (('slug', cmp_['slug']),)
        else:
            key = tuple((n, link[n]) for n in sorted(link))
            for pref in ('name', 'title', 'image'):
                if pref in cmp_:
                    key += ((pref, str(cmp_[pref])),)
                    break
            else:
                key += (('all', json.dumps(cmp_, sort_keys=True, default=str)),)
        rows.append({'key': key, 'py': py, 'cmp': cmp_, 'fks': link, 'obj': obj,
                     'label': str(obj)[:50] if str(obj) and not str(obj).endswith(' object (' + str(obj.pk) + ')') else ', '.join(str(x) for _, x in key)[:50]})
    return rows

def in_scope(M, r):
    name = M._meta.model_name
    for m, fk, sub in rules:
        if m == name and sub in (r['fks'].get(fk) or '').lower():
            return True
    return False

all_models = [M for M in apps.get_app_config('explore').get_models() if M._meta.model_name not in SKIP_MODELS]
usable, notes = [], []
for M in all_models:
    bad = [f.name for f in fk_fields(M) if not any(x.name == 'slug' for x in f.related_model._meta.fields)]
    if bad:
        notes.append('skipped ' + M._meta.model_name + ' (links to something without a slug: ' + ', '.join(bad) + ')')
        continue
    if any(f.many_to_many for f in M._meta.get_fields() if hasattr(f, 'many_to_many') and f.concrete):
        notes.append('note: ' + M._meta.model_name + ' has many-to-many links; those are NOT copied')
    usable.append(M)

ordered, pending = [], list(usable)
while pending:
    progressed = False
    for M in list(pending):
        deps = {f.related_model for f in fk_fields(M) if f.related_model is not M and f.related_model in usable}
        if all(d in ordered for d in deps):
            ordered.append(M); pending.remove(M); progressed = True
    if not progressed:
        ordered.extend(pending); break

slug_cache = {}
def slugs(RM):
    if RM not in slug_cache:
        slug_cache[RM] = {s: pk for s, pk in RM.objects.using('default').values_list('slug', 'pk')}
    return slug_cache[RM]

total_new = total_upd = 0
media_needed = set()
lines = []

def run():
    global total_new, total_upd
    for M in ordered:
        name = M._meta.model_name
        src_rows = read_rows(M, 'mine')
        dst_rows = read_rows(M, 'default')
        dst = {r['key']: r for r in dst_rows}
        creates, updates, same, skipped = [], [], 0, []
        for r in src_rows:
            d = dst.get(r['key'])
            if d is None:
                missing = [(n, s) for n, s in r['fks'].items() if s is not None and s not in slugs(M._meta.get_field(n).related_model)]
                if missing:
                    skipped.append((r, missing)); continue
                creates.append(r)
                continue
            if not in_scope(M, r):
                same += 1; continue
            changes = []
            for n, new in r['cmp'].items():
                cur = d['cmp'].get(n)
                if cur != new:
                    if blank(new) and not blank(cur):
                        continue
                    changes.append((n, cur, new))
            for n, new in r['fks'].items():
                cur = d['fks'].get(n)
                if cur != new and not (new is None and cur is not None):
                    if new is not None and new not in slugs(M._meta.get_field(n).related_model):
                        continue
                    changes.append((n, cur, new))
            if changes:
                updates.append((d, r, changes))
            else:
                same += 1
        if creates or updates or skipped:
            lines.append('== ' + name + ': ' + str(len(creates)) + ' new, ' + str(len(updates)) + ' changed (yours), ' + str(same) + ' already the same' + (', ' + str(len(skipped)) + ' skipped' if skipped else ''))
            for r in creates[:25]:
                lines.append('     + new   ' + r['label'])
            if len(creates) > 25:
                lines.append('     + ... and ' + str(len(creates) - 25) + ' more new')
            for d, r, ch in updates[:40]:
                lines.append('     ~ change ' + r['label'] + ' | ' + '; '.join(c[0] + ': ' + str(c[1])[:25] + ' -> ' + str(c[2])[:25] for c in ch[:4]) + (' ...' if len(ch) > 4 else ''))
            for r, miss in skipped[:10]:
                lines.append('     ! skipped ' + r['label'] + ' (needs ' + ', '.join(n + '=' + s for n, s in miss) + ' which is not in the shared database)')
        total_new += len(creates); total_upd += len(updates)
        for r in creates + [u[1] for u in updates]:
            for f in plain_fields(M):
                if isinstance(f, dj.FileField) and r['cmp'].get(f.name):
                    media_needed.add(r['cmp'][f.name])
        if APPLY:
            objs = []
            for r in creates:
                kw = dict(r['py'])
                for f in fk_fields(M):
                    s = r['fks'][f.name]
                    kw[f.attname] = None if s is None else slugs(f.related_model)[s]
                objs.append(M(**kw))
            if objs:
                M.objects.using('default').bulk_create(objs, batch_size=100)
                slug_cache.pop(M, None)
            for d, r, ch in updates:
                obj = d['obj']
                names = []
                for n, cur, new in ch:
                    f = M._meta.get_field(n)
                    if f.is_relation:
                        setattr(obj, f.attname, None if new is None else slugs(f.related_model)[new]); names.append(f.attname)
                    else:
                        setattr(obj, n, r['py'][n]); names.append(n)
                obj.save(using='default', update_fields=names)
        else:
            if has_slug(M) and creates:
                slug_cache.setdefault(M, {})
                for r in creates:
                    slug_cache[M][r['cmp']['slug']] = None

try:
    if APPLY:
        with transaction.atomic(using='default'):
            run()
    else:
        run()
except Exception as e:
    print('')
    print('FAILED - NOTHING was changed in the shared database.')
    print('Reason:', repr(e)[:600])
    sys.exit(1)

for l in lines:
    print(l)
for n in notes:
    print(n)
if not lines:
    print('Nothing to do: the shared database already has everything from your file.')
print('')
missing_local = sorted(f for f in media_needed if not os.path.exists(os.path.join(str(settings.MEDIA_ROOT), f)))
if media_needed:
    print(len(media_needed), 'photo file(s) are used by these rows.')
    if missing_local:
        print('WARNING: not found in your media folder (the photo will be missing on the site):')
        for f in missing_local[:15]:
            print('   ', f)
    print('After --apply, upload the photos with:  python tools/upload_media.py --apply')
print('')
if not APPLY:
    print('PREVIEW ONLY:', total_new, 'to add,', total_upd, 'to change. NOTHING was changed. Run again with --apply to do it.')
else:
    print('DONE:', total_new, 'added,', total_upd, 'changed. Nothing was deleted.')
