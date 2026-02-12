import json
import csv
import urllib.request
import urllib.parse
import time

relation_ids = [
    19946662, 19946938, 19950139, 19950214, 19953369, 19953601, 19976312,
    19959151, 19975974, 19959184, 19959196, 19959202, 19959207, 19959214,
    19959217, 19959224, 19961769, 19961792, 19961795, 19966193, 19966196,
    19961869, 19961898, 19961919, 19961936, 19961948, 19961958, 19972938,
    19971942, 19961962, 19971967, 19971999, 19976301, 19962130, 19962183,
    19972901, 19976337, 19973156, 19962204, 19962194, 19962272, 19962222,
    19962213, 19962218, 19962228, 19962230, 19962257, 19976195, 19962263,
    19962271, 19962280, 19962320, 19962287, 19962292, 19962294, 19962298,
    19962300, 19962303, 19962313, 19962315, 19962318, 19962323, 19962394,
    19962362, 19962432, 19971395, 19971408, 19971409, 19971413, 19971417,
    19962502, 19972008, 19972010, 19972018, 19972027, 19965057, 19972041,
    19972045, 19972046, 19972051, 19965743, 19965745, 19965750, 19965773,
    19965775, 19965776, 19965801, 19965802, 19965837, 19965840, 19965847,
    19965854, 19972060, 19965855, 19966163, 19966210, 19966201, 19966215,
    19966218, 19966224, 19966226, 19966253, 19966264, 19966270, 19966288,
    19966297, 19967351, 19972065, 19967429, 19972072, 19967529, 19967536,
    19967551, 19967562, 19967583, 19967604, 19967639, 19967670, 19967674,
    19967678, 19967679, 19990111, 19990115, 19968040, 19968053, 19968101,
    19968109, 19968121, 19968127, 19968129, 19968140, 19972103, 19968169,
    19968174, 19968178, 19990157, 19990165, 19968183, 19968195, 19968210,
    19968338, 19968352, 19988569, 19968388, 19968383, 19971427, 19971440,
    19972121, 19972128, 19972155, 19972157, 19970882, 19970891, 19970967,
    19972158, 19972081, 19972086, 19972095, 19972123, 19972130, 19972154,
    19972163, 19972176, 19972190, 19972196, 19988797, 19988815, 19972175,
    19972187, 19972422, 19972433, 19972461, 19972470, 19972473, 19972479,
    19991778, 19990939, 19972496, 19972502, 19972508, 19973946, 19973949,
    19973958, 19972515, 19972516, 19988601, 19988606, 19988678, 19988688,
    19988714, 19988728, 19972512, 19973941, 19973224, 19973932, 19973251,
    19973922, 19972510, 19972509, 19972505, 19972504, 19972501, 19972495,
    19988589, 19972478, 19972475, 19972474, 19972472, 19972467, 19977991,
    19972466, 19972458, 19972195, 19972191,
]

print(f"Total relaciones a consultar: {len(relation_ids)}")

# Build Overpass query for all relations at once
id_list = ",".join(str(r) for r in relation_ids)
query = f"""
[out:json][timeout:120];
(
  relation(id:{id_list});
);
out tags;
"""

url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": query}).encode("utf-8")

print("Consultando Overpass API...")
req = urllib.request.Request(url, data=data)
with urllib.request.urlopen(req, timeout=180) as resp:
    result = json.loads(resp.read().decode("utf-8"))

elements = result.get("elements", [])
print(f"Relaciones obtenidas: {len(elements)}")

# Build CSV
rows = []
for el in elements:
    tags = el.get("tags", {})
    rows.append({
        "relation_id": el["id"],
        "type": tags.get("type", ""),
        "route": tags.get("route", ""),
        "ref": tags.get("ref", ""),
        "name": tags.get("name", ""),
        "from": tags.get("from", ""),
        "to": tags.get("to", ""),
        "operator": tags.get("operator", ""),
        "network": tags.get("network", ""),
        "colour": tags.get("colour", ""),
        "public_transport_version": tags.get("public_transport:version", ""),
    })

# Sort by ref then name
rows.sort(key=lambda r: (r["ref"], r["name"]))

out_path = "rutas_osm.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV generado: {out_path} ({len(rows)} rutas)")

# Quick summary
routes = [r for r in rows if r["route"]]
print(f"\nResumen:")
print(f"  Con tag 'route': {len(routes)}")
route_types = {}
for r in rows:
    rt = r["route"] or "(sin route)"
    route_types[rt] = route_types.get(rt, 0) + 1
for rt, cnt in sorted(route_types.items()):
    print(f"    {rt}: {cnt}")
