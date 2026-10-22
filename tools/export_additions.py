"""Sabah only: export today's additions into seed_data/additions.json
   python tools/export_additions.py            -> preview only
   python tools/export_additions.py --write    -> writes the file"""
import os, sys, json, django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
django.setup()
from django.apps import apps
from django.db import models as dj
from additions_lib import row, key

WRITE = '--write' in sys.argv
Exp = apps.get_model('explore.experience')
Dest = apps.get_model('explore.destination')
Pin = apps.get_model('explore.mappin')

def val(obj, name):
    return row(obj)['fields'].get(name)

experiences = []
for e in Exp.objects.order_by('pk'):
    cat = str(getattr(e, 'category', '') or '').lower()
    experiences.append({'slug': e.slug, 'name': e.name, 'nature': 'nature' in cat,
                        'latitude': val(e, 'latitude'), 'longitude': val(e, 'longitude')})
destinations = []
for d in Dest.objects.filter(region__slug='north').order_by('pk'):
    r = row(d)['fields']
    destinations.append({'slug': d.slug, 'name': d.name, **{k: r.get(k) for k in ('description', 'latitude', 'longitude', 'price')}})
pins = [row(p) for p in Pin.objects.order_by('pk')]
gallery_model, gallery = None, []
for M in apps.get_app_config('explore').get_models():
    for f in M._meta.fields:
        if isinstance(f, dj.FileField) and isinstance(f.upload_to, str) and f.upload_to.startswith('gallery'):
            gallery_model = M._meta.label_lower
            gallery = [row(g) for g in M.objects.order_by('pk')]
            break
    if gallery_model:
        break

print('experiences:', len(experiences), '| with coordinates:', sum(1 for e in experiences if e['latitude'] not in (None, '0', '0.0', 0)))
print('   treated as YOUR pages (Nature), these will overwrite coordinates:', [e['name'] for e in experiences if e['nature']])
print('north places:', len(destinations), [d['name'] for d in destinations])
print('map pins:', len(pins), [p['fields'].get('name') for p in pins])
print('gallery photos:', len(gallery), '(' + str(gallery_model) + ')', [g['fields'].get('image') for g in gallery])
data = {'experiences': experiences, 'destinations': destinations, 'map_pins': pins,
        'gallery_model': gallery_model, 'gallery': gallery}
print('')
if not WRITE:
    print('Preview only. Nothing written. If the lists above are right, run again with --write')
else:
    with open('seed_data/additions.json', 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print('written seed_data/additions.json')
