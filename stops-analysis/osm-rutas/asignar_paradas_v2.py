#!/usr/bin/env python3
"""
asignar_paradas_v2.py — Asignación mejorada de paradas municipales a rutas OSM.

Mejoras respecto a v1:
  1. Soporte multi-paso: si una ruta pasa dos veces por la misma vía,
     la parada aparece dos veces en la relación.
  2. Dirección de primera vía resuelta geométricamente (no asumida).

Descarga datos frescos de Overpass, encadena vías, asigna paradas con
walk-and-assign, y genera relaciones_con_paradas_v2.osm + reporte CSV.
"""

import json
import csv
import math
import time
import urllib.request
import urllib.parse
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer
from lxml import etree

# ── Constantes ──────────────────────────────────────────────────────────────

EPSG_UTM = 32717           # UTM zona 17S (Trujillo)
BUFFER_M = 20              # Distancia máx de parada a segmento
SEARCH_EXTRA_M = 25        # Margen adicional para búsqueda cKDTree
GAP_THRESHOLD = 5          # Segmentos de gap para separar "pasos" de una parada
MIN_SEGMENT_LEN_M = 0.1    # Ignorar segmentos degenerados

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OUTPUT_OSM = "relaciones_con_paradas.osm"
OUTPUT_CSV = "reporte_asignacion_v2.csv"

# Archivo v1 para comparación (opcional)
V1_OSM = "relaciones_con_paradas.osm"


# ── Proyección UTM ──────────────────────────────────────────────────────────

def setup_projection():
    """Retorna transformador WGS84 → UTM 17S."""
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG_UTM}", always_xy=True)
    return to_utm


# ── Funciones geométricas ──────────────────────────────────────────────────

def cross_product_sign(ax, ay, bx, by, px, py):
    """Signo del producto cruzado (B-A) × (P-A).
    < 0 → P a la derecha de A→B (válido en Perú, tránsito derecha)
    > 0 → P a la izquierda
    = 0 → P sobre la línea
    """
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if cross < 0:
        return -1
    elif cross > 0:
        return 1
    return 0


def point_to_segment_dist(px, py, ax, ay, bx, by):
    """Distancia mínima de un punto a un segmento en coordenadas UTM."""
    dx = bx - ax
    dy = by - ay
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


# ── Paso 1: Descarga de datos de Overpass ──────────────────────────────────

def overpass_query(query, timeout=300):
    """Ejecuta una consulta Overpass y retorna el JSON."""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout + 60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_relations_and_geometry():
    """Descarga relaciones de rutas con geometría completa de vías."""
    print("Descargando relaciones y geometría de vías...")
    # out meta for relations (need version), >; resolves ways→nodes,
    # out body for ways (need tags+nodes) and out skel for bare nodes (just coords)
    query = """[out:json][timeout:300];
relation["network"="Transporte Público Urbano Trujillo"]["route"="bus"];
out meta;
way(r);
out body;
node(w);
out skel;"""
    result = overpass_query(query, timeout=300)

    relations = []
    ways_by_id = {}
    nodes_by_id = {}

    for elem in result["elements"]:
        if elem["type"] == "relation":
            relations.append(elem)
        elif elem["type"] == "way":
            ways_by_id[elem["id"]] = elem
        elif elem["type"] == "node":
            nodes_by_id[elem["id"]] = elem

    print(f"  Relaciones: {len(relations)}")
    print(f"  Vías: {len(ways_by_id)}")
    print(f"  Nodos: {len(nodes_by_id)}")
    return relations, ways_by_id, nodes_by_id


def fetch_municipal_stops():
    """Descarga paradas municipales de OSM."""
    print("Descargando paradas municipales...")
    query = """[out:json][timeout:60];
node["network"="Transporte Público Urbano Trujillo"]["public_transport"="platform"];
out meta;"""
    result = overpass_query(query, timeout=60)

    stops = []
    for elem in result["elements"]:
        if elem["type"] == "node":
            tags = elem.get("tags", {})
            ref = tags.get("ref", "")
            source = tags.get("source", tags.get("source:ref", ""))
            stops.append({
                "id": elem["id"],
                "lat": elem["lat"],
                "lon": elem["lon"],
                "ref": ref,
                "source": source,
                "tags": tags,
                "version": elem.get("version", 1),
            })

    print(f"  Paradas municipales: {len(stops)}")
    return stops


