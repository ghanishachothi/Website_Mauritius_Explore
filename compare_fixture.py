# READ-ONLY: compares a fixture file with your current database. It changes nothing.
import json, os
from django.apps import apps
from django.core import serializers

path = os.environ.get("FIXTURE", "seed_data/all.json")
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)

summary = {}
lines = []
for obj in data:
    label = obj["model"]
    s = summary.setdefault(label, {"new": 0, "changed": 0, "same": 0, "unknown": 0})
    try:
        Model = apps.get_model(label)
    except LookupError:
        s["unknown"] += 1
        lines.append("UNKNOWN  " + label + " pk=" + str(obj.get("pk")))
        continue
    pk = obj.get("pk")
    try:
        inst = Model.objects.get(pk=pk)
    except Model.DoesNotExist:
        s["new"] += 1
        lines.append("NEW      " + label + " pk=" + str(pk))
        continue
    current = json.loads(serializers.serialize("json", [inst]))[0]["fields"]
    diffs = []
    for key, new in obj["fields"].items():
        old = current.get(key)
        if isinstance(new, list) and isinstance(old, list):
            same = sorted(map(str, new)) == sorted(map(str, old))
        else:
            same = str(old) == str(new)
        if not same:
            diffs.append(key)
    if diffs:
        s["changed"] += 1
        lines.append("CHANGED  " + label + " pk=" + str(pk) + " (" + str(inst)[:40] + "): " + ", ".join(diffs))
    else:
        s["same"] += 1

print("Comparing", path, "with your current database (nothing is changed)")
print()
print("%-32s %6s %8s %6s" % ("model", "NEW", "CHANGED", "same"))
for label in sorted(summary):
    s = summary[label]
    print("%-32s %6d %8d %6d" % (label, s["new"], s["changed"], s["same"]))
with open("compare_report.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(lines))
print()
print("Details for every NEW / CHANGED row were written to compare_report.txt")