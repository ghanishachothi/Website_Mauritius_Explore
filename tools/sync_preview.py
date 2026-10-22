"""Safe look before syncing: changes NOTHING. Shows what tools/team_sync.py would replace or remove on this laptop."""
import os, sys, json, django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
django.setup()
from django.apps import apps
from django.core import serializers

FILES = ['part_categories', 'part_experiences', 'part_north', 'part_south_places', 'part_guides',
         'part_guide_reviews', 'part_packages', 'part_map_pins', 'part_gallery']
data = {}
for name in FILES:
    p = 'seed_data/' + name + '.json'
    if os.path.exists(p):
        data[p] = json.load(open(p, encoding='utf-8'))

def short(v):
    s = str(v).replace('\n', ' ')
    return s if len(s) <= 40 else s[:37] + '...'

def empty(v):
    return v is None or v == '' or v == []

replaced, removed = [], []
for p, rows in data.items():
    for label in sorted({r['model'] for r in rows}):
        try:
            Model = apps.get_model(label)
        except LookupError:
            print('(model', label, 'not found - did you run migrate?)')
            continue
        want = {r['pk']: r['fields'] for r in rows if r['model'] == label}
        for obj in Model.objects.filter(pk__in=list(want)):
            have = json.loads(serializers.serialize('json', [obj]))[0]['fields']
            for k, v in want[obj.pk].items():
                if k in have and have[k] != v and not empty(have[k]):
                    replaced.append(label + ' #' + str(obj.pk) + ' ' + str(obj)[:30] + ' | ' + k + ': yours "' + short(have[k]) + '" -> team "' + short(v) + '"')

def inside(file_part, label):
    p = 'seed_data/' + file_part + '.json'
    return {r['pk'] for r in data.get(p, []) if r['model'] == label}

checks = [
    ('explore.package', 'part_packages', {}), ('explore.guidereview', 'part_guide_reviews', {}),
    ('explore.guide', 'part_guides', {}), ('explore.experience', 'part_experiences', {}),
    ('explore.destination', 'part_north', {'region__slug': 'north'}),
    ('explore.destination', 'part_south_places', {'region__slug': 'south'}),
    ('explore.regionhighlight', 'part_north', {'region__slug': 'north'}),
]
for label, f, scope in checks:
    if 'seed_data/' + f + '.json' not in data:
        continue
    for obj in apps.get_model(label).objects.filter(**scope).exclude(pk__in=inside(f, label)):
        removed.append(label + ' #' + str(obj.pk) + ' ' + str(obj)[:50])

print('')
print('=== Things on YOUR laptop that the sync would REPLACE with the team version ===')
for x in replaced[:60]:
    print(' ', x)
if len(replaced) > 60:
    print('  ... and', len(replaced) - 60, 'more')
if not replaced:
    print('  none')
print('')
print('=== Things on YOUR laptop that are not in the team files, so the sync would REMOVE them ===')
for x in removed[:60]:
    print(' ', x)
if len(removed) > 60:
    print('  ... and', len(removed) - 60, 'more')
if not removed:
    print('  none')
print('')
print('Nothing was changed. If a line above is something you want to keep, STOP and tell Ghanisha before syncing.')