# ── Paso 2: Encadenamiento de vías ────────────────────────────────────────

def chain_ways(relation, ways_by_id, nodes_by_id, to_utm):
    """Construye la polilínea completa de una ruta encadenando sus way members.

    Retorna lista de (lat, lon) en orden de recorrido, o None si falla.
    """
    # Extraer way members en orden
    way_members = []
    for m in relation.get("members", []):
        if m["type"] == "way" and m.get("role", "") in ("", "forward", "backward"):
            wid = m["ref"]
            if wid in ways_by_id:
                way_members.append(ways_by_id[wid])

    if not way_members:
        return None, []

    # Convertir cada way a lista de node IDs
    way_node_lists = []
    for w in way_members:
        nids = w.get("nodes", [])
        if not nids:
            continue
        way_node_lists.append(nids)

    if not way_node_lists:
        return None, []

    # Helper: obtener coordenadas de un nodo
    def node_coord(nid):
        n = nodes_by_id.get(nid)
        if n is None:
            return None
        return (n["lat"], n["lon"])

    # Helper: distancia UTM entre dos nodos
    def node_dist_utm(nid1, nid2):
        c1, c2 = node_coord(nid1), node_coord(nid2)
        if c1 is None or c2 is None:
            return float('inf')
        x1, y1 = to_utm.transform(c1[1], c1[0])
        x2, y2 = to_utm.transform(c2[1], c2[0])
        return math.hypot(x2 - x1, y2 - y1)

    # Resolver dirección de la primera vía mirando la segunda
    def resolve_first_way(wnl):
        if len(wnl) < 2:
            return wnl[0]  # Solo una vía, no se puede resolver

        w0 = wnl[0]
        w1 = wnl[1]

        # Verificar si way0 se conecta forward o backward con way1
        w0_first, w0_last = w0[0], w0[-1]
        w1_first, w1_last = w1[0], w1[-1]

        # way0 forward: su último nodo conecta con way1
        if w0_last == w1_first or w0_last == w1_last:
            return w0  # forward

        # way0 backward: su primer nodo conecta con way1
        if w0_first == w1_first or w0_first == w1_last:
            return list(reversed(w0))  # backward

        # No comparten nodo → heurística de distancia mínima
        d_ff = node_dist_utm(w0_last, w1_first)
        d_fl = node_dist_utm(w0_last, w1_last)
        d_bf = node_dist_utm(w0_first, w1_first)
        d_bl = node_dist_utm(w0_first, w1_last)
        min_d = min(d_ff, d_fl, d_bf, d_bl)

        if min_d in (d_ff, d_fl):
            return w0  # forward
        else:
            return list(reversed(w0))  # backward

    # Encadenar vías
    chain = list(resolve_first_way(way_node_lists))
    way_ids_ordered = [way_members[0]["id"]]

    for i in range(1, len(way_node_lists)):
        wnl = way_node_lists[i]
        wid = way_members[i]["id"] if i < len(way_members) else None

        last_node = chain[-1]
        w_first, w_last = wnl[0], wnl[-1]

        if last_node == w_first:
            # Forward, skip first node (already in chain)
            chain.extend(wnl[1:])
        elif last_node == w_last:
            # Backward
            chain.extend(reversed(wnl[:-1]))
        else:
            # Gap: heurística de distancia mínima entre endpoints
            d_f = node_dist_utm(last_node, w_first)
            d_l = node_dist_utm(last_node, w_last)
            if d_f <= d_l:
                chain.extend(wnl)  # forward, include first (gap)
            else:
                chain.extend(reversed(wnl))  # backward, include first (gap)

        if wid:
            way_ids_ordered.append(wid)

    # Convertir chain de node IDs a coordenadas
    polyline = []
    for nid in chain:
        c = node_coord(nid)
        if c is not None:
            polyline.append(c)

    return polyline, way_ids_ordered


# ── Paso 3: Proyección y cKDTree ──────────────────────────────────────────

