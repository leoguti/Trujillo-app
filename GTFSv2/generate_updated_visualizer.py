#!/usr/bin/env python3
"""
Genera visualizador actualizado que permite seleccionar cualquier trip
de los 210 procesados y ver sus paradas asignadas.
"""

import json
import csv
from pathlib import Path

def load_trips_info():
    """Carga información de trips desde trips.txt"""
    base_path = Path(__file__).parent
    trips_file = base_path.parent / 'GTFS/out/trujillo/gtfs/trips.txt'
    
    with open(trips_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_shapes_coords():
    """Carga coordenadas de todas las shapes"""
    base_path = Path(__file__).parent
    shapes_file = base_path.parent / 'GTFS/out/trujillo/gtfs/shapes.txt'
    
    shapes_dict = {}
    
    with open(shapes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            shape_id = row['shape_id']
            if shape_id not in shapes_dict:
                shapes_dict[shape_id] = []
            
            shapes_dict[shape_id].append({
                'lat': float(row['shape_pt_lat']),
                'lon': float(row['shape_pt_lon']),
                'seq': int(row['shape_pt_sequence'])
            })
    
    # Ordenar por secuencia
    for shape_id in shapes_dict:
        shapes_dict[shape_id].sort(key=lambda x: x['seq'])
    
    return shapes_dict

def load_all_stops():
    """Carga todas las paradas desde stops_with_ids_final.json"""
    base_path = Path(__file__).parent
    stops_file = base_path / 'stops_with_ids_final.json'
    
    with open(stops_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['stops']

def load_trip_stops(trip_id):
    """Carga paradas de un trip específico"""
    base_path = Path(__file__).parent
    trip_file = base_path / f'trip_{trip_id}_stops.json'
    
    try:
        with open(trip_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def generate_html():
    """Genera el HTML del visualizador"""
    
    print("Cargando datos...")
    trips = load_trips_info()
    shapes = load_shapes_coords()
    all_stops = load_all_stops()
    
    # Crear índice de paradas
    stops_index = {s['stop_id']: s for s in all_stops}
    
    # Organizar trips por ruta
    routes_dict = {}
    for trip in trips:
        route_id = trip['route_id']
        if route_id not in routes_dict:
            routes_dict[route_id] = []
        routes_dict[route_id].append(trip)
    
    print(f"  ✓ {len(trips)} trips")
    print(f"  ✓ {len(shapes)} shapes")
    print(f"  ✓ {len(all_stops)} paradas")
    print(f"  ✓ {len(routes_dict)} rutas")
    
    # Preparar datos para el visualizador
    trips_data = []
    for trip in trips:
        trip_stops = load_trip_stops(trip['trip_id'])
        if trip_stops:
            # Cargar coordenadas de paradas
            stops_with_coords = []
            for stop_info in trip_stops['stops_sequence']:
                stop_id = stop_info['stop_id']
                if stop_id in stops_index:
                    stop = stops_index[stop_id]
                    stops_with_coords.append({
                        'stop_sequence': stop_info['stop_sequence'],
                        'stop_id': stop_id,
                        'stop_name': stop['stop_name'],
                        'lat': stop['stop_lat'],
                        'lon': stop['stop_lon'],
                        'is_synthetic': stop_id.startswith('SYNTH_')
                    })
            
            trips_data.append({
                'trip_id': trip['trip_id'],
                'route_id': trip['route_id'],
                'shape_id': trip['shape_id'],
                'stops': stops_with_coords
            })
    
    print(f"\nGenerando HTML...")
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Visualizador de Trips - GTFS Trujillo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 350px;
            max-height: 90vh;
            overflow-y: auto;
        }}
        .info-panel h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
            color: #333;
        }}
        .info-panel h3 {{
            margin: 10px 0 5px 0;
            font-size: 14px;
            color: #666;
        }}
        .selector {{
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-size: 14px;
        }}
        .stats {{
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 3px;
            font-size: 13px;
        }}
        .stats-item {{
            margin: 5px 0;
        }}
        .toggle-button {{
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}
        .toggle-button:hover {{
            background: #45a049;
        }}
        .toggle-button.hidden {{
            background: #f44336;
        }}
        .legend {{
            margin: 10px 0;
            padding: 8px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-size: 12px;
        }}
        .legend-item {{
            margin: 5px 0;
            display: flex;
            align-items: center;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 50%;
            border: 2px solid #333;
        }}
        .stop-label {{
            pointer-events: none !important;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>🚌 Visualizador de Trips</h2>
        
        <h3>Seleccionar Ruta:</h3>
        <select id="routeSelector" class="selector">
            <option value="">Todas las rutas</option>
        </select>
        
        <h3>Seleccionar Trip:</h3>
        <select id="tripSelector" class="selector">
            <option value="">Seleccione un trip</option>
        </select>
        
        <div class="stats" id="statsPanel" style="display:none;">
            <div class="stats-item"><strong>Trip ID:</strong> <span id="tripId"></span></div>
            <div class="stats-item"><strong>Ruta:</strong> <span id="routeId"></span></div>
            <div class="stats-item"><strong>Paradas:</strong> <span id="stopCount"></span></div>
            <div class="stats-item"><strong>Sintéticas:</strong> <span id="syntheticCount"></span></div>
        </div>
        
        <button id="toggleStops" class="toggle-button" style="display:none;">
            👁️ Ocultar Paradas
        </button>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50;"></div>
                <span>Parada Regular</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FFC107;"></div>
                <span>Parada Sintética</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2196F3;"></div>
                <span>Ruta del Trip</span>
            </div>
        </div>
    </div>

    <script>
        // Datos
        const tripsData = {json.dumps(trips_data, ensure_ascii=False)};
        const shapesData = {json.dumps(shapes, ensure_ascii=False)};
        
        // Inicializar mapa
        const map = L.map('map').setView([-8.1116, -79.0288], 13);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);
        
        // Capas
        let routeLayer = null;
        let stopsLayer = null;
        let stopsVisible = true;
        
        // Selectores
        const routeSelector = document.getElementById('routeSelector');
        const tripSelector = document.getElementById('tripSelector');
        const statsPanel = document.getElementById('statsPanel');
        const toggleButton = document.getElementById('toggleStops');
        
        // Organizar trips por ruta
        const tripsByRoute = {{}};
        tripsData.forEach(trip => {{
            if (!tripsByRoute[trip.route_id]) {{
                tripsByRoute[trip.route_id] = [];
            }}
            tripsByRoute[trip.route_id].push(trip);
        }});
        
        // Poblar selector de rutas
        const sortedRoutes = Object.keys(tripsByRoute).sort();
        sortedRoutes.forEach(routeId => {{
            const option = document.createElement('option');
            option.value = routeId;
            option.textContent = `${{routeId}} (${{tripsByRoute[routeId].length}} trips)`;
            routeSelector.appendChild(option);
        }});
        
        // Event: cambio de ruta
        routeSelector.addEventListener('change', function() {{
            const selectedRoute = this.value;
            
            // Limpiar selector de trips
            tripSelector.innerHTML = '<option value="">Seleccione un trip</option>';
            
            if (selectedRoute) {{
                const trips = tripsByRoute[selectedRoute];
                trips.forEach(trip => {{
                    const option = document.createElement('option');
                    option.value = trip.trip_id;
                    option.textContent = `Trip ${{trip.trip_id}} (${{trip.stops.length}} paradas)`;
                    tripSelector.appendChild(option);
                }});
            }} else {{
                // Mostrar todos los trips
                tripsData.forEach(trip => {{
                    const option = document.createElement('option');
                    option.value = trip.trip_id;
                    option.textContent = `${{trip.route_id}} - Trip ${{trip.trip_id}}`;
                    tripSelector.appendChild(option);
                }});
            }}
            
            // Limpiar mapa
            clearMap();
        }});
        
        // Event: cambio de trip
        tripSelector.addEventListener('change', function() {{
            const tripId = this.value;
            if (tripId) {{
                displayTrip(tripId);
            }} else {{
                clearMap();
            }}
        }});
        
        // Event: toggle paradas
        toggleButton.addEventListener('click', function() {{
            stopsVisible = !stopsVisible;
            if (stopsLayer) {{
                if (stopsVisible) {{
                    map.addLayer(stopsLayer);
                    toggleButton.textContent = '👁️ Ocultar Paradas';
                    toggleButton.classList.remove('hidden');
                }} else {{
                    map.removeLayer(stopsLayer);
                    toggleButton.textContent = '👁️ Mostrar Paradas';
                    toggleButton.classList.add('hidden');
                }}
            }}
        }});
        
        function clearMap() {{
            if (routeLayer) {{
                map.removeLayer(routeLayer);
                routeLayer = null;
            }}
            if (stopsLayer) {{
                map.removeLayer(stopsLayer);
                stopsLayer = null;
            }}
            statsPanel.style.display = 'none';
            toggleButton.style.display = 'none';
        }}
        
        function displayTrip(tripId) {{
            clearMap();
            
            const trip = tripsData.find(t => t.trip_id === tripId);
            if (!trip) return;
            
            // Dibujar ruta
            const shapeCoords = shapesData[trip.shape_id];
            if (shapeCoords) {{
                const latLngs = shapeCoords.map(pt => [pt.lat, pt.lon]);
                routeLayer = L.polyline(latLngs, {{
                    color: '#2196F3',
                    weight: 4,
                    opacity: 0.7
                }}).addTo(map);
                
                map.fitBounds(routeLayer.getBounds(), {{padding: [50, 50]}});
            }}
            
            // Dibujar paradas
            stopsLayer = L.layerGroup();
            let syntheticCount = 0;
            
            trip.stops.forEach(stop => {{
                const isSynthetic = stop.is_synthetic;
                if (isSynthetic) syntheticCount++;
                
                // Popup con información
                const popupContent = '<div style="min-width: 200px;">' +
                    '<strong>' + stop.stop_name + '</strong><br>' +
                    '<small>' +
                    'Stop ID: ' + stop.stop_id + '<br>' +
                    'Secuencia: ' + stop.stop_sequence + '<br>' +
                    (isSynthetic ? '⚠️ PARADA SINTÉTICA' : '') +
                    '</small>' +
                    '</div>';
                
                // Círculo de color más grande (fondo)
                const marker = L.circleMarker([stop.lat, stop.lon], {{
                    radius: 12,
                    fillColor: isSynthetic ? '#FFC107' : '#4CAF50',
                    color: '#fff',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 0.95
                }});
                
                // Bind popup y evento de click
                marker.bindPopup(popupContent);
                marker.on('click', function(e) {{
                    this.openPopup();
                }});
                
                stopsLayer.addLayer(marker);
                
                // Label con número encima (más pequeño, con fondo transparente)
                const label = L.marker([stop.lat, stop.lon], {{
                    icon: L.divIcon({{
                        className: 'stop-label',
                        html: '<div style="width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); pointer-events: none;">' + stop.stop_sequence + '</div>',
                        iconSize: [24, 24]
                    }})
                }});
                stopsLayer.addLayer(label);
            }});
            
            if (stopsVisible) {{
                map.addLayer(stopsLayer);
            }}
            
            // Actualizar stats
            document.getElementById('tripId').textContent = trip.trip_id;
            document.getElementById('routeId').textContent = trip.route_id;
            document.getElementById('stopCount').textContent = trip.stops.length;
            document.getElementById('syntheticCount').textContent = syntheticCount;
            
            statsPanel.style.display = 'block';
            toggleButton.style.display = 'block';
        }}
    </script>
</body>
</html>'''
    
    return html

def main():
    print("=" * 80)
    print("🎨 GENERANDO VISUALIZADOR ACTUALIZADO")
    print("=" * 80)
    print()
    
    html = generate_html()
    
    output_file = Path(__file__).parent / 'trips_visualizer.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    file_size = output_file.stat().st_size / (1024 * 1024)
    
    print()
    print("=" * 80)
    print("✅ VISUALIZADOR GENERADO")
    print("=" * 80)
    print(f"📁 Archivo: {output_file}")
    print(f"📊 Tamaño: {file_size:.1f} MB")
    print()
    print("🌐 Para ver:")
    print(f"   file://{output_file.absolute()}")

if __name__ == "__main__":
    main()
