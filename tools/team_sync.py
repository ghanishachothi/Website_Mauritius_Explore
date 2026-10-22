import os, sys, json, django
if '--force' not in sys.argv:
    print('team_sync.py is switched off: it overwrites other people rows.')
    print('Use: python tools/apply_additions.py')
    sys.exit(1)
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mauritius_explore.settings')
django.setup()
from django.apps import apps
from django.core.management import call_command
from apps.explore.models import Destination, Event

def used_count(obj):
    n = 0
    for r in obj._meta.related_objects:
        if r.one_to_many or r.many_to_many:
            n += getattr(obj, r.get_accessor_name()).count()
    return n

def load(path):
    return json.load(open(path, encoding='utf-8'))

def pks(path, label):
    return {o['pk'] for o in load(path) if o['model'] == label}

C = 'seed_data/part_categories.json'
X = 'seed_data/part_experiences.json'
N = 'seed_data/part_north.json'
S = 'seed_data/part_south_places.json'
G = 'seed_data/part_guides.json'
R = 'seed_data/part_guide_reviews.json'
P = 'seed_data/part_packages.json'
M = 'seed_data/part_map_pins.json'
GL = 'seed_data/part_gallery.json'

keep = {
    'north_dest': pks(N, 'explore.destination'),
    'north_hl': pks(N, 'explore.regionhighlight'),
    'south_dest': pks(S, 'explore.destination'),
    'guide': pks(G, 'explore.guide'),
    'review': pks(R, 'explore.guidereview'),
    'package': pks(P, 'explore.package'),
    'experience': pks(X, 'explore.experience'),
}

# 1. clear rows that would clash on a unique slug with the incoming files
for path in (C, X, N, S, G, R, P):
    for o in load(path):
        if 'slug' not in o['fields']:
            continue
        Model = apps.get_model(o['model'])
        for old in Model.objects.filter(slug=o['fields']['slug']).exclude(pk=o['pk']):
            if used_count(old) == 0:
                print('deleted clashing', o['model'], old.pk, old.slug)
                old.delete()
            else:
                old.slug = old.slug + '-old-' + str(old.pk)
                old.save()
                print('renamed clashing (in use)', o['model'], old.pk, old.slug)

# 2. load every file, in the right order
for path in (C, X, N, S, G, R, P):
    call_command('loaddata', path)
for extra in (M, GL):
    if os.path.exists(extra):
        call_command('loaddata', extra)
keep_pins = set()
if os.path.exists(M):
    keep_pins = pks(M, 'explore.mappin')
    for pin in apps.get_model('explore.mappin').objects.exclude(pk__in=keep_pins):
        print('removed map pin', pin.pk, str(pin))
        pin.delete()

# 3. remove anything that is not in the files
kept_places = []
def prune(label, keepset, scope=None, collect=None):
    Model = apps.get_model(label)
    qs = Model.objects.all() if scope is None else Model.objects.filter(**scope)
    for obj in qs.exclude(pk__in=keepset):
        if used_count(obj) == 0:
            print('removed', label, obj.pk, str(obj))
            obj.delete()
        else:
            print('KEPT (still linked)', label, obj.pk, str(obj))
            if collect is not None:
                collect.append(obj)

prune('explore.package', keep['package'])
prune('explore.guidereview', keep['review'])
prune('explore.guide', keep['guide'])
prune('explore.experience', keep['experience'])
prune('explore.destination', keep['north_dest'], {'region__slug': 'north'}, kept_places)
prune('explore.destination', keep['south_dest'], {'region__slug': 'south'}, kept_places)
prune('explore.regionhighlight', keep['north_hl'], {'region__slug': 'north'})

# 4. leftover places that are still attached to events (the team agreed to remove them)
if kept_places:
    rule = Event._meta.get_field('destination').remote_field.on_delete.__name__
    print('')
    print('Leftover places that are not in the files:')
    for d in kept_places:
        print('-', d.pk, d.name, '|', d.region.slug, '| events:', [e.title for e in Event.objects.filter(destination=d)])
    if rule == 'PROTECT':
        print('They are protected by their events and cannot be deleted. Ask for help.')
    else:
        if rule == 'CASCADE':
            print('Note: deleting these also deletes the events listed above.')
        for d in kept_places:
            d.delete()
        print('deleted the leftover places')

# 5. check the numbers against the files
def check(name, db_count, file_count):
    print(name, '| database:', db_count, '| file:', file_count, '| OK' if db_count == file_count else '| DIFFERENT')
check('north places', Destination.objects.filter(region__slug='north').count(), len(keep['north_dest']))
check('south places', Destination.objects.filter(region__slug='south').count(), len(keep['south_dest']))
check('guides', apps.get_model('explore.guide').objects.count(), len(keep['guide']))
check('reviews', apps.get_model('explore.guidereview').objects.count(), len(keep['review']))
check('packages', apps.get_model('explore.package').objects.count(), len(keep['package']))
check('category cards', apps.get_model('explore.experience').objects.count(), len(keep['experience']))
if os.path.exists(M):
    check('map pins', apps.get_model('explore.mappin').objects.count(), len(keep_pins))
