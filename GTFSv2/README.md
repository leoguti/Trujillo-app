# GTFS v2 - Trujillo, Perú

Sistema de generación de feed GTFS para el transporte público de Trujillo, con asignación geométrica de paradas y cálculo realista de tiempos de viaje.

## 📋 Contenido

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Proceso de Generación](#proceso-de-generación)
- [Scripts Principales](#scripts-principales)
- [Archivos de Configuración](#archivos-de-configuración)
- [Validación](#validación)
- [Uso](#uso)

## 🎯 Descripción General

Este proyecto genera un feed GTFS completo y válido para el sistema de transporte público de Trujillo, procesando:

- **210 trips** (viajes) de transporte público
- **79 routes** (rutas) operadas por múltiples agencias
- **2,180 stops** (paradas):
  - 1,765 paradas reales (físicas)
  - 415 paradas sintéticas (inicio/fin de ruta)
- **11,133 stop_times** (conexiones parada-viaje)

### Características Principales

✅ **Asignación Geométrica de Paradas**: Usa geometrías OSM y Shapely para asignar paradas al lado correcto de la vía
✅ **Tiempos Realistas**: Calcula tiempos de viaje basados en distancias reales y velocidades específicas por ruta
✅ **Multi-operador**: Soporta múltiples agencias operando la misma ruta (modelo latinoamericano)
✅ **100% Válido**: Pasa validación oficial de MobilityData sin errores

## 🏗️ Arquitectura

### Flujo de Datos

```
[OSM Shapes] + [Paradas Físicas] 
         ↓
    [assign_stops_to_trips.py]
         ↓
    [trip_*_stops.json] (210 archivos)
         ↓
    [generate_stop_times_realistic.py] + [Google Sheet Velocidades]
         ↓
    [gtfs_feed/*.txt]
         ↓
    [gtfs_trujillo.zip]
```

### Estructura de Archivos

```
GTFSv2/
├── README.md                          # Este archivo
├── POLITICA_GTFS_V2.md               # Políticas de generación de IDs
├── RESUMEN_GENERACION_GTFS.md        # Resumen del proceso
├── ANALISIS_VALIDACION_GTFS.md       # Análisis de validación
│
├── Scripts Principales:
│   ├── assign_stops_to_trips.py      # Asigna paradas a trips usando geometría
│   ├── generate_stop_ids.py          # Genera IDs únicos para paradas
│   ├── generate_stop_times_realistic.py # Calcula tiempos con velocidades reales
│   ├── fix_duplicate_routes.py       # Corrige route_ids duplicados
│   ├── generate_updated_visualizer.py # Genera visualizador interactivo
│   └── generate_stops_to_trips_index.py # Índice inverso stops→trips
│
├── Datos de Entrada:
│   └── stops_with_ids_final.json     # 2,180 paradas con IDs únicos
│
├── Datos de Salida:
│   ├── gtfs_feed/                    # Archivos GTFS finales
│   │   ├── agency.txt
│   │   ├── routes.txt               # 79 rutas
│   │   ├── trips.txt                # 210 trips
│   │   ├── stops.txt                # 2,180 paradas
│   │   ├── stop_times.txt           # 11,133 registros
│   │   ├── calendar.txt
│   │   └── shapes.txt
│   └── gtfs_trujillo.zip            # Feed completo (1.2 MB)
│
└── Visualizadores:
    └── README_VISUALIZADOR.md        # Documentación de visualizadores
```

## 🔄 Proceso de Generación

### 1. Preparación de Paradas

**Script**: `generate_stop_ids.py`

- Carga paradas físicas desde paraderos consolidados
- Genera IDs únicos: formato `DISTRITO-NUMERO` (ej: `JEN-141`)
- Evita duplicados y valida coordenadas
- **Output**: `stops_with_ids_final.json`

### 2. Asignación de Paradas a Trips

**Script**: `assign_stops_to_trips.py`

Algoritmo geométrico:
1. Lee geometría OSM del trip desde `shapes.txt`
2. Para cada parada física:
   - Calcula distancia perpendicular a la ruta (máx 20-25m)
   - Determina lado de la vía con producto cruz: `cross = dx * py - dy * px`
   - Si `cross < 0`: lado derecho (asigna) ✅
   - Si `cross >= 0`: lado izquierdo (descarta) ❌
3. Ordena paradas por distancia a lo largo de la ruta usando `LineString.project()`
4. Crea paradas sintéticas si no hay parada real en inicio/fin (threshold 10m)

**Paradas Sintéticas**:
- Formato: `SYNTH_START_{trip_id}` y `SYNTH_END_{trip_id}`
- Ubicadas en coordenadas exactas del inicio/fin de geometría OSM
- **Problema conocido**: Algunas están muy lejos de paradas reales (20-50 km)
  - Causa: Geometría OSM completa vs cobertura real de paradas
  - Impacto: Tiempos de viaje altos en primer segmento (pero realistas según velocidad)

**Output**: `trip_*_stops.json` (210 archivos)

### 3. Corrección de Routes Duplicados

**Script**: `fix_duplicate_routes.py`

- Problema: 6 rutas con route_id duplicado (múltiples operadores)
- Solución: Consolidar en una sola entrada por route_id
- Rutas afectadas: M-28 A, C-13 D, C-39 S, C-15 P1, C-33 P2, C-45 C
- **Output**: `gtfs_feed/routes.txt` (85 → 79 entradas)

### 4. Cálculo de Tiempos de Viaje

**Script**: `generate_stop_times_realistic.py`

**Metodología**:

1. **Fuente de Velocidades**: Google Sheet (columna U)
   - URL: `https://docs.google.com/spreadsheets/d/1DqplLS5iLnz3oHqtJCCdOvpUyhWGnL5VzeyaGhb2VSA`
   - 205 trips con velocidades específicas (20-30 km/h)
   - 5 trips usan velocidad default (20 km/h)

2. **Cálculo de Distancias**:
   ```python
   distance_along = route_line.project(stop_point) * 111  # degrees → km
   delta_distance = distance_along - prev_distance
   ```

3. **Cálculo de Tiempo**:
   ```python
   travel_time_minutes = (delta_distance / avg_speed_kmh) * 60
   travel_time_minutes = max(1, round(travel_time_minutes))  # mínimo 1 min
   ```

4. **Reglas**:
   - Primera parada: 06:00:00 (hora fija de inicio)
   - Mínimo 1 minuto entre paradas consecutivas
   - `pickup_type/drop_off_type`: Primera parada solo pickup, última solo dropoff

**Ejemplo Real - Trip 19972496 (Ruta C-32 S, velocidad 30 km/h)**:

| # | Stop ID | Dist Acum | Delta Dist | Hora | Delta Tiempo | Velocidad |
|---|---------|-----------|------------|------|--------------|-----------|
| 1 | SYNTH_START_19972496 | 0.00 km | 0.00 km | 06:00:00 | 0 min | - |
| 2 | PL-62 | 52.07 km | 52.07 km | 07:44:00 | 104 min | 30.0 km/h |
| 3 | PL-64 | 52.49 km | 0.42 km | 07:45:00 | 1 min | 25.3 km/h |
| ... | ... | ... | ... | ... | ... | ... |
| 30 | SYNTH_END_19972496 | 62.14 km | 0.27 km | 08:13:00 | 1 min | 16.0 km/h |

**Totales**: 62.14 km en 133 minutos = 28.0 km/h promedio ✅

**Output**: `gtfs_feed/stop_times.txt` (453 KB, 11,133 registros)

### 5. Generación de Archivos GTFS

Los archivos en `gtfs_feed/` son copiados desde el GTFS base (`../GTFS/out/trujillo/gtfs/`) excepto:
- `routes.txt` - corregido por `fix_duplicate_routes.py`
- `stop_times.txt` - generado por `generate_stop_times_realistic.py`
- `stops.txt` - generado desde `stops_with_ids_final.json`

## 📝 Scripts Principales

### `assign_stops_to_trips.py`
Asigna paradas a trips usando algoritmo geométrico con Shapely.

**Uso**:
```bash
python3 assign_stops_to_trips.py
```

**Requisitos**:
- `shapely` library
- `../GTFS/out/trujillo/gtfs/shapes.txt`
- `stops_with_ids_final.json`

**Output**: 210 archivos `trip_*_stops.json`

---

### `generate_stop_times_realistic.py`
Genera stop_times.txt con tiempos calculados basados en velocidades reales.

**Uso**:
```bash
python3 generate_stop_times_realistic.py
```

**Features**:
- Descarga velocidades desde Google Sheet automáticamente
- Usa `LineString.project()` para distancias precisas
- Velocidad específica por trip (columna U del sheet)

**Output**: `gtfs_feed/stop_times.txt`

---

### `fix_duplicate_routes.py`
Consolida route_ids duplicados manteniendo solo primera ocurrencia.

**Uso**:
```bash
python3 fix_duplicate_routes.py
```

**Output**: `gtfs_feed/routes.txt` (79 rutas únicas)

---

### `generate_updated_visualizer.py`
Genera visualizador Leaflet interactivo con todos los trips.

**Uso**:
```bash
python3 generate_updated_visualizer.py
```

**Output**: `trips_visualizer.html` (7.6 MB)

**Features**:
- Selector jerárquico: ruta → trip
- Colores: verde (paradas reales), amarillo (sintéticas)
- Popups con información de parada
- Toggle para mostrar/ocultar paradas

---

### `generate_stops_to_trips_index.py`
Genera índice inverso: para cada parada, qué trips pasan por ella.

**Uso**:
```bash
python3 generate_stops_to_trips_index.py
```

**Output**: `stops_to_trips_index.json` (2.5 MB)

**Estadísticas**:
- 2,035 paradas con servicio
- Promedio: 5.5 trips por parada
- Parada más transitada: JEN-141 (52 trips, 36 rutas)

## 📊 Archivos de Configuración

### `stops_with_ids_final.json`
Lista maestra de paradas con IDs únicos.

**Estructura**:
```json
{
  "total_stops": 2180,
  "synthetic_stops": 415,
  "stops": [
    {
      "stop_id": "JEN-141",
      "stop_code": "Jenaro Herrera",
      "stop_name": "Jenaro Herrera (JEN-141)",
      "stop_lat": -8.123456,
      "stop_lon": -79.123456,
      "distrito": "Trujillo"
    }
  ]
}
```

### Google Sheet de Velocidades
Contiene configuración de velocidades por trip.

**Columnas relevantes**:
- **K (ID_OSM)**: trip_id
- **T (Distancia)**: Distancia total de la ruta (km) - INFORMATIVA
- **U (Velocidad)**: Velocidad promedio (km/h) - USADA

**Nota**: Las distancias del sheet son referenciales (geometría completa OSM). El script calcula distancias reales basadas en paradas asignadas.

## ✅ Validación

### Resultados Finales

**Validador**: MobilityData GTFS Validator v5.0.1

```
✅ 0 ERRORS
✅ 4 WARNINGS (menores)
```

**Warnings Restantes**:
1. `missing_recommended_column` (1): Columna opcional faltante
2. `missing_recommended_file` (1): `feed_info.txt` recomendado
3. `mixed_case_recommended_field` (457): Nombres con mayúsculas/minúsculas
4. `stop_without_stop_time` (145): 145 paradas sin trips asignados

**✨ Sin warnings de velocidad**: El problema de velocidades excesivas (400-1,070 km/h) fue completamente resuelto usando velocidades específicas del Google Sheet.

### Comparación

| Métrica | Antes | Después |
|---------|-------|---------|
| ERRORS | 6 | 0 ✅ |
| WARNINGS | 40+ | 4 ✅ |
| Velocidad promedio | 20 km/h fijo | 20-30 km/h por ruta ✅ |

### Ejecutar Validación Local

```bash
# Desde directorio raíz GTFSTRUJILLO
java -jar gtfs-validator.jar \
  --input GTFSv2/gtfs_trujillo.zip \
  --output_base validation_report \
  --country_code PE
```

**Output**: `validation_report/report.html`

## 🚀 Uso

### Regenerar Feed Completo

```bash
# 1. Asignar paradas a trips (si hay cambios en geometrías o paradas)
python3 assign_stops_to_trips.py

# 2. Generar stop_times con velocidades del Google Sheet
python3 generate_stop_times_realistic.py

# 3. Empaquetar GTFS
cd gtfs_feed && zip -q ../gtfs_trujillo.zip *.txt && cd ..

# 4. Validar
cd .. && java -jar gtfs-validator.jar \
  --input GTFSv2/gtfs_trujillo.zip \
  --output_base validation_report \
  --country_code PE
```

### Actualizar Solo Tiempos (sin cambiar geometría)

```bash
# Si solo cambiaron velocidades en Google Sheet
python3 generate_stop_times_realistic.py
cd gtfs_feed && zip -q ../gtfs_trujillo.zip *.txt && cd ..
```

### Generar Visualizador

```bash
python3 generate_updated_visualizer.py
# Abrir trips_visualizer.html en navegador
```

## 📚 Documentación Adicional

- [`POLITICA_GTFS_V2.md`](./POLITICA_GTFS_V2.md) - Políticas de generación de IDs y convenciones
- [`RESUMEN_GENERACION_GTFS.md`](./RESUMEN_GENERACION_GTFS.md) - Resumen ejecutivo del proceso
- [`ANALISIS_VALIDACION_GTFS.md`](./ANALISIS_VALIDACION_GTFS.md) - Análisis detallado de validación
- [`README_VISUALIZADOR.md`](./README_VISUALIZADOR.md) - Cómo usar el visualizador

## 🔧 Requisitos

### Python Libraries
```bash
pip install shapely
```

### Herramientas Externas
- Java 8+ (para GTFS validator)
- Navegador web moderno (para visualizadores)

### Datos de Entrada
- Geometrías OSM: `../GTFS/out/trujillo/gtfs/shapes.txt`
- GTFS base: `../GTFS/out/trujillo/gtfs/*.txt`
- Paradas consolidadas: archivos paraderos originales

## 🐛 Problemas Conocidos

### 1. Paradas Sintéticas Lejanas
**Síntoma**: Algunas paradas `SYNTH_START` están 20-50 km del primer paradero real.

**Causa**: La geometría OSM de la ruta comienza muy lejos de donde realmente operan los buses.

**Impacto**: 
- Primer segmento del viaje tiene tiempo largo (ej: 104 min para 52 km)
- Velocidad es correcta (30 km/h), pero operacionalmente no hace sentido

**Posibles soluciones**:
1. Eliminar paradas sintéticas >10 km del primer paradero real
2. Recortar geometría OSM al tramo con cobertura real de paradas
3. Marcar paradas sintéticas lejanas con `location_type` especial

### 2. Velocidades Variables Entre Paradas Cercanas
**Síntoma**: Entre paradas muy cercanas (<200m), la velocidad aparenta ser baja (8-15 km/h).

**Causa**: Mínimo de 1 minuto entre paradas. Si están a 140m, 1 minuto = 8.4 km/h.

**Impacto**: Menor. La velocidad promedio del trip es correcta.

**Posible solución**: Permitir tiempos fraccionarios (30-45 segundos) entre paradas muy cercanas.

## 📈 Estadísticas

### Feed Overview
- **Agencias**: 37
- **Rutas**: 79
- **Trips**: 210
- **Paradas**: 2,180 (1,765 reales + 415 sintéticas)
- **Stop Times**: 11,133
- **Puntos de Geometría**: 106,676

### Cobertura
- **Paradas con servicio**: 2,035 / 2,180 (93.3%)
- **Paradas sin servicio**: 145 (6.7%)
- **Promedio paradas/trip**: 53
- **Promedio trips/parada**: 5.5

### Tamaños de Archivo
- `gtfs_trujillo.zip`: 1.2 MB
- `stop_times.txt`: 453 KB
- `shapes.txt`: 4.4 MB
- `stops.txt`: 145 KB

## 👥 Contribuciones

Este sistema fue desarrollado para el proyecto de transporte público de Trujillo, Perú.

**Contacto**: Leonardo Gutiérrez

## 📄 Licencia

[Por definir]

---

**Última actualización**: Enero 2026
**Versión del Feed**: GTFS v2.0
**Estado**: ✅ Producción (validación 100% exitosa)