def project_polyline(polyline, to_utm):
    """Proyecta polilínea [(lat,lon),...] a UTM [(x,y),...]."""
    utm_pts = []
    for lat, lon in polyline:
        x, y = to_utm.transform(lon, lat)
        utm_pts.append((x, y))
    return utm_pts


def build_stop_tree(stops, to_utm):
    """Proyecta paradas a UTM y construye cKDTree."""
    utm_coords = []
    for s in stops:
        x, y = to_utm.transform(s["lon"], s["lat"])
        s["utm_x"] = x
        s["utm_y"] = y
        utm_coords.append([x, y])

    if not utm_coords:
        return None, np.array([])

    coords_arr = np.array(utm_coords)
    tree = cKDTree(coords_arr)
    return tree, coords_arr


# ── Paso 4: Walk-and-Assign ──────────────────────────────────────────────

def walk_and_assign(polyline_utm, stops, stop_tree, stop_coords):
    """Camina la polilínea segmento a segmento y asigna paradas.

    Retorna lista de (seg_idx, stop_idx, dist) ordenada por seg_idx.
    Soporta multi-paso: una parada puede aparecer múltiples veces.
    """
    if stop_tree is None or len(polyline_utm) < 2:
        return []

    raw_hits = []  # (seg_idx, stop_idx, dist)

    for i in range(len(polyline_utm) - 1):
        ax, ay = polyline_utm[i]
        bx, by = polyline_utm[i + 1]

        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len < MIN_SEGMENT_LEN_M:
            continue

        # Punto medio del segmento
        mx = (ax + bx) / 2
        my = (ay + by) / 2

        # Radio de búsqueda en el cKDTree
        search_r = seg_len / 2 + SEARCH_EXTRA_M

        nearby_idx = stop_tree.query_ball_point([mx, my], search_r)

        for sidx in nearby_idx:
            px, py = stop_coords[sidx]
            dist = point_to_segment_dist(px, py, ax, ay, bx, by)
            if dist <= BUFFER_M:
                cross = cross_product_sign(ax, ay, bx, by, px, py)
                if cross <= 0:  # derecha o sobre la línea
                    raw_hits.append((i, sidx, dist))

    if not raw_hits:
        return []

    # Agrupar hits por parada
    hits_by_stop = defaultdict(list)
    for seg_idx, stop_idx, dist in raw_hits:
        hits_by_stop[stop_idx].append((seg_idx, dist))

    # Para cada parada, dividir en grupos por gap de segmentos
    assignments = []
    for stop_idx, hits in hits_by_stop.items():
        hits.sort(key=lambda h: h[0])  # ordenar por seg_idx

        # Dividir en grupos donde gap > GAP_THRESHOLD
        groups = []
        current_group = [hits[0]]
        for j in range(1, len(hits)):
            if hits[j][0] - hits[j - 1][0] > GAP_THRESHOLD:
                groups.append(current_group)
                current_group = [hits[j]]
            else:
                current_group.append(hits[j])
        groups.append(current_group)

        # Cada grupo = un paso → tomar el hit con menor distancia
        for group in groups:
            best = min(group, key=lambda h: h[1])
            assignments.append((best[0], stop_idx, best[1]))

    # Ordenar por seg_idx → orden en la relación
    assignments.sort(key=lambda a: a[0])

    return assignments


# ── Paso 5: Generar .osm ────────────────────────────────────────────────

