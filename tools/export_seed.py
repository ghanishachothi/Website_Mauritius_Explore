"""Ghanisha only: export this laptop's database into seed_data/*.json.
   python tools/export_seed.py            -> preview only, writes nothing
   python tools/export_seed.py --write    -> writes the files"""
import os, sys, json, subprocess, django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
django.setup()
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.db import models as dj

WRITE = '--write' in sys.argv

def dump(label, **flt):
    qs = apps.get_model(label).objects.filter(**flt).order_by('pk')
    return json.loads(serializers.serialize('json', qs))

plan = [
    ('seed_data/part_experiences.json', {'explore.experience': dump('explore.experience')}),
    ('seed_data/part_north.json', {
        'explore.destination': dump('explore.destination', region__slug='north'),
        'explore.regionhighlight': dump('explore.regionhighlight', region__slug='north')}),
    ('seed_data/part_map_pins.json', {'explore.mappin': dump('explore.mappin')}),
]

gal = {}
for M in apps.get_app_config('explore').get_models():
    for f in M._meta.fields:
        if isinstance(f, dj.FileField) and isinstance(f.upload_to, str) and f.upload_to.startswith('gallery'):
            gal[M._meta.label_lower] = dump(M._meta.label_lower)
            break
if gal:
    print('gallery model(s) found:', ', '.join(gal))
    plan.append(('seed_data/part_gallery.json', gal))
else:
    print('no separate gallery model found (that is fine if the photos are fields on the cards)')
print('')

problems = 0
outputs = []
for path, owned in plan:
    old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []
    for m, rows in owned.items():
        o = {x['pk']: x['fields'] for x in old if x['model'] == m}
        n = {x['pk']: x['fields'] for x in rows}
        if o and not n:
            print('STOP:', path, 'has', len(o), m, 'rows but this database has none. Wrong database?')
            problems += 1
            continue
        added = sorted(set(n) - set(o))
        removed = sorted(set(o) - set(n))
        changed = [pk for pk in n if pk in o and n[pk] != o[pk]]
        fields = sorted({k for pk in changed for k in set(n[pk]) | set(o[pk]) if n[pk].get(k) != o[pk].get(k)})
        print(path, '|', m)
        print('   file had', len(o), '| database has', len(n), '| new rows', added, '| rows no longer in database', removed)
        print('   rows changed:', len(changed), '| fields that differ:', fields)
    keep = [x for x in old if x['model'] not in owned]
    new = keep + [x for rows in owned.values() for x in rows]
    outputs.append((path, new))

root = os.path.relpath(str(settings.MEDIA_ROOT), os.getcwd()).replace(os.sep, '/')
tracked = set(subprocess.run(['git', 'ls-files', root], capture_output=True, text=True).stdout.split('\n'))
need_add = set()
for path, new in outputs:
    for x in new:
        try:
            Model = apps.get_model(x['model'])
        except LookupError:
            continue
        for f in Model._meta.fields:
            if isinstance(f, dj.FileField):
                v = x['fields'].get(f.name)
                if v:
                    rel = root + '/' + v
                    if not os.path.exists(rel):
                        print('MISSING PHOTO on this laptop:', rel, '(', x['model'], x['pk'], ')')
                        problems += 1
                    elif rel not in tracked:
                        need_add.add(rel)
print('')
if need_add:
    print('Photos used by the data but NOT in git yet (run git add on each):')
    for r in sorted(need_add):
        print('   git add "' + r + '"')
else:
    print('All photos used by the data are already in git.')
print('')
if problems:
    print('Nothing written. Fix the STOP / MISSING lines above first.')
elif not WRITE:
    print('Preview only. Nothing written. If this looks right, run it again with --write')
else:
    for path, new in outputs:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(new, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
        print('written', path, '(', len(new), 'rows )')
