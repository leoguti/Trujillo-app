#!/usr/bin/env python3
"""
Genera los archivos GTFS finales:
- stops.txt: Todas las paradas con sus coordenadas
- stop_times.txt: Secuencias de paradas por trip con tiempos estimados
"""

import json
import csv
from pathlib import Path

def generate_stops_txt(stops_data, output_file):
    """Genera stops.txt desde stops_with_ids_final.json"""
    print("📝 Generando stops.txt...")
    
    fieldnames = [
        'stop_id',
        'stop_code',
        'stop_name',
        'stop_lat',
        'stop_lon',
        'location_type',
        'parent_station'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for stop in stops_data['stops']:
            writer.writerow({
                'stop_id': stop['stop_id'],
                'stop_code': stop['stop_code'],
                'stop_name': stop['stop_name'],
                'stop_lat': stop['stop_lat'],
                'stop_lon': stop['stop_lon'],
                'location_type': 0,  # 0 = stop/platform
                'parent_station': ''
            })
    
    print(f"   ✅ {len(stops_data['stops'])} paradas escritas en {output_file}")

def generate_stop_times_txt(trip_files, output_file):
    """Genera stop_times.txt desde archivos trip_*.json"""
    print("\n📝 Generando stop_times.txt...")
    
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
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for trip_file in sorted(trip_files):
            with open(trip_file, 'r', encoding='utf-8') as tf:
                trip_data = json.load(tf)
            
            trip_id = trip_data['trip_id']
            num_stops = len(trip_data['stops_sequence'])
            
            # Generar tiempos estimados: 2 minutos entre paradas
            # Inicio a las 06:00:00
            start_time_minutes = 6 * 60  # 360 minutos = 6:00 AM
            
            for stop_info in trip_data['stops_sequence']:
                stop_seq = stop_info['stop_sequence']
                time_minutes = start_time_minutes + (stop_seq - 1) * 2
                
                hours = time_minutes // 60
                minutes = time_minutes % 60
                time_str = f"{hours:02d}:{minutes:02d}:00"
                
                # Primera parada: solo pickup
                # Última parada: solo drop_off
                # Resto: ambos
                if stop_seq == 1:
                    pickup_type = 0  # Regular pickup
                    drop_off_type = 1  # No drop off
                elif stop_seq == num_stops:
                    pickup_type = 1  # No pickup
                    drop_off_type = 0  # Regular drop off
                else:
                    pickup_type = 0  # Regular pickup
                    drop_off_type = 0  # Regular drop off
                
                writer.writerow({
                    'trip_id': trip_id,
                    'arrival_time': time_str,
                    'departure_time': time_str,
                    'stop_id': stop_info['stop_id'],
                    'stop_sequence': stop_seq,
                    'pickup_type': pickup_type,
                    'drop_off_type': drop_off_type
                })
                
                total_stop_times += 1
    
    print(f"   ✅ {total_stop_times} stop_times escritos en {output_file}")
    print(f"   📊 Promedio: {total_stop_times / len(trip_files):.1f} paradas por trip")

def main():
    base_path = Path(__file__).parent
    
    print("=" * 80)
    print("📋 GENERANDO ARCHIVOS GTFS FINALES")
    print("=" * 80)
    
    # 1. Generar stops.txt
    print("\n1. Procesando stops.txt...")
    stops_file = base_path / 'stops_with_ids_final.json'
    with open(stops_file, 'r', encoding='utf-8') as f:
        stops_data = json.load(f)
    
    output_stops = base_path / 'stops.txt'
    generate_stops_txt(stops_data, output_stops)
    
    # 2. Generar stop_times.txt
    print("\n2. Procesando stop_times.txt...")
    trip_files = sorted(base_path.glob('trip_*.json'))
    print(f"   📁 Encontrados {len(trip_files)} archivos trip_*.json")
    
    output_stop_times = base_path / 'stop_times.txt'
    generate_stop_times_txt(trip_files, output_stop_times)
    
    # Resumen final
    print("\n" + "=" * 80)
    print("✅ ARCHIVOS GTFS GENERADOS")
    print("=" * 80)
    print(f"\n📁 Archivos creados:")
    print(f"   • stops.txt ({stops_data['total_stops']} paradas)")
    print(f"   • stop_times.txt ({len(trip_files)} trips)")
    print(f"\n📦 Paradas totales:")
    print(f"   • Regulares: {stops_data['total_stops'] - stops_data['synthetic_stops']}")
    print(f"   • Sintéticas: {stops_data['synthetic_stops']}")
    print(f"   • Total: {stops_data['total_stops']}")

if __name__ == "__main__":
    main()
