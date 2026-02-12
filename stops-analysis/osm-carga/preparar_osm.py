#!/usr/bin/env python3
"""
preparar_osm.py — Prepara paradas de bus KML para subir a OpenStreetMap.

Lee las paradas clasificadas de map_data_v4.json (green + cyan = 1,405 paradas),
consulta Overpass API para obtener las paradas OSM actuales, y genera:
  - paradas_trujillo.osm  → archivo para revisión/subida en JOSM
  - reporte_preparacion_osm.csv → detalle de cada acción (new/merge)

Algoritmo: para cada parada KML, busca paradas OSM a <30m. Si las hay,
verifica con producto cruzado sobre segmentos de ruta que estén del mismo
lado de la calle antes de fusionar. Si están en lados opuestos, crea nueva.
"""

import json
import csv
import math
import time
import urllib.request
import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer
from lxml import etree

# ── Constantes ──────────────────────────────────────────────────────────────

MATCH_RADIUS_M = 30       # Radio para buscar candidatos OSM
ROUTE_BUFFER_M = 20       # Distancia máx de parada a segmento de ruta
EPSG_UTM = 32717          # UTM zona 17S (Trujillo)
BBOX_MARGIN_DEG = 0.01    # Margen para la consulta Overpass

INPUT_FILE = "map_data_v4.json"
OUTPUT_OSM = "paradas_trujillo.osm"
OUTPUT_CSV = "reporte_preparacion_osm.csv"

NEW_STOP_TAGS = {
    "public_transport": "platform",
    "bus": "yes",
    "highway": "bus_stop",
    "network": "Transporte Público Urbano Trujillo",
    "source": "Gerencia de Transporte Metropolitano de Trujillo",
}

# Tipos de parada OSM que se pueden fusionar
MERGEABLE_TYPES = {"bus_stop", "platform"}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 120


# ── Proyección UTM ──────────────────────────────────────────────────────────

def setup_projection():
    """Retorna transformadores WGS84 ↔ UTM 17S."""
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG_UTM}", always_xy=True)
    to_wgs = Transformer.from_crs(f"EPSG:{EPSG_UTM}", "EPSG:4326", always_xy=True)
    return to_utm, to_wgs


# ── Carga de datos ──────────────────────────────────────────────────────────

def load_kml_candidates(data):
    """Carga las 1,405 paradas KML candidatas (green + cyan)."""
    stops = []
    for cat in ("green", "cyan"):
        for s in data[cat]:
            stops.append({
                "nombre": s["nombre"],
                "lat": s["lat"],
                "lon": s["lon"],
                "capa": s["capa"],
                "category": cat,
            })
    return stops


def load_route_shapes(data, to_utm):
    """Carga los segmentos de ruta proyectados a UTM.

    Retorna lista de segmentos: [(ax, ay, bx, by, mx, my), ...]
    donde (a,b) son los extremos y (m) el punto medio.
    """
    segments = []
    for shape in data["shapes"]:
        coords = shape["coords"]  # [[lat, lon], ...]
        for i in range(len(coords) - 1):
            lat1, lon1 = coords[i]
            lat2, lon2 = coords[i + 1]
            ax, ay = to_utm.transform(lon1, lat1)
            bx, by = to_utm.transform(lon2, lat2)
            mx = (ax + bx) / 2
            my = (ay + by) / 2
            segments.append((ax, ay, bx, by, mx, my))
    return segments


def build_segment_index(segments):
    """Construye un cKDTree con los puntos medios de los segmentos."""
    midpoints = np.array([(s[4], s[5]) for s in segments])
    tree = cKDTree(midpoints)
    return tree


# ── Overpass API ────────────────────────────────────────────────────────────