def generate_osm_v2(relations, assignments_by_rel, stops, ways_by_id,
                     nodes_by_id, output_path):
    """Genera relaciones_con_paradas_v2.osm."""

    # Recopilar todos los nodos y vías referenciados
    referenced_node_ids = set()
    referenced_way_ids = set()

    for rel in relations:
        rel_id = rel["id"]
        asgn = assignments_by_rel.get(rel_id, [])

        # Nodos de paradas asignadas
        for _, stop_idx, _ in asgn:
            referenced_node_ids.add(stops[stop_idx]["id"])

        # Vías de la relación
        for m in rel.get("members", []):
            if m["type"] == "way":
                wid = m["ref"]
                referenced_way_ids.add(wid)
                w = ways_by_id.get(wid)
                if w:
                    for nid in w.get("nodes", []):
                        referenced_node_ids.add(nid)

    print(f"  Nodos referenciados: {len(referenced_node_ids)}")
    print(f"  Vías referenciadas: {len(referenced_way_ids)}")

    # Construir XML
    root = etree.Element("osm", version="0.6",
                         generator="paraderos_trujillo_v2")

    # Emitir nodos (ordenados por ID para consistencia)
    for nid in sorted(referenced_node_ids):
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        attrs = {
            "id": str(nid),
            "lat": f"{n['lat']:.7f}",
            "lon": f"{n['lon']:.7f}",
        }
        if "version" in n:
            attrs["version"] = str(n["version"])
        else:
            attrs["version"] = "1"

        node_elem = etree.SubElement(root, "node", **attrs)

        # Tags solo para nodos que los tienen (paradas, traffic_signals, etc.)
        for tag_k, tag_v in sorted(n.get("tags", {}).items()):
            etree.SubElement(node_elem, "tag", k=tag_k, v=str(tag_v))

    # Emitir vías (ordenadas por ID)
    for wid in sorted(referenced_way_ids):
        w = ways_by_id.get(wid)
        if w is None:
            continue
        attrs = {
            "id": str(wid),
        }
        if "version" in w:
            attrs["version"] = str(w["version"])
        else:
            attrs["version"] = "1"

        way_elem = etree.SubElement(root, "way", **attrs)
        for nid in w.get("nodes", []):
            etree.SubElement(way_elem, "nd", ref=str(nid))
        for tag_k, tag_v in sorted(w.get("tags", {}).items()):
            etree.SubElement(way_elem, "tag", k=tag_k, v=str(tag_v))

    # Emitir relaciones
    for rel in sorted(relations, key=lambda r: r["id"]):
        rel_id = rel["id"]
        asgn = assignments_by_rel.get(rel_id, [])

        attrs = {
            "id": str(rel_id),
            "action": "modify",
        }
        if "version" in rel:
            attrs["version"] = str(rel["version"])

        rel_elem = etree.SubElement(root, "relation", **attrs)

        # Primero: platform members (paradas) en orden de ruta
        for _, stop_idx, _ in asgn:
            etree.SubElement(rel_elem, "member",
                             type="node",
                             ref=str(stops[stop_idx]["id"]),
                             role="platform")

        # Luego: way members en orden original
        for m in rel.get("members", []):
            if m["type"] == "way":
                etree.SubElement(rel_elem, "member",
                                 type="way",
                                 ref=str(m["ref"]),
                                 role=m.get("role", ""))

        # Tags: preservar todos
        for tag_k, tag_v in sorted(rel.get("tags", {}).items()):
            etree.SubElement(rel_elem, "tag", k=tag_k, v=str(tag_v))

    # Escribir
    tree = etree.ElementTree(root)
    tree.write(output_path, xml_declaration=True, encoding="UTF-8",
               pretty_print=True)
    print(f"\nArchivo OSM escrito: {output_path}")


# ── Paso 6: Reporte comparativo ─────────────────────────────────────────

def load_v1_assignments(v1_path):
    """Carga asignaciones de v1 desde el .osm para comparación."""
    v1_data = {}  # rel_id → [stop_id, ...]
    try:
        tree = etree.parse(v1_path)
    except (FileNotFoundError, etree.XMLSyntaxError):
        return v1_data

    for rel_elem in tree.findall(".//relation"):
        rel_id = int(rel_elem.get("id"))
        platforms = []
        for m in rel_elem.findall("member"):
            if m.get("role") == "platform" and m.get("type") == "node":
                platforms.append(int(m.get("ref")))
        v1_data[rel_id] = platforms

    return v1_data


