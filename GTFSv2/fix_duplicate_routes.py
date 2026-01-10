#!/usr/bin/env python3
"""
Corrige los route_id duplicados en routes.txt
Mantiene UNA SOLA entrada por ruta (Opción A: múltiples operadores, una ruta)
"""

import csv
from pathlib import Path
from collections import defaultdict

def main():
    base_path = Path(__file__).parent
    
    print("=" * 80)
    print("🔧 CORRIGIENDO ROUTE_IDs DUPLICADOS")
    print("=" * 80)
    print()
    
    # Rutas de entrada
    input_routes = base_path.parent / 'GTFS/out/trujillo/gtfs/routes.txt'
    input_trips = base_path.parent / 'GTFS/out/trujillo/gtfs/trips.txt'
    
    # Rutas de salida
    output_routes = base_path / 'gtfs_feed/routes.txt'
    output_trips = base_path / 'gtfs_feed/trips.txt'
    
    # 1. Leer routes.txt
    print("1. Analizando routes.txt...")
    with open(input_routes, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        routes = list(reader)
    
    print(f"   Total rutas en archivo original: {len(routes)}")
    
    # 2. Identificar duplicados
    route_groups = defaultdict(list)
    for idx, route in enumerate(routes):
        route_id = route['route_id']
        route_groups[route_id].append((idx, route))
    
    duplicates = {k: v for k, v in route_groups.items() if len(v) > 1}
    
    print(f"   Rutas únicas: {len(route_groups)}")
    print(f"   Rutas con duplicados: {len(duplicates)}")
    print()
    
    # 3. Mostrar duplicados
    if duplicates:
        print("📋 Rutas duplicadas encontradas:")
        for route_id, instances in sorted(duplicates.items()):
            print(f"\n   {route_id}:")
            for idx, route in instances:
                agency_id = route.get('agency_id', 'N/A')
                print(f"     - Línea {idx+2}, agency_id: {agency_id}")
    print()
    
    # 4. Decidir qué ruta mantener (primera ocurrencia)
    print("2. Seleccionando rutas únicas...")
    unique_routes = []
    kept_agencies = {}
    
    for route_id, instances in sorted(route_groups.items()):
        # Mantener solo la primera ocurrencia
        first_route = instances[0][1]
        unique_routes.append(first_route)
        
        if len(instances) > 1:
            # Guardar info de qué agencias operan esta ruta
            agencies = [r['agency_id'] for _, r in instances]
            kept_agencies[route_id] = agencies
            print(f"   {route_id}: Mantenida primera, fusionadas {len(instances)} agencias: {', '.join(agencies)}")
    
    print(f"\n   ✅ Rutas después de unificación: {len(unique_routes)}")
    print()
    
    # 5. Escribir routes.txt corregido
    print("3. Generando routes.txt corregido...")
    with open(output_routes, 'w', newline='', encoding='utf-8') as f:
        fieldnames = routes[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_routes)
    
    print(f"   ✅ {output_routes}")
    print()
    
    # 6. Verificar trips.txt (no necesita cambios porque los trip_id ya apuntan a route_id correcto)
    print("4. Verificando trips.txt...")
    with open(input_trips, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        trips = list(reader)
    
    # Contar trips por route_id
    trips_per_route = defaultdict(int)
    for trip in trips:
        trips_per_route[trip['route_id']] += 1
    
    print(f"   Total trips: {len(trips)}")
    
    # Mostrar trips de las rutas que tenían duplicados
    if kept_agencies:
        print("\n   📊 Trips por ruta unificada:")
        for route_id in sorted(kept_agencies.keys()):
            count = trips_per_route[route_id]
            agencies = kept_agencies[route_id]
            print(f"     {route_id}: {count} trips (de {len(agencies)} agencias)")
    
    # Copiar trips.txt sin cambios (ya está correcto)
    with open(output_trips, 'w', newline='', encoding='utf-8') as f:
        fieldnames = trips[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trips)
    
    print(f"\n   ✅ {output_trips} (sin cambios necesarios)")
    print()
    
    # 7. Resumen final
    print("=" * 80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("📊 Resumen:")
    print(f"   • Rutas antes: {len(routes)}")
    print(f"   • Rutas después: {len(unique_routes)}")
    print(f"   • Duplicados eliminados: {len(routes) - len(unique_routes)}")
    print(f"   • Trips totales: {len(trips)} (sin cambios)")
    print()
    print("📁 Archivos generados:")
    print(f"   • {output_routes.relative_to(base_path)}")
    print(f"   • {output_trips.relative_to(base_path)}")
    print()
    print("💡 Próximo paso:")
    print("   Regenerar gtfs_trujillo.zip con los archivos corregidos")

if __name__ == "__main__":
    main()
