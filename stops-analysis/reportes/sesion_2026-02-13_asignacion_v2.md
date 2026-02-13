# Sesión 2026-02-13: Asignación de paradas v2

## Problema

El algoritmo v1 que generó `relaciones_con_paradas.osm` tenía dos defectos:

### 1. Rutas con doble paso (multi-paso)
Si una ruta pasa dos veces por la misma vía (ej: rutas que hacen bucle como M-30 D, M-32 A1-B1), la parada solo aparecía una vez en la relación. En PTv2, debe aparecer dos veces: una por cada paso del bus.

### 2. Dirección de la primera vía
El producto cruzado (cross product) que determina izquierda/derecha fallaba al inicio de las rutas porque la dirección de la primera vía no se resolvía correctamente. Se asumía forward, pero muchas rutas comienzan con la vía en sentido inverso.

### 3. Bug de versiones en v1 (heredado de sesión anterior)
En la sesión del 12/feb, al generar el .osm de relaciones, todas tenían `version="1"` pero en el servidor OSM tenían versiones reales (7-15). JOSM detectaba esto como conflicto al intentar subir. Se corrigió manualmente consultando Overpass, pero era un problema estructural del script.

## Solución: `asignar_paradas_v2.py`

Script nuevo que descarga datos frescos de Overpass y reconstruye todas las asignaciones desde cero.

### Arquitectura del script

```
Overpass API
  ├── Query 1: Relaciones (out meta) + Vías (out body) + Nodos (out skel)
  └── Query 2: Paradas municipales (out meta)
         ↓
Way Chaining: encadenar vías en polilínea continua
         ↓
cKDTree: índice espacial de paradas (una vez, se reutiliza)
         ↓
Walk-and-Assign: caminar segmento a segmento, asignar paradas
         ↓
relaciones_con_paradas.osm + reporte_asignacion_v2.csv
```

### Fix 1: Multi-paso
El algoritmo agrupa los "hits" de cada parada por segmento. Si hay un gap > 5 segmentos entre hits consecutivos de la misma parada, los separa en grupos independientes. Cada grupo genera una asignación separada → la parada aparece múltiples veces en la relación.

### Fix 2: Dirección de primera vía
En vez de asumir que la primera vía va forward, se compara con la segunda vía:
- Si comparten nodo → se determina la dirección por el nodo compartido
- Si no comparten nodo → heurística de distancia mínima en UTM entre endpoints

### Fix 3: Versiones correctas
Se usa `out meta` en la consulta Overpass para relaciones, que retorna la versión actual del servidor. Esto elimina completamente el problema de conflictos de versiones en JOSM.

## Resultados

| Métrica | v1 | v2 | Diferencia |
|---------|----|----|------------|
| Total asignaciones | 10,017 | 10,255 | +238 |
| Paraderos únicos asignados | 1,368 | 1,398 | +30 |
| Rutas procesadas | 214 | 214 | = |
| Paradas repetidas (multi-paso) | 0 | 104 | +104 |
| Rutas con paradas repetidas | 0 | 29 | +29 |
| Rutas con cambios vs v1 | — | 174 | — |

### Rutas con más paradas repetidas (multi-paso)
| Ruta | Repetidas | Total paradas |
|------|-----------|---------------|
| M-30 D (ida) | 21 | 78 |
| M-30 D (vuelta) | 19 | 70 |
| M-32 A1-B1 (ida) | 12 | 82 |
| M-32 A1-B1 (vuelta) | 12 | 78 |
| M-05 H (ida) | 4 | 84 |
| M-05 H (vuelta) | 4 | 79 |

### Verificación piloto C-10 M ida (relación 19967562)
- v1: 22 paradas (verificadas manualmente en sesión anterior)
- v2: 22 paradas (mismas, confirmado)

### Versiones de relaciones
- Rango: 6 - 20 (todas con versión real del servidor)
- Ninguna con version="1" (bug de v1 eliminado)