def generate_report(relations, assignments_by_rel, stops, v1_data,
                    output_path):
    """Genera reporte CSV comparativo v1 vs v2."""
    rows = []
    total_v1 = 0
    total_v2 = 0
    routes_changed = 0
    total_repeated = 0

    for rel in sorted(relations, key=lambda r: r["id"]):
        rel_id = rel["id"]
        tags = rel.get("tags", {})
        ref = tags.get("ref", "")
        name = tags.get("name", "")

        v2_asgn = assignments_by_rel.get(rel_id, [])
        v2_stop_ids = [stops[si]["id"] for _, si, _ in v2_asgn]
        v1_stop_ids = v1_data.get(rel_id, [])

        n_v1 = len(v1_stop_ids)
        n_v2 = len(v2_stop_ids)
        total_v1 += n_v1
        total_v2 += n_v2

        # Paradas únicas
        v1_set = set(v1_stop_ids)
        v2_set = set(v2_stop_ids)

        nuevas = v2_set - v1_set
        removidas = v1_set - v2_set

        # Repetidas (multi-paso)
        repeated_count = n_v2 - len(v2_set)
        total_repeated += repeated_count

        changed = (v1_stop_ids != v2_stop_ids)
        if changed and (n_v1 > 0 or n_v2 > 0):
            routes_changed += 1

        rows.append({
            "relation_id": rel_id,
            "ref": ref,
            "name": name,
            "n_paradas_v1": n_v1,
            "n_paradas_v2": n_v2,
            "paradas_nuevas": len(nuevas),
            "paradas_removidas": len(removidas),
            "paradas_repetidas": repeated_count,
        })

    # Escribir CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "relation_id", "ref", "name", "n_paradas_v1", "n_paradas_v2",
            "paradas_nuevas", "paradas_removidas", "paradas_repetidas",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Reporte CSV escrito: {output_path}")

    # Resumen en consola
    print(f"\n{'='*60}")
    print(f"RESUMEN COMPARATIVO v1 vs v2")
    print(f"{'='*60}")
    print(f"Total asignaciones v1: {total_v1}")
    print(f"Total asignaciones v2: {total_v2}")
    print(f"Diferencia:            {total_v2 - total_v1:+d}")
    print(f"Rutas con cambios:     {routes_changed} de {len(relations)}")
    print(f"Paradas repetidas (multi-paso): {total_repeated}")

    # Top 10 rutas con más cambios
    rows_sorted = sorted(rows, key=lambda r: abs(r["n_paradas_v2"] - r["n_paradas_v1"]),
                         reverse=True)
    print(f"\nTop 10 rutas con mayor cambio:")
    for r in rows_sorted[:10]:
        diff = r["n_paradas_v2"] - r["n_paradas_v1"]
        print(f"  {r['ref']:12s} v1={r['n_paradas_v1']:3d}  v2={r['n_paradas_v2']:3d}  "
              f"diff={diff:+d}  rep={r['paradas_repetidas']}")

    # Rutas con paradas repetidas
    reps = [r for r in rows if r["paradas_repetidas"] > 0]
    if reps:
        print(f"\nRutas con paradas repetidas ({len(reps)}):")
        for r in sorted(reps, key=lambda x: -x["paradas_repetidas"])[:15]:
            print(f"  {r['ref']:12s} {r['paradas_repetidas']} repetidas "
                  f"({r['n_paradas_v2']} total)")


# ── Verificación piloto C-10 M ──────────────────────────────────────────

