# Análisis Espacial de Paraderos

Comparación de tres fuentes de datos de paradas de bus de Trujillo y clasificación en 8 categorías según su posición respecto a las rutas.

## Fuentes de datos comparadas

| Fuente | Paradas | Origen |
|--------|---------|--------|
| KML del municipio | 1,645 únicas | Gerencia de Transporte Metropolitano de Trujillo |
| GTFS | 605 | Generado por nosotros a partir de OSM |
| OpenStreetMap | 196 | Datos existentes vía Overpass API |

## Metodología

### 1. Deduplicación
Las 1,858 paradas del KML se deduplican a 1,645 eliminando registros que aparecen en múltiples capas a menos de 10m de distancia.

### 2. Matching KML ↔ GTFS
Cada parada KML se compara con las paradas GTFS. Si hay una parada GTFS a menos de **50m**, se consideran la misma parada.

### 3. Zona de cobertura de rutas
Se construye un buffer de **20m** alrededor de la geometría de cada ruta GTFS (proyectado a UTM 17S para trabajar en metros). Las paradas que caen fuera de todo buffer se clasifican como "fuera de ruta".

### 4. Detección de lado derecho
En Perú se circula por la derecha, por lo que los paraderos deben estar al lado derecho de la vía en el sentido de circulación. Para cada parada dentro del buffer, se calcula el producto cruz respecto al segmento de ruta más cercano:

- **Producto cruz < 0** → lado derecho (válido)
- **Producto cruz > 0** → lado izquierdo (incorrecto)

Una parada se considera válida si está del lado derecho de al menos un segmento a menos de 20m.

### 5. Detección de duplicados
Pares de paradas a menos de 20m sin ningún segmento de ruta entre ellas se marcan como duplicadas. Se conserva una de cada par.

## Las 8 categorías

| Color | Código JSON | Cantidad | Descripción |
|-------|-------------|----------|-------------|
| Verde (#16a34a) | `green` | 570 | Aparece en KML y GTFS, lado derecho de la ruta. Todo correcto. |
| Oliva (#a3a30e) | `green_olive` | 21 | Aparece en KML y GTFS, pero del lado izquierdo. Revisar posición. |
| Amarillo (#eab308) | `yellow` | 2 | Aparece en KML y GTFS, pero fuera de toda ruta. Posible error de ruta. |
| Cian (#06b6d4) | `cyan` | 835 | Solo en KML, lado derecho. **Faltaban en el GTFS y deben agregarse.** |
| Naranja (#f97316) | `orange` | 124 | Solo en KML, lado izquierdo. Posiblemente mal ubicadas. |
| Rojo (#dc2626) | `red` | 33 | Solo en KML, fuera de toda ruta. Posiblemente inválidas. |
| Púrpura (#8b5cf6) | `purple` | 91 | Solo en GTFS. No aparecen en los datos del municipio. |
| Rosa (#ec4899) | `pink` | 74 | Duplicadas (< 20m entre ellas, sin segmento de ruta separándolas). |

## Umbrales de distancia

| Umbral | Uso | Justificación |
|--------|-----|---------------|
| 10m | Deduplicación KML | Mismo paradero registrado en distintas capas |
| 20m | Buffer de ruta / duplicados | Ancho razonable de una calle + acera |
| 50m | Matching KML ↔ GTFS | Tolerancia para imprecisión de GPS y posicionamiento manual |

## Archivos

| Archivo | Tamaño | Contenido |
|---------|--------|-----------|
| `map_data_v4.json` | 3.0 MB | Clasificación completa: 8 categorías con coordenadas, refs y metadata |
| `paradas_faltantes_en_gtfs.csv` | 79 KB | 1,033 paradas KML que no están en el GTFS |
| `paradas_solo_en_gtfs.csv` | 6.4 KB | 105 paradas GTFS que no aparecen en el KML |
| `paradas_osm.csv` | 15 KB | 196 paradas que existían en OSM antes de la importación |
| `analisis_brechas.csv` | 26 KB | Análisis de brechas en terminales de ruta (gap entre último paradero y fin de ruta) |
| `mapa_paraderos.html` | 3.3 MB | Mapa interactivo con todas las categorías, rutas y buffers |

## Mapa interactivo

Abrir `mapa_paraderos.html` en cualquier navegador. El archivo es autocontenido (todos los datos están embebidos como JSON). Incluye:

- Las 8 categorías de paradas con colores distintos
- Geometría de las rutas GTFS
- Zona buffer de 20m con los 428 huecos interiores
- Leyenda interactiva para filtrar categorías
- Click en cualquier parada para ver sus datos
