"""Everyone: add Sabah's new data to this laptop WITHOUT touching anything else.
   python tools/apply_additions.py            -> shows what it would do, changes nothing
   python tools/apply_additions.py --apply    -> does it
It never deletes anything and never changes a row it was not told about."""
import os, sys, json, django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
django.setup()
from django.apps import apps
from django.conf import settings
from django.db import transaction
from additions_lib import row, key

APPLY = '--apply' in sys.argv
data = json.load(open('seed_data/additions.json', encoding='utf-8'))
Exp = apps.get_model('explore.experience')
Dest = apps.get_model('explore.destination')
Pin = apps.get_model('explore.mappin')
todo = []

def conv(Model, name, v):
    return Model._meta.get_field(name).to_python(v)

def blank(v):
    return v is None or v == '' or (isinstance(v, (int, float)) and v == 0) or str(v) in ('0', '0.0', '0.000000')

# 1. experience coordinates: fill blanks; Nature cards (Sabah's pages) are overwritten
for e in data['experiences']:
    obj = Exp.objects.filter(slug=e['slug']).first()
    if obj is None:
        continue
    for name in ('latitude', 'longitude'):
        new = conv(Exp, name, e[name])
        if blank(new):
            continue
        cur = getattr(obj, name)
        if cur != new and (blank(cur) or e['nature']):
            todo.append(('set', obj, name, new, 'experience ' + obj.name + ' | ' + name + ': ' + str(cur) + ' -> ' + str(new)))

# 1b. Nature cards (Sabah's pages): every normal field is copied (text, price, photo name...). Other cards are never touched.
for e in data['experiences']:
    if not e.get('nature') or not e.get('fields'):
        continue
    obj = Exp.objects.filter(slug=e['slug']).first()
    if obj is None:
        continue
    for name, v in e['fields'].items():
        if name in ('slug', 'latitude', 'longitude'):
            continue
        try:
            f = Exp._meta.get_field(name)
        except Exception:
            continue
        if getattr(f, 'auto_now', False) or getattr(f, 'auto_now_add', False):
            continue
        new = f.to_python(v)
        cur = getattr(obj, name)
        cur = cur.name if hasattr(cur, 'storage') else cur
        new_cmp = new.name if hasattr(new, 'storage') else new
        if cur != new_cmp:
            todo.append(('set', obj, name, new_cmp, 'card ' + obj.name + ' | ' + name + ': ' + str(cur)[:30] + ' -> ' + str(new_cmp)[:30]))
            if hasattr(f, 'upload_to') and new_cmp and not os.path.exists(os.path.join(str(settings.MEDIA_ROOT), str(new_cmp))):
                print('WARNING: photo file missing on this laptop (git pull again?):', new_cmp)

# 2. North places (Sabah's pages): description, coordinates, price
for d in data['destinations']:
    obj = Dest.objects.filter(slug=d['slug']).first()
    if obj is None:
        print('(skipped: no place', d['slug'], 'on this laptop)')
        continue
    for name in ('description', 'latitude', 'longitude', 'price'):
        if name in d:
            new = conv(Dest, name, d[name])
            cur = getattr(obj, name)
            if cur != new:
                todo.append(('set', obj, name, new, 'place ' + obj.name + ' | ' + name + ': ' + str(cur)[:30] + ' -> ' + str(new)[:30]))

# 3. map pins and gallery photos: create only the ones that are missing
def add_rows(Model, rows, label):
    have = {key(row(o)) for o in Model.objects.all()}
    for r in rows:
        k = key(r)
        if k in have:
            continue
        kwargs = {n: conv(Model, n, v) for n, v in r['fields'].items()}
        ok = True
        for n, slug in r['fks'].items():
            if slug is None:
                kwargs[n] = None
                continue
            target = Model._meta.get_field(n).related_model.objects.filter(slug=slug).first()
            if target is None:
                print('(skipped', label, dict(k), '- no', n, slug, 'on this laptop)')
                ok = False
                break
            kwargs[n] = target
        if ok:
            todo.append(('create', Model, kwargs, 'add ' + label + ': ' + str(dict(k))))
            if label == 'gallery photo':
                img = kwargs.get('image')
                path = os.path.join(str(settings.MEDIA_ROOT), str(img))
                if img and not os.path.exists(path):
                    print('WARNING: photo file missing on this laptop (git pull again?):', path)

add_rows(Pin, data['map_pins'], 'map pin')
if data.get('gallery_model'):
    add_rows(apps.get_model(data['gallery_model']), data['gallery'], 'gallery photo')

print('')
for t in todo:
    print(' ', t[-1])
if not todo:
    print('  nothing to do - this laptop already has everything')
print('')
if not APPLY:
    print(len(todo), 'change(s) planned. NOTHING was changed. Run again with --apply to do them.')
else:
    with transaction.atomic():
        for t in todo:
            if t[0] == 'set':
                _, obj, name, new, _msg = t
                setattr(obj, name, new)
                obj.save(update_fields=[name])
            else:
                _, Model, kwargs, _msg = t
                Model(**kwargs).save()
    print('DONE:', len(todo), 'change(s) applied. Nothing was deleted.')
