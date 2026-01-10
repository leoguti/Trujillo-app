#!/usr/bin/env python3
"""
Genera la secuencia de paradas para cada trip
Asigna stop_ids y maneja paradas sintéticas
"""

import json
import csv
from pathlib import Path
from shapely.geometry import Point, LineString

def load_shape_from_gtfs(shapes_file, shape_id):
    """Carga un shape desde shapes.txt del GTFS"""
    shapes = {}
    with open(shapes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row['shape_id']
            if sid not in shapes:
                shapes[sid] = []
            shapes[sid].append({
                'lat': float(row['shape_pt_lat']),
                'lon': float(row['shape_pt_lon']),
                'seq': int(row['shape_pt_sequence'])
            })
    
    if shape_id in shapes:
        coords = sorted(shapes[shape_id], key=lambda x: x['seq'])
        return [[p['lon'], p['lat']] for p in coords]
    return None

def calculate_right_side_stops(route_coords, stops_dict, max_distance=25):
    """
    Calcula qué paradas están al lado derecho de la ruta
    stops_dict: diccionario con stop_id como clave
    """
    route_line = LineString(route_coords)
    right_stops = []
    
    for stop_id, stop_data in stops_dict.items():
        stop_point = Point(stop_data['stop_lon'], stop_data['stop_lat'])
        
        # Calcular distancia a la ruta
        distance = route_line.distance(stop_point)
        distance_meters = distance * 111000
        
        if distance_meters > max_distance:
            continue
        
        # Encontrar el segmento más cercano
        min_dist = float('inf')
        segment_idx = 0
        for i in range(len(route_coords) - 1):
            seg = LineString([route_coords[i], route_coords[i+1]])
            d = seg.distance(stop_point)
            if d < min_dist:
                min_dist = d
                segment_idx = i
        
        # Determinar lado usando producto cruz
        p1 = route_coords[segment_idx]
        p2 = route_coords[segment_idx + 1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        px = stop_data['stop_lon'] - p1[0]
        py = stop_data['stop_lat'] - p1[1]
        
        cross = dx * py - dy * px
        
        distance_along = route_line.project(stop_point)
        
        if cross < 0:  # Invertido: negativo = derecha
            right_stops.append({
                'stop_id': stop_id,
                'distance_meters': distance_meters,
                'distance_along': distance_along * 111000
            })
    
    right_stops.sort(key=lambda x: x['distance_along'])
    
    return right_stops

def ensure_start_end_stops(route_coords, right_stops, stops_dict, trip_id, threshold_meters=10):
    """
    Verifica paradas de inicio y fin
    Si no existen, crea paradas sintéticas y las agrega al diccionario global
    """
    route_line = LineString(route_coords)
    start_point = Point(route_coords[0][0], route_coords[0][1])
    end_point = Point(route_coords[-1][0], route_coords[-1][1])
    
    # Verificar inicio
    has_start = False
    for stop in right_stops:
        stop_data = stops_dict[stop['stop_id']]
        stop_point = Point(stop_data['stop_lon'], stop_data['stop_lat'])
        distance = start_point.distance(stop_point) * 111000
        if distance < threshold_meters:
            has_start = True
            break
    
    # Verificar fin
    has_end = False
    for stop in right_stops:
        stop_data = stops_dict[stop['stop_id']]
        stop_point = Point(stop_data['stop_lon'], stop_data['stop_lat'])
        distance = end_point.distance(stop_point) * 111000
        if distance < threshold_meters:
            has_end = True
            break
    
    new_stops = list(right_stops)
    synthetic_stops_added = []
    
    # Crear parada de inicio si es necesaria
    if not has_start:
        start_stop_id = f"SYNTH_START_{trip_id}"
        stops_dict[start_stop_id] = {
            'stop_id': start_stop_id,
            'stop_code': f"INICIO_{trip_id}",
            'stop_name': f"INICIO RUTA {trip_id}",
            'stop_lat': route_coords[0][1],
            'stop_lon': route_coords[0][0],
            'distrito': 'Generado',
            'synthetic': True
        }
        new_stops.insert(0, {
            'stop_id': start_stop_id,
            'distance_meters': 0,
            'distance_along': 0
        })
        synthetic_stops_added.append(start_stop_id)
    
    # Crear parada de fin si es necesaria
    if not has_end:
        end_stop_id = f"SYNTH_END_{trip_id}"
        stops_dict[end_stop_id] = {
            'stop_id': end_stop_id,
            'stop_code': f"FIN_{trip_id}",
            'stop_name': f"FIN RUTA {trip_id}",
            'stop_lat': route_coords[-1][1],
            'stop_lon': route_coords[-1][0],
            'distrito': 'Generado',
            'synthetic': True
        }
        new_stops.append({
            'stop_id': end_stop_id,
            'distance_meters': 0,
            'distance_along': route_line.length * 111000
        })
        synthetic_stops_added.append(end_stop_id)
    
    return new_stops, synthetic_stops_added

def main():
    base_path = Path(__file__).parent
    
    print("=" * 80)
    print("🚏 GENERANDO SECUENCIA DE PARADAS POR TRIP")
    print("=" * 80)
    
    # Archivos de entrada
    shapes_file = base_path.parent / 'GTFS/out/trujillo/gtfs/shapes.txt'
    trips_file = base_path.parent / 'GTFS/out/trujillo/gtfs/trips.txt'
    stops_clean_file = base_path / 'stops_with_ids_clean.json'
    
    # 1. Cargar paradas limpias
    print("\n1. Cargando paradas limpias...")
    with open(stops_clean_file, 'r', encoding='utf-8') as f:
        stops_data = json.load(f)
    
    # Crear diccionario por stop_id
    stops_dict = {stop['stop_id']: stop for stop in stops_data['stops']}
    print(f"   ✅ {len(stops_dict)} paradas cargadas")
    
    # 2. Cargar trips
    print("\n2. Cargando trips...")
    with open(trips_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        trips = [row for row in reader]
    print(f"   ✅ {len(trips)} trips cargados")
    
    # 3. Procesar TODOS los trips
    print(f"\n3. Procesando todos los trips ({len(trips)} en total)...")
    
    # Colección de todas las paradas (incluyendo sintéticas)
    all_stops_dict = stops_dict.copy()
    
    # Estadísticas globales
    total_processed = 0
    total_stops_assigned = 0
    total_synthetic = 0
    failed_trips = []
    
    for trip_info in trips:
        trip_id = trip_info['trip_id']
        shape_id = trip_info['shape_id']
        route_id = trip_info.get('route_id', 'N/A')
        
        print(f"\n   [{total_processed + 1}/{len(trips)}] Trip {trip_id} (Ruta: {route_id})...")
        
        route_coords = load_shape_from_gtfs(shapes_file, shape_id)
        
        if not route_coords:
            print(f"      ❌ Shape {shape_id} no encontrado")
            failed_trips.append({'trip_id': trip_id, 'reason': 'Shape not found'})
            total_processed += 1
            continue
        
        print(f"      Shape: {len(route_coords)} puntos")
        
        # Calcular paradas del lado derecho
        right_stops = calculate_right_side_stops(route_coords, all_stops_dict, max_distance=20)
        
        if not right_stops:
            print(f"      ⚠️  0 paradas asignadas")
            failed_trips.append({'trip_id': trip_id, 'reason': 'No stops found'})
            total_processed += 1
            continue
        
        # Asegurar inicio/fin
        right_stops, synthetic_added = ensure_start_end_stops(route_coords, right_stops, all_stops_dict, trip_id)
        
        # Actualizar diccionario global con las sintéticas nuevas
        for stop_id in synthetic_added:
            if stop_id in all_stops_dict:
                pass  # Ya está
        
        # Guardar secuencia del trip
        trip_stops_sequence = {
            'trip_id': trip_id,
            'route_id': route_id,
            'shape_id': shape_id,
            'total_stops': len(right_stops),
            'stops_sequence': [
                {
                    'stop_sequence': idx + 1,
                    'stop_id': stop['stop_id']
                }
                for idx, stop in enumerate(right_stops)
            ]
        }
        
        with open(base_path / f'trip_{trip_id}_stops.json', 'w', encoding='utf-8') as f:
            json.dump(trip_stops_sequence, f, ensure_ascii=False, indent=2)
        
        print(f"      ✅ {len(right_stops)} paradas ({len(synthetic_added)} sintéticas)")
        
        total_processed += 1
        total_stops_assigned += len(right_stops)
        total_synthetic += len(synthetic_added)
    
    # 4. Guardar stops_with_ids_final.json con todas las paradas (incluyendo sintéticas)
    print(f"\n4. Guardando stops_with_ids_final.json...")
    all_stops_list = list(all_stops_dict.values())
    
    with open(base_path / 'stops_with_ids_final.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_stops': len(all_stops_list),
            'synthetic_stops': total_synthetic,
            'stops': all_stops_list
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ {len(all_stops_list)} paradas guardadas")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("=" * 80)
    print(f"\n📊 Resumen global:")
    print(f"   • Trips procesados: {total_processed}/{len(trips)}")
    print(f"   • Trips exitosos: {total_processed - len(failed_trips)}")
    print(f"   • Trips fallidos: {len(failed_trips)}")
    print(f"   • Total paradas asignadas: {total_stops_assigned}")
    print(f"   • Paradas sintéticas creadas: {total_synthetic}")
    print(f"   • Total paradas únicas: {len(all_stops_list)}")
    
    if failed_trips:
        print(f"\n⚠️  Trips con problemas:")
        for ft in failed_trips[:10]:  # Mostrar solo primeros 10
            print(f"   • {ft['trip_id']}: {ft['reason']}")
        if len(failed_trips) > 10:
            print(f"   ... y {len(failed_trips) - 10} más")

if __name__ == "__main__":
    main()