def fetch_osm_stops(kml_stops):
    """Consulta Overpass API para paradas OSM en el área de las paradas KML."""
    lats = [s["lat"] for s in kml_stops]
    lons = [s["lon"] for s in kml_stops]
    bbox = (
        min(lats) - BBOX_MARGIN_DEG,
        min(lons) - BBOX_MARGIN_DEG,
        max(lats) + BBOX_MARGIN_DEG,
        max(lons) + BBOX_MARGIN_DEG,
    )
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    query = f"""[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  node["highway"="bus_stop"]({bbox_str});
  node["public_transport"="platform"]({bbox_str});
  node["public_transport"="stop_position"]({bbox_str});
  node["amenity"="bus_station"]({bbox_str});
  way["public_transport"="platform"]({bbox_str});
);
out meta;
>;
out meta;"""

    print(f"Consultando Overpass API (bbox: {bbox_str})...")
    import urllib.parse
    data_bytes = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data_bytes)
    with urllib.request.urlopen(req, timeout=OVERPASS_TIMEOUT + 30) as resp:
        result = json.loads(resp.read().decode())

    # Separar nodos y ways
    nodes_by_id = {}
    ways = []
    for elem in result["elements"]:
        if elem["type"] == "node":
            nodes_by_id[elem["id"]] = elem
        elif elem["type"] == "way":
            ways.append(elem)

    stops = []

    # Procesar nodos que son paradas (tienen tags relevantes)
    for nid, node in nodes_by_id.items():
        tags = node.get("tags", {})
        if not tags:
            continue
        stop_type = _classify_osm_node(tags)
        if stop_type is None:
            continue
        stops.append({
            "osm_type": "node",
            "osm_id": node["id"],
            "lat": node["lat"],
            "lon": node["lon"],
            "version": node.get("version", 1),
            "tags": tags,
            "stop_type": stop_type,
        })

    # Procesar ways (calcular centroide)
    for way in ways:
        tags = way.get("tags", {})
        stop_type = _classify_osm_way(tags)
        if stop_type is None:
            continue
        # Centroide de los nodos del way
        way_nodes = [nodes_by_id[nid] for nid in way.get("nodes", [])
                     if nid in nodes_by_id]
        if not way_nodes:
            continue
        clat = sum(n["lat"] for n in way_nodes) / len(way_nodes)
        clon = sum(n["lon"] for n in way_nodes) / len(way_nodes)
        stops.append({
            "osm_type": "way",
            "osm_id": way["id"],
            "lat": clat,
            "lon": clon,
            "version": way.get("version", 1),
            "tags": tags,
            "stop_type": stop_type,
            "nodes": way.get("nodes", []),
            "node_data": {nid: nodes_by_id[nid] for nid in way.get("nodes", [])
                          if nid in nodes_by_id},
        })

    print(f"  Obtenidas {len(stops)} paradas OSM")
    type_counts = {}
    for s in stops:
        t = s["stop_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    return stops


def _classify_osm_node(tags):
    """Clasifica un nodo OSM por tipo de parada."""
    if tags.get("amenity") == "bus_station":
        return "bus_station"
    if tags.get("public_transport") == "stop_position":
        return "stop_position"
    if tags.get("public_transport") == "platform":
        return "platform"
    if tags.get("highway") == "bus_stop":
        return "bus_stop"
    return None


def _classify_osm_way(tags):
    """Clasifica un way OSM por tipo de parada."""
    if tags.get("public_transport") == "platform":
        return "platform"
    return None


# ── Clasificación KML → new / merge ────────────────────────────────────────

def cross_product_sign(ax, ay, bx, by, px, py):
    """Signo del producto cruzado (B-A) × (P-A).

    < 0 → P está a la derecha de A→B (válido en Perú, tránsito por la derecha)
    > 0 → P está a la izquierda
    = 0 → P está sobre la línea
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


def are_on_same_side(kml_utm, osm_utm, segments, seg_tree):
    """Determina si dos puntos están del mismo lado de la calle.

    Busca segmentos de ruta cercanos a ambos puntos. Si algún segmento
    compartido muestra signos de producto cruzado opuestos, están en
    lados opuestos → retorna False.

    Si no hay segmentos compartidos o todos muestran mismo lado → True.
    """
    kx, ky = kml_utm
    ox, oy = osm_utm

    # Buscar segmentos cercanos al punto medio entre ambas paradas
    mid_x = (kx + ox) / 2
    mid_y = (ky + oy) / 2
    # Radio de búsqueda: distancia entre puntos + buffer
    search_radius = math.hypot(kx - ox, ky - oy) / 2 + ROUTE_BUFFER_M + 10

    nearby_idx = seg_tree.query_ball_point([mid_x, mid_y], search_radius)

    found_shared = False
    for idx in nearby_idx:
        seg = segments[idx]
        ax, ay, bx, by = seg[0], seg[1], seg[2], seg[3]

        dist_kml = point_to_segment_dist(kx, ky, ax, ay, bx, by)
        dist_osm = point_to_segment_dist(ox, oy, ax, ay, bx, by)

        if dist_kml <= ROUTE_BUFFER_M and dist_osm <= ROUTE_BUFFER_M:
            found_shared = True
            sign_kml = cross_product_sign(ax, ay, bx, by, kx, ky)
            sign_osm = cross_product_sign(ax, ay, bx, by, ox, oy)

            # Si alguno está sobre la línea, tratar como mismo lado
            if sign_kml == 0 or sign_osm == 0:
                continue

            if sign_kml != sign_osm:
                return False  # Lados opuestos

    # Sin segmentos compartidos o todos en mismo lado
    return True


def classify_kml_stops(kml_stops, osm_stops, segments, seg_tree, to_utm):
    """Clasifica cada parada KML como 'new' o 'merge'.

    Retorna lista de diccionarios con la acción y detalles.
    """
    # Proyectar paradas OSM a UTM y construir índice
    osm_utm_coords = []
    for s in osm_stops:
        x, y = to_utm.transform(s["lon"], s["lat"])
        s["utm_x"] = x
        s["utm_y"] = y
        osm_utm_coords.append([x, y])

    if osm_utm_coords:
        osm_tree = cKDTree(np.array(osm_utm_coords))
    else:
        osm_tree = None

    results = []
    merge_targets = {}  # osm_id → [(kml_idx, distance)]

    for i, kml in enumerate(kml_stops):
        kx, ky = to_utm.transform(kml["lon"], kml["lat"])
        kml["utm_x"] = kx
        kml["utm_y"] = ky

        action = "new"
        matched_osm = None
        match_dist = None
        notes = ""

        if osm_tree is not None:
            # Buscar paradas OSM dentro del radio
            nearby_idx = osm_tree.query_ball_point([kx, ky], MATCH_RADIUS_M)

            # Ordenar por distancia
            candidates = []
            for idx in nearby_idx:
                osm = osm_stops[idx]
                dist = math.hypot(kx - osm["utm_x"], ky - osm["utm_y"])
                candidates.append((dist, idx, osm))
            candidates.sort(key=lambda c: c[0])

            for dist, idx, osm in candidates:
                # Solo merge con platform o bus_stop
                if osm["stop_type"] not in MERGEABLE_TYPES:
                    continue

                # Verificar que están del mismo lado de la calle
                same_side = are_on_same_side(
                    (kx, ky),
                    (osm["utm_x"], osm["utm_y"]),
                    segments,
                    seg_tree,
                )

                if same_side:
                    action = "merge"
                    matched_osm = osm
                    match_dist = dist
                    osm_id = osm["osm_id"]

                    if osm_id not in merge_targets:
                        merge_targets[osm_id] = []
                    merge_targets[osm_id].append((i, dist))
                    break
                else:
                    notes += f"Rechazado OSM {osm['osm_id']} (lado opuesto, {dist:.1f}m). "

        results.append({
            "kml_idx": i,
            "action": action,
            "osm_stop": matched_osm,
            "distance": match_dist,
            "notes": notes,
        })

    # ── Resolver conflictos de merge ────────────────────────────────────
    conflicts_resolved = 0
    for osm_id, kml_matches in merge_targets.items():
        if len(kml_matches) <= 1:
            continue
        # El más cercano gana
        kml_matches.sort(key=lambda x: x[1])
        winner_idx = kml_matches[0][0]
        for kml_idx, dist in kml_matches[1:]:
            results[kml_idx]["action"] = "new"
            results[kml_idx]["osm_stop"] = None
            results[kml_idx]["distance"] = None
            old_notes = results[kml_idx]["notes"]
            results[kml_idx]["notes"] = (
                old_notes +
                f"Conflicto: OSM {osm_id} asignado a parada más cercana "
                f"(idx {winner_idx}, {kml_matches[0][1]:.1f}m vs {dist:.1f}m). "
            )
            conflicts_resolved += 1

    if conflicts_resolved:
        print(f"  Conflictos de merge resueltos: {conflicts_resolved}")

    return results


# ── Generación de archivo .osm ──────────────────────────────────────────────

def generate_osm_xml(kml_stops, results, output_path):
    """Genera archivo .osm para JOSM."""
    root = etree.Element("osm", version="0.6", generator="paraderos_trujillo")

    new_id = -1

    for i, res in enumerate(results):
        kml = kml_stops[i]

        if res["action"] == "new":
            node = etree.SubElement(root, "node",
                                    id=str(new_id),
                                    lat=f"{kml['lat']:.7f}",
                                    lon=f"{kml['lon']:.7f}",
                                    visible="true")
            # Tags para parada nueva
            for k, v in NEW_STOP_TAGS.items():
                etree.SubElement(node, "tag", k=k, v=v)
            # Ref del municipio (NO poner código como name — name debe ser
            # nombre legible o omitirse si no se conoce)
            if kml["nombre"]:
                ref_clean = kml["nombre"].strip()
                # Limpiar espacios internos en refs como "PM-  83" → "PM-83"
                ref_clean = "-".join(p.strip() for p in ref_clean.split("-"))
                etree.SubElement(node, "tag", k="ref", v=ref_clean)
            new_id -= 1

        elif res["action"] == "merge":
            osm = res["osm_stop"]

            if osm["osm_type"] == "node":
                node = etree.SubElement(root, "node",
                                        id=str(osm["osm_id"]),
                                        lat=f"{osm['lat']:.7f}",
                                        lon=f"{osm['lon']:.7f}",
                                        version=str(osm["version"]),
                                        action="modify")
            else:
                # Way: emitir el way con sus nodos
                # Primero emitir los nodos del way (sin modificar)
                for nid in osm.get("nodes", []):
                    ndata = osm.get("node_data", {}).get(nid)
                    if ndata:
                        n_elem = etree.SubElement(root, "node",
                                                  id=str(nid),
                                                  lat=f"{ndata['lat']:.7f}",
                                                  lon=f"{ndata['lon']:.7f}",
                                                  version=str(ndata.get("version", 1)))
                        for tk, tv in ndata.get("tags", {}).items():
                            etree.SubElement(n_elem, "tag", k=tk, v=str(tv))

                node = etree.SubElement(root, "way",
                                        id=str(osm["osm_id"]),
                                        version=str(osm["version"]),
                                        action="modify")
                for nid in osm.get("nodes", []):
                    etree.SubElement(node, "nd", ref=str(nid))

            # Tags: mantener todas las existentes
            merged_tags = dict(osm["tags"])

            # Agregar solo si no existe (excepto source → usar source:ref)
            for k, v in NEW_STOP_TAGS.items():
                if k == "source":
                    # En merges, solo atribuir el ref al municipio, no la geometría
                    merged_tags.setdefault("source:ref", v)
                else:
                    merged_tags.setdefault(k, v)

            # NO poner código como name en merges tampoco
            # (el name original de OSM se preserva intacto)

            # Ref del municipio: siempre agregar/sobreescribir
            if kml["nombre"]:
                ref_clean = kml["nombre"].strip()
                ref_clean = "-".join(p.strip() for p in ref_clean.split("-"))
                merged_tags["ref"] = ref_clean

            for k, v in sorted(merged_tags.items()):
                etree.SubElement(node, "tag", k=k, v=str(v))

    # Escribir XML
    tree = etree.ElementTree(root)
    tree.write(output_path, xml_declaration=True, encoding="UTF-8",
               pretty_print=True)
    print(f"Archivo OSM escrito: {output_path}")


# ── Reporte CSV ─────────────────────────────────────────────────────────────

def generate_csv_report(kml_stops, results, output_path):
    """Genera reporte CSV con detalle de cada acción."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "kml_nombre", "kml_lat", "kml_lon", "kml_capa", "kml_category",
            "action", "osm_id", "osm_name", "distance_m", "notes",
        ])
        for i, res in enumerate(results):
            kml = kml_stops[i]
            osm = res["osm_stop"]
            writer.writerow([
                kml["nombre"],
                f"{kml['lat']:.7f}",
                f"{kml['lon']:.7f}",
                kml["capa"],
                kml["category"],
                res["action"],
                osm["osm_id"] if osm else "",
                osm["tags"].get("name", "") if osm else "",
                f"{res['distance']:.1f}" if res["distance"] is not None else "",
                res["notes"],
            ])
    print(f"Reporte CSV escrito: {output_path}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()

    # 1. Configurar proyección
    to_utm, to_wgs = setup_projection()

    # 2. Cargar datos
    print(f"Cargando {INPUT_FILE}...")
    with open(INPUT_FILE) as f:
        data = json.load(f)

    kml_stops = load_kml_candidates(data)
    print(f"  Paradas KML candidatas: {len(kml_stops)} (green: {sum(1 for s in kml_stops if s['category'] == 'green')}, cyan: {sum(1 for s in kml_stops if s['category'] == 'cyan')})")

    # 3. Cargar rutas
    print("Cargando segmentos de ruta...")
    segments = load_route_shapes(data, to_utm)
    seg_tree = build_segment_index(segments)
    print(f"  Segmentos de ruta: {len(segments)}")

    # 4. Consultar OSM
    osm_stops = fetch_osm_stops(kml_stops)

    # 5. Clasificar
    print("Clasificando paradas KML...")
    results = classify_kml_stops(kml_stops, osm_stops, segments, seg_tree, to_utm)

    # 6. Resumen
    new_count = sum(1 for r in results if r["action"] == "new")
    merge_count = sum(1 for r in results if r["action"] == "merge")
    print(f"\nResumen:")
    print(f"  Crear nuevas:  {new_count}")
    print(f"  Fusionar:      {merge_count}")
    print(f"  Total:         {new_count + merge_count}")

    # 7. Generar archivos
    generate_osm_xml(kml_stops, results, OUTPUT_OSM)
    generate_csv_report(kml_stops, results, OUTPUT_CSV)

    elapsed = time.time() - t0
    print(f"\nCompletado en {elapsed:.1f}s")


if __name__ == "__main__":
    main()
