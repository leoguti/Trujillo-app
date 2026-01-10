#!/usr/bin/env python3
"""
Genera stop_ids únicos para las paradas
Agrega sufijos _1, _2, etc. a nombres duplicados
"""

import json
from collections import defaultdict
from pathlib import Path

def generate_unique_stop_ids(stops_geojson_file, output_file):
    """Genera stop_ids únicos y guarda el mapeo"""
    
    print("=" * 80)
    print("🔢 GENERANDO STOP_IDS ÚNICOS")
    print("=" * 80)
    
    # Cargar paradas
    print("\n1. Cargando paradas...")
    with open(stops_geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = len(data['features'])
    print(f"   ✅ {total} paradas cargadas")
    
    # Agrupar por nombre para detectar duplicados
    print("\n2. Analizando nombres...")
    grupos = defaultdict(list)
    for idx, feature in enumerate(data['features']):
        nombre = feature['properties']['nombre']
        grupos[nombre].append(idx)
    
    duplicados = {nombre: indices for nombre, indices in grupos.items() if len(indices) > 1}
    print(f"   ✅ {len(grupos)} nombres únicos")
    print(f"   ⚠️  {len(duplicados)} nombres duplicados")
    
    # Generar stop_ids
    print("\n3. Generando stop_ids...")
    stops_data = []
    
    for nombre, indices in grupos.items():
        if len(indices) == 1:
            # Nombre único - usar tal cual
            idx = indices[0]
            feature = data['features'][idx]
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            stops_data.append({
                'stop_id': nombre,
                'stop_code': nombre,
                'stop_name': nombre,
                'stop_lat': coords[1],
                'stop_lon': coords[0],
                'distrito': props['distrito'],
                'original_index': idx
            })
        else:
            # Nombre duplicado - agregar sufijos
            for suffix_idx, idx in enumerate(indices, 1):
                feature = data['features'][idx]
                coords = feature['geometry']['coordinates']
                props = feature['properties']
                
                stop_id = f"{nombre}_{suffix_idx}"
                
                stops_data.append({
                    'stop_id': stop_id,
                    'stop_code': nombre,  # Código original sin sufijo
                    'stop_name': stop_id, # Nombre con sufijo para diferenciar
                    'stop_lat': coords[1],
                    'stop_lon': coords[0],
                    'distrito': props['distrito'],
                    'original_index': idx
                })
    
    # Ordenar por índice original para mantener orden
    stops_data.sort(key=lambda x: x['original_index'])
    
    print(f"   ✅ {len(stops_data)} stop_ids generados")
    
    # Guardar resultado
    print(f"\n4. Guardando resultado...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_stops': len(stops_data),
            'unique_names': len(grupos),
            'duplicated_names': len(duplicados),
            'stops': stops_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Archivo guardado: {output_file.name}")
    
    # Mostrar ejemplos de duplicados
    if duplicados:
        print(f"\n5. Ejemplos de stop_ids con sufijos:")
        for nombre in list(duplicados.keys())[:5]:
            stops_con_sufijo = [s for s in stops_data if s['stop_code'] == nombre]
            print(f"   • {nombre}:")
            for stop in stops_con_sufijo:
                print(f"     → {stop['stop_id']} ({stop['distrito']})")
    
    print("\n" + "=" * 80)
    print("✅ COMPLETADO")
    print("=" * 80)
    
    return stops_data

def main():
    base_path = Path(__file__).parent
    
    stops_file = base_path / 'paraderos_consolidados.geojson'
    output_file = base_path / 'stops_with_ids.json'
    
    stops_data = generate_unique_stop_ids(stops_file, output_file)
    
    print(f"\n📊 Resumen:")
    print(f"   • Total de paradas: {len(stops_data)}")
    print(f"   • IDs únicos generados: {len(stops_data)}")

if __name__ == "__main__":
    main()