def verify_pilot(assignments_by_rel, stops):
    """Verifica la ruta piloto C-10 M ida (relación 19967562)."""
    pilot_id = 19967562
    asgn = assignments_by_rel.get(pilot_id, [])
    if not asgn:
        print("\n⚠ Ruta piloto C-10 M (19967562) no encontrada o sin paradas")
        return

    stop_refs = [stops[si]["ref"] for _, si, _ in asgn]
    print(f"\nVerificación piloto C-10 M ida (19967562):")
    print(f"  Paradas asignadas: {len(asgn)}")
    print(f"  Refs: {', '.join(stop_refs[:10])}{'...' if len(stop_refs) > 10 else ''}")

    # Contar repetidas
    unique = set(stops[si]["id"] for _, si, _ in asgn)
    if len(unique) < len(asgn):
        print(f"  ⚠ {len(asgn) - len(unique)} paradas repetidas (multi-paso)")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()

    # 1. Proyección
    to_utm = setup_projection()

    # 2. Descargar datos de Overpass
    relations, ways_by_id, nodes_by_id = fetch_relations_and_geometry()
    time.sleep(2)  # Cortesía con el servidor Overpass
    stops = fetch_municipal_stops()

    # Merge stop data into nodes_by_id (out skel doesn't return tags)
    for s in stops:
        sid = s["id"]
        if sid in nodes_by_id:
            # Enrich existing node with tags and version
            nodes_by_id[sid]["tags"] = s["tags"]
            nodes_by_id[sid]["version"] = s["version"]
        else:
            # Stop node not in relations geometry — add it
            nodes_by_id[sid] = {
                "id": sid,
                "lat": s["lat"],
                "lon": s["lon"],
                "tags": s["tags"],
                "version": s["version"],
            }

    # Filtrar solo paradas municipales (con ref y source de Gerencia)
    municipal_stops = [
        s for s in stops
        if s["ref"] and (
            "Gerencia" in s.get("source", "")
            or "Gerencia" in s.get("tags", {}).get("source", "")
            or "Gerencia" in s.get("tags", {}).get("source:ref", "")
        )
    ]
    print(f"  Paradas municipales con ref: {len(municipal_stops)}")

    # Si no hay filtro de source, usar todas las que tengan ref
    if len(municipal_stops) < 100:
        print("  ⚠ Pocas paradas con filtro de Gerencia, usando todas con ref")
        municipal_stops = [s for s in stops if s["ref"]]
        print(f"  Paradas con ref: {len(municipal_stops)}")

    # 3. Construir cKDTree de paradas
    stop_tree, stop_coords = build_stop_tree(municipal_stops, to_utm)
    print(f"\ncKDTree construido con {len(municipal_stops)} paradas")

    # 4. Procesar cada relación
    print(f"\nProcesando {len(relations)} relaciones...")
    assignments_by_rel = {}
    stats = {"ok": 0, "no_ways": 0, "no_stops": 0, "chain_fail": 0}
    total_assignments = 0

    for idx, rel in enumerate(relations):
        rel_id = rel["id"]
        ref = rel.get("tags", {}).get("ref", "?")

        # Encadenar vías
        polyline, way_ids = chain_ways(rel, ways_by_id, nodes_by_id, to_utm)

        if polyline is None or len(polyline) < 2:
            stats["no_ways"] += 1
            assignments_by_rel[rel_id] = []
            continue

        # Proyectar polilínea a UTM
        polyline_utm = project_polyline(polyline, to_utm)

        # Walk and assign
        asgn = walk_and_assign(polyline_utm, municipal_stops, stop_tree,
                               stop_coords)

        assignments_by_rel[rel_id] = asgn
        total_assignments += len(asgn)

        if len(asgn) > 0:
            stats["ok"] += 1
        else:
            stats["no_stops"] += 1

        # Progreso cada 50 rutas
        if (idx + 1) % 50 == 0:
            print(f"  {idx + 1}/{len(relations)} rutas procesadas...")

    print(f"\nEstadísticas de procesamiento:")
    print(f"  Rutas con paradas: {stats['ok']}")
    print(f"  Rutas sin paradas: {stats['no_stops']}")
    print(f"  Rutas sin vías:    {stats['no_ways']}")
    print(f"  Total asignaciones: {total_assignments}")

    # Paradas únicas asignadas
    all_stop_ids = set()
    for asgn in assignments_by_rel.values():
        for _, si, _ in asgn:
            all_stop_ids.add(municipal_stops[si]["id"])
    print(f"  Paradas únicas asignadas: {len(all_stop_ids)} de {len(municipal_stops)}")

    # 5. Verificar piloto
    verify_pilot(assignments_by_rel, municipal_stops)

    # 6. Generar archivo .osm
    print(f"\nGenerando {OUTPUT_OSM}...")
    generate_osm_v2(relations, assignments_by_rel, municipal_stops,
                    ways_by_id, nodes_by_id, OUTPUT_OSM)

    # 7. Cargar v1 y generar reporte comparativo
    print(f"\nCargando v1 para comparación ({V1_OSM})...")
    v1_data = load_v1_assignments(V1_OSM)
    if v1_data:
        print(f"  Relaciones v1: {len(v1_data)}")
    else:
        print("  ⚠ No se encontró archivo v1, reporte sin comparación")

    generate_report(relations, assignments_by_rel, municipal_stops, v1_data,
                    OUTPUT_CSV)

    elapsed = time.time() - t0
    print(f"\nCompletado en {elapsed:.1f}s")


if __name__ == "__main__":
    main()