## Archivos generados

| Archivo | Descripción |
|---------|-------------|
| `asignar_paradas_v2.py` | Script completo (descarga, encadena, asigna, genera) |
| `relaciones_con_paradas.osm` | Mismo nombre que v1 para que git registre el diff |
| `reporte_asignacion_v2.csv` | Comparación ruta por ruta: v1 vs v2 |

## Decisión: mismo nombre de archivo

Se decidió mantener el nombre `relaciones_con_paradas.osm` (no usar `_v2.osm`) para que git pueda mostrar el diff entre la versión anterior y la nueva. El reporte comparativo sí se llama `reporte_asignacion_v2.csv` porque es un archivo nuevo.

## Dependencias del script

```python
import json, csv, math, time, urllib.request, urllib.parse
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer
from lxml import etree
```

## Parámetros clave

| Parámetro | Valor | Uso |
|-----------|-------|-----|
| BUFFER_M | 20m | Distancia máxima de parada a segmento de ruta |
| SEARCH_EXTRA_M | 25m | Margen adicional para búsqueda en cKDTree |
| GAP_THRESHOLD | 5 segmentos | Separación mínima para considerar un nuevo "paso" |
| MIN_SEGMENT_LEN_M | 0.1m | Ignorar segmentos degenerados |

## Filtro de falsos positivos (agregado en la misma sesión)

### Problema detectado
En zonas urbanas densas con calles paralelas (ej: Jirón Unión / Av. España), el buffer de 20m atrapa paradas de calles adyacentes. Una parada puede estar a 18m de la ruta asignada pero a solo 1m de otra ruta — claramente pertenece a la otra vía.

### Análisis previo
Se ejecutó `analisis_falsos_positivos.py` que evaluó las 10,255 asignaciones:
- 78.5% están a 0-8m (saludable)
- 7.4% (759) están a 12-20m (zona de riesgo)
- **122 asignaciones sospechosas** (1.2%) donde otra ruta pasa significativamente más cerca
- Solo **28 paradas físicas** afectadas, pero se propagan a múltiples rutas

### Solución implementada: filtro relativo
Criterio de rechazo (las 3 condiciones deben cumplirse):
1. `dist_a_esta_ruta > 15m`
2. `dist_a_otra_ruta < 10m`
3. `ratio dist/rival > 3x`

### Resultado del filtro
- **83 asignaciones removidas** de 10,255 → quedan **10,172**
- **24 paradas únicas** afectadas
- Peores casos eliminados: ABR-365 (ratio 76:1), PL-46 (18:1), PAT-141 (17:1)
- El piloto C-10 M pasó de 22 a 21 paradas (IN-167 eliminada, estaba a 17.73m de C-10 M pero a 4.81m de M-02 A)

### Parámetros del filtro
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| FP_MIN_DIST_M | 15m | Solo revisar asignaciones a más de 15m |
| FP_RIVAL_MAX_M | 10m | Rechazar si otra ruta pasa a menos de 10m |
| FP_RATIO_MIN | 3.0 | Rechazar si ratio distancia/rival supera 3x |

### Archivos de análisis
- `analisis_falsos_positivos.py` — Script de diagnóstico
- `falsos_positivos.csv` — Todas las 10,255 asignaciones con distancias
- `falsos_positivos_detalle.csv` — 122 asignaciones sospechosas

## Mejora adicional: caché de Overpass
El script ahora guarda las respuestas de Overpass en `cache_overpass/` (JSON). En ejecuciones posteriores usa el caché en vez de re-descargar. Para forzar datos frescos, borrar la carpeta `cache_overpass/`.

## Próximos pasos

- Subir `relaciones_con_paradas.osm` via JOSM (214 relaciones)
- Verificar visualmente en JOSM que las rutas con multi-paso tengan sentido
- Suspender 5 rutas rurales del GTFS (C-15, C-30, C-31, C-32, C-33)
