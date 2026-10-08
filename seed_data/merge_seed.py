# seed_data/merge_seed.py
#
# Combines every seed_data/*.json (one per team member) into the CURRENT database,
# without letting different people's ID numbers overwrite each other.
#
# Run from the project root (the folder with manage.py), venv active:
#   DRY RUN (changes nothing, just prints a report):
#     python manage.py shell -c "exec(open('seed_data/merge_seed.py', encoding='utf-8').read())"
#   REAL RUN (saves the merged data and writes seed_data/all.json):
#     $env:MERGE_COMMIT = "1"
#     python manage.py shell -c "exec(open('seed_data/merge_seed.py', encoding='utf-8').read())"
#
# Rules used when two members have the same row (same slug / name):
#   - the row is reused, not duplicated
#   - any empty field on it is filled in from the other member's data
#   - existing text/photos are never overwritten

import glob
import json
import os

from django.apps import apps
from django.core.management import call_command
from django.db import transaction

EXCLUDES = ['auth', 'contenttypes', 'admin', 'sessions', 'bookings', 'users',
            'experiences.chatsession', 'experiences.chatmessage']
AUTO_PKS = ('AutoField', 'BigAutoField', 'SmallAutoField')


def is_empty(value):
    return value is None or value == '' or value == [] or value == {}


def merge_file(path, report):
    with open(path, encoding='utf-8') as fh:
        objects = json.load(fh)

    present = {(o['model'].lower(), o['pk']) for o in objects}
    idmap = {}          # (model_label, old_pk) -> pk in the real database
    m2m_todo = []       # (instance, field_name, target_label, [old_pks])
    pending = list(objects)

    while pending:
        progressed = False
        still_pending = []

        for obj in pending:
            label = obj['model'].lower()
            try:
                Model = apps.get_model(label)
            except LookupError:
                report['skipped'].append(f"{os.path.basename(path)}: unknown model {label}")
                progressed = True
                continue

            raw = obj['fields']
            data = {}
            ready = True

            for field in Model._meta.concrete_fields:
                if field.primary_key and field.get_internal_type() in AUTO_PKS:
                    continue
                if field.name not in raw:
                    continue
                value = raw[field.name]
                if field.is_relation and value is not None:
                    target = field.related_model._meta.label_lower
                    key = (target, value)
                    if key in idmap:
                        data[field.attname] = idmap[key]
                    elif key in present:
                        ready = False      # parent row not created yet, retry later
                        break
                    else:
                        data[field.attname] = value   # points at something outside the files
                elif field.is_relation:
                    data[field.attname] = None
                else:
                    data[field.name] = value

            if not ready:
                still_pending.append(obj)
                continue

            try:
                with transaction.atomic():
                    existing = None
                    unique_fields = [
                        f for f in Model._meta.concrete_fields
                        if f.unique and not f.primary_key
                    ]
                    for f in unique_fields:
                        val = data.get(f.attname, data.get(f.name))
                        if not is_empty(val):
                            existing = Model.objects.filter(**{f.attname: val}).first()
                            if existing:
                                break
                    if existing is None and not unique_fields:
                        existing = Model.objects.filter(**data).first()

                    if existing is not None:
                        changed = False
                        for k, v in data.items():
                            if is_empty(getattr(existing, k, None)) and not is_empty(v):
                                setattr(existing, k, v)
                                changed = True
                        if changed:
                            existing.save()
                        instance = existing
                        report['merged'][label] = report['merged'].get(label, 0) + 1
                    else:
                        instance = Model(**data)
                        instance.save()
                        report['created'][label] = report['created'].get(label, 0) + 1
            except Exception as exc:  # keep going, report the problem
                report['skipped'].append(
                    f"{os.path.basename(path)}: {label} pk={obj['pk']} -> {exc}")
                progressed = True
                continue

            idmap[(label, obj['pk'])] = instance.pk
            for m2m in Model._meta.many_to_many:
                if m2m.name in raw and raw[m2m.name]:
                    m2m_todo.append((instance, m2m.name,
                                     m2m.related_model._meta.label_lower, raw[m2m.name]))
            progressed = True

        if not progressed and still_pending:
            for obj in still_pending:
                report['skipped'].append(
                    f"{os.path.basename(path)}: {obj['model']} pk={obj['pk']} "
                    f"-> its parent row was not found")
            break
        pending = still_pending

    for instance, name, target, old_pks in m2m_todo:
        new_pks = [idmap.get((target, p), p) for p in old_pks]
        getattr(instance, name).add(*new_pks)


def main():
    commit = os.environ.get('MERGE_COMMIT') == '1'
    files = sorted(
        f for f in glob.glob('seed_data/*.json')
        if os.path.basename(f).lower() != 'all.json'
    )
    if not files:
        print('No seed_data/*.json files found. Run this from the project root.')
        return

    report = {'created': {}, 'merged': {}, 'skipped': []}
    with transaction.atomic():
        for path in files:
            print('Reading', path)
            merge_file(path, report)
        if not commit:
            transaction.set_rollback(True)

    print()
    print('=== REPORT ===')
    print('Created (new rows):', report['created'] or 'none')
    print('Merged (already existed, empty fields filled):', report['merged'] or 'none')
    if report['skipped']:
        print('SKIPPED / PROBLEMS:')
        for line in report['skipped']:
            print('  -', line)
    else:
        print('No problems.')

    if commit:
        call_command('dumpdata', *sum([['--exclude', e] for e in EXCLUDES], []),
                     indent=2, output='seed_data/all.json')
        print('\nSaved the merged database to seed_data/all.json')
    else:
        print('\nDRY RUN: nothing was saved. Set $env:MERGE_COMMIT = "1" for the real run.')


main()