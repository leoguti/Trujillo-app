#!/usr/bin/env python3
"""
Genera stop_times.txt con tiempos calculados según distancia real
Usa la distancia a lo largo de la ruta (distance_along) de los archivos trip_*.json
"""

import json
import csv
from pathlib import Path
from shapely.geometry import Point, LineString

def calculate_travel_time(distance_km, avg_speed_kmh=20):
    """
    Calcula tiempo de viaje basado en distancia
    
    Args:
        distance_km: Distancia en kilómetros
        avg_speed_kmh: Velocidad promedio (20 km/h para buses urbanos)
    
    Returns:
        Tiempo en minutos (mínimo 1 minuto)
    """
    time_hours = distance_km / avg_speed_kmh
    time_minutes = int(time_hours * 60)
    return max(time_minutes, 1)  # Mínimo 1 minuto

def load_shape_from_gtfs(shapes_file, shape_id):
    """Carga las coordenadas de una shape desde shapes.txt"""
    coords = []
    with open(shapes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['shape_id'] == shape_id:
                coords.append((
                    float(row['shape_pt_lon']),
                    float(row['shape_pt_lat']),
                    int(row['shape_pt_sequence'])
                ))
    coords.sort(key=lambda x: x[2])
    return [(lon, lat) for lon, lat, _ in coords]

def calculate_distance_along_for_stops(route_coords, stops_with_coords):
    """
    Calcula la distancia a lo largo de la ruta para cada parada
    
    Args:
        route_coords: Lista de coordenadas (lon, lat) de la ruta
        stops_with_coords: Lista de diccionarios con stop_id, lat, lon
    
    Returns:
        Lista de diccionarios con stop_id y distance_along_km
    """
    route_line = LineString(route_coords)
    
    stops_with_distance = []
    for stop in stops_with_coords:
        stop_point = Point(stop['lon'], stop['lat'])
        distance_along = route_line.project(stop_point)  # En grados
        distance_along_km = distance_along * 111  # Convertir a km (aprox)
        
        stops_with_distance.append({
            'stop_id': stop['stop_id'],
            'stop_sequence': stop['stop_sequence'],
            'distance_along_km': distance_along_km
        })
    
    return stops_with_distance

def generate_stop_times_with_realistic_times(base_path, avg_speed_kmh=20):
    """
    Genera stop_times.txt con tiempos calculados según distancia real
    """
    print("=" * 80)
    print("⏱️  GENERANDO STOP_TIMES CON TIEMPOS REALISTAS")
    print("=" * 80)
    print()
    print(f"Velocidad promedio: {avg_speed_kmh} km/h")
    print()
    
    # Archivos necesarios
    shapes_file = base_path.parent / 'GTFS/out/trujillo/gtfs/shapes.txt'
    trips_file = base_path.parent / 'GTFS/out/trujillo/gtfs/trips.txt'
    stops_file = base_path / 'stops_with_ids_final.json'
    output_file = base_path / 'gtfs_feed/stop_times.txt'
    
    # Cargar paradas
    with open(stops_file, 'r', encoding='utf-8') as f:
        stops_data = json.load(f)
    stops_dict = {s['stop_id']: s for s in stops_data['stops']}
    
    # Cargar trips para obtener shape_id
    with open(trips_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        trips_shapes = {row['trip_id']: row['shape_id'] for row in reader}
    
    # Procesar cada trip
    trip_files = sorted(base_path.glob('trip_*.json'))
    
    fieldnames = [
        'trip_id',
        'arrival_time',
        'departure_time',
        'stop_id',
        'stop_sequence',
        'pickup_type',
        'drop_off_type'
    ]
    
    total_stop_times = 0
    total_synthetic_warnings = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, trip_file in enumerate(trip_files, 1):
            with open(trip_file, 'r', encoding='utf-8') as tf:
                trip_data = json.load(tf)
            
            trip_id = trip_data['trip_id']
            shape_id = trips_shapes.get(trip_id)
            
            if not shape_id:
                print(f"   ⚠️  Trip {trip_id}: No shape_id encontrado, usando tiempos fijos")
                continue
            
            # Cargar geometría de la ruta
            route_coords = load_shape_from_gtfs(shapes_file, shape_id)
            
            if not route_coords:
                print(f"   ⚠️  Trip {trip_id}: Shape {shape_id} no encontrado")
                continue
            
            # Preparar paradas con coordenadas
            stops_with_coords = []
            for stop_info in trip_data['stops_sequence']:
                stop_id = stop_info['stop_id']
                if stop_id in stops_dict:
                    stops_with_coords.append({
                        'stop_id': stop_id,
                        'stop_sequence': stop_info['stop_sequence'],
                        'lat': stops_dict[stop_id]['stop_lat'],
                        'lon': stops_dict[stop_id]['stop_lon']
                    })
            
            # Calcular distancias a lo largo de la ruta
            stops_with_distance = calculate_distance_along_for_stops(route_coords, stops_with_coords)
            
            # Calcular tiempos acumulados
            start_time_minutes = 6 * 60  # 06:00:00
            cumulative_time_minutes = start_time_minutes
            
            num_stops = len(stops_with_distance)
            
            for i, stop in enumerate(stops_with_distance):
                # Calcular tiempo desde la parada anterior
                if i > 0:
                    distance_delta_km = stop['distance_along_km'] - stops_with_distance[i-1]['distance_along_km']
                    travel_time_min = calculate_travel_time(distance_delta_km, avg_speed_kmh)
                    cumulative_time_minutes += travel_time_min
                
                hours = cumulative_time_minutes // 60
                minutes = cumulative_time_minutes % 60
                time_str = f"{hours:02d}:{minutes:02d}:00"
                
                # Pickup/dropoff types
                if stop['stop_sequence'] == 1:
                    pickup_type = 0
                    drop_off_type = 1
                elif stop['stop_sequence'] == num_stops:
                    pickup_type = 1
                    drop_off_type = 0
                else:
                    pickup_type = 0
                    drop_off_type = 0
                
                writer.writerow({
                    'trip_id': trip_id,
                    'arrival_time': time_str,
                    'departure_time': time_str,
                    'stop_id': stop['stop_id'],
                    'stop_sequence': stop['stop_sequence'],
                    'pickup_type': pickup_type,
                    'drop_off_type': drop_off_type
                })
                
                total_stop_times += 1
            
            if idx % 50 == 0:
                print(f"   Procesados {idx}/{len(trip_files)} trips...")
    
    print()
    print(f"   ✅ {total_stop_times} stop_times escritos")
    print(f"   📊 Promedio: {total_stop_times / len(trip_files):.1f} paradas por trip")
    print()
    
    return output_file

def main():
    base_path = Path(__file__).parent
    
    print()
    print("Generando stop_times.txt con tiempos calculados por distancia...")
    print()
    
    output_file = generate_stop_times_with_realistic_times(base_path, avg_speed_kmh=20)
    
    print("=" * 80)
    print("✅ STOP_TIMES.TXT REGENERADO CON TIEMPOS REALISTAS")
    print("=" * 80)
    print()
    print(f"📁 Archivo: {output_file}")
    print()
    print("💡 Próximo paso:")
    print("   1. Regenerar gtfs_trujillo.zip")
    print("   2. Validar nuevamente con GTFS validator")
    print()

if __name__ == "__main__":
    main()
