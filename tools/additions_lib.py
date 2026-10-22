import json
from django.core import serializers


def row(obj):
    """One database row as plain data: normal fields as they are, links to other rows as slugs."""
    ser = json.loads(serializers.serialize('json', [obj]))[0]['fields']
    plain = {f.name for f in obj._meta.concrete_fields if not f.is_relation and not f.primary_key}
    fields = {k: v for k, v in ser.items() if k in plain}
    fks = {}
    for f in obj._meta.concrete_fields:
        if f.is_relation:
            target = getattr(obj, f.name)
            if target is None:
                fks[f.name] = None
            elif hasattr(target, 'slug'):
                fks[f.name] = target.slug
            else:
                raise SystemExit('STOP: ' + obj._meta.label + ' links to ' + str(target) + ' which has no slug.')
    return {'fields': fields, 'fks': fks}


def key(r):
    """What makes a row 'the same row' on every laptop (never the id number)."""
    k = [(n, r['fks'][n]) for n in sorted(r['fks'])]
    for pref in ('name', 'title', 'image'):
        if pref in r['fields']:
            k.append((pref, str(r['fields'][pref])))
            return tuple(k)
    k.append(('all', json.dumps(r['fields'], sort_keys=True)))
    return tuple(k)
