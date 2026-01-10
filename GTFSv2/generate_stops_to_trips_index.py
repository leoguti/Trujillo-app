#!/usr/bin/env python3
"""
Genera un índice invertido: para cada parada, lista los trips que pasan por ella.
Útil para saber qué opciones de transporte tiene un usuario desde una parada.
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    base_path = Path(__file__).parent
    
    print("=" * 80)
    print("🔄 GENERANDO ÍNDICE INVERTIDO: PARADAS → TRIPS")
    print("=" * 80)
    print()
    
    # 1. Cargar todas las paradas
    print("1. Cargando paradas...")
    stops_file = base_path / 'stops_with_ids_final.json'
    with open(stops_file, 'r', encoding='utf-8') as f:
        stops_data = json.load(f)
    
    stops_index = {s['stop_id']: s for s in stops_data['stops']}
    print(f"   ✅ {len(stops_index)} paradas cargadas")
    
    # 2. Cargar todos los trips
    print("\n2. Procesando trips...")
    trip_files = sorted(base_path.glob('trip_*.json'))
    print(f"   📁 {len(trip_files)} archivos encontrados")
    
    # Índice invertido: stop_id -> lista de trips
    stops_to_trips = defaultdict(list)
    
    # Contadores
    total_connections = 0
    
    for trip_file in trip_files:
        with open(trip_file, 'r', encoding='utf-8') as f:
            trip_data = json.load(f)
        
        trip_id = trip_data['trip_id']
        route_id = trip_data['route_id']
        
        # Para cada parada en este trip
        for stop_info in trip_data['stops_sequence']:
            stop_id = stop_info['stop_id']
            stop_sequence = stop_info['stop_sequence']
            
            # Agregar este trip a la lista de la parada
            stops_to_trips[stop_id].append({
                'trip_id': trip_id,
                'route_id': route_id,
                'stop_sequence': stop_sequence
            })
            
            total_connections += 1
    
    print(f"   ✅ {total_connections} conexiones parada-trip procesadas")
    
    # 3. Ordenar trips por ruta
    print("\n3. Organizando datos...")
    for stop_id in stops_to_trips:
        # Ordenar por route_id primero, luego por trip_id
        stops_to_trips[stop_id].sort(key=lambda x: (x['route_id'], x['trip_id']))
    
    # 4. Generar estadísticas
    print("\n4. Calculando estadísticas...")
    
    trips_per_stop = [len(trips) for trips in stops_to_trips.values()]
    
    if trips_per_stop:
        avg_trips = sum(trips_per_stop) / len(trips_per_stop)
        max_trips = max(trips_per_stop)
        min_trips = min(trips_per_stop)
        
        # Encontrar la parada con más trips
        busiest_stop_id = max(stops_to_trips.keys(), key=lambda k: len(stops_to_trips[k]))
        busiest_stop_name = stops_index[busiest_stop_id]['stop_name']
        
        print(f"   📊 Promedio de trips por parada: {avg_trips:.1f}")
        print(f"   📊 Máximo trips en una parada: {max_trips}")
        print(f"   📊 Mínimo trips en una parada: {min_trips}")
        print(f"   🏆 Parada más concurrida: {busiest_stop_name} ({max_trips} trips)")
    
    # 5. Crear estructura final con información completa
    print("\n5. Generando archivo JSON...")
    
    stops_with_trips = []
    
    for stop_id, trips_list in stops_to_trips.items():
        if stop_id in stops_index:
            stop = stops_index[stop_id]
            
            # Agrupar por ruta para mejor visualización
            routes_dict = {}
            for trip in trips_list:
                route_id = trip['route_id']
                if route_id not in routes_dict:
                    routes_dict[route_id] = []
                routes_dict[route_id].append({
                    'trip_id': trip['trip_id'],
                    'stop_sequence': trip['stop_sequence']
                })
            
            stops_with_trips.append({
                'stop_id': stop_id,
                'stop_name': stop['stop_name'],
                'stop_code': stop['stop_code'],
                'stop_lat': stop['stop_lat'],
                'stop_lon': stop['stop_lon'],
                'distrito': stop.get('distrito', ''),
                'total_trips': len(trips_list),
                'total_routes': len(routes_dict),
                'routes': [
                    {
                        'route_id': route_id,
                        'trips_count': len(trips),
                        'trips': trips
                    }
                    for route_id, trips in sorted(routes_dict.items())
                ]
            })
    
    # Ordenar por número de trips (más concurridas primero)
    stops_with_trips.sort(key=lambda x: x['total_trips'], reverse=True)
    
    # 6. Guardar archivo
    output_file = base_path / 'stops_to_trips_index.json'
    
    output_data = {
        'metadata': {
            'total_stops': len(stops_with_trips),
            'total_trips': len(trip_files),
            'total_connections': total_connections,
            'avg_trips_per_stop': avg_trips if trips_per_stop else 0,
            'max_trips_per_stop': max_trips if trips_per_stop else 0,
            'min_trips_per_stop': min_trips if trips_per_stop else 0,
            'busiest_stop': {
                'stop_id': busiest_stop_id if trips_per_stop else '',
                'stop_name': busiest_stop_name if trips_per_stop else '',
                'trips_count': max_trips if trips_per_stop else 0
            }
        },
        'stops': stops_with_trips
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    file_size = output_file.stat().st_size / 1024
    print(f"   ✅ Archivo generado: {output_file}")
    print(f"   📊 Tamaño: {file_size:.1f} KB")
    
    # 7. Mostrar top 10 paradas más concurridas
    print("\n" + "=" * 80)
    print("✅ ÍNDICE GENERADO")
    print("=" * 80)
    
    print(f"\n📊 Estadísticas globales:")
    print(f"   • Paradas con servicio: {len(stops_with_trips)}")
    print(f"   • Total de trips: {len(trip_files)}")
    print(f"   • Conexiones parada-trip: {total_connections}")
    print(f"   • Promedio trips/parada: {avg_trips:.1f}")
    
    print(f"\n🏆 Top 10 paradas más concurridas:")
    for i, stop in enumerate(stops_with_trips[:10], 1):
        routes_str = ', '.join([r['route_id'] for r in stop['routes'][:5]])
        if len(stop['routes']) > 5:
            routes_str += f"... (+{len(stop['routes'])-5})"
        print(f"   {i:2d}. {stop['stop_name']:30s} - {stop['total_trips']:3d} trips - Rutas: {routes_str}")
    
    print(f"\n📁 Archivo: stops_to_trips_index.json")
    print("\n💡 Uso: Busca un stop_id para ver todos los trips que pasan por esa parada")

if __name__ == "__main__":
    main()
