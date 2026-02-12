# Asignación de Paraderos a Rutas en OpenStreetMap

Proceso de asignación de paraderos a las 214 relaciones de ruta de bus del sistema de transporte público de Trujillo en OpenStreetMap.

## ¿Qué es una relación de ruta?

Una relación de ruta en OpenStreetMap es como una lista que le dice a las aplicaciones de transporte:

> *"El bus C-10 recorre estas calles y para en estos 47 paraderos, en este orden."*

Sin esta información, las aplicaciones saben que la ruta C-10 existe y por dónde pasa, pero **no saben en qué paraderos se detiene**. Las 214 relaciones de ruta de Trujillo ya tenían la geometría del recorrido, pero les faltaban las paradas.

## ¿Por qué es necesario?

Aplicaciones como OTP (OpenTripPlanner), Trufi, Organic Maps y cualquier sistema basado en GTFS generado desde OSM necesitan saber qué paradas pertenecen a qué ruta. Sin esta asignación:
- No se pueden calcular rutas de transporte público
- No se puede mostrar "las siguientes paradas del bus"
- No se puede generar un GTFS completo

## Resultados

| Métrica | Valor |
|---------|-------|
| Asignaciones paradero → ruta | 10,017 |
| Paraderos únicos asignados | 1,368 (de 1,405 totales) |
| Rutas con al menos un paradero | 214 |
| Promedio de paraderos por ruta | 47 |

Los 37 paraderos no asignados están a más de 20m de cualquier ruta, probablemente en zonas donde la geometría de la ruta no es precisa.

## Algoritmo de asignación

Para cada ruta, el script:

1. **Camina la geometría** segmento a segmento (cada tramo entre dos puntos consecutivos)
2. **Busca paraderos** a menos de 20m de cada segmento
3. **Verifica el lado**: solo asigna paradas del **lado derecho** de la vía (producto cruz < 0 en UTM 17S)
4. **Ordena las paradas** en el orden natural del recorrido
5. **Filtra**: solo paradas con `source=Gerencia de Transporte Metropolitano de Trujillo` y `ref` (paradas municipales)

## Archivos

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `fetch_rutas_osm.py` | 4.2 KB | Script que descarga las 214 rutas de OSM vía Overpass API |
| `rutas_osm.csv` | 37 KB | Listado de las 214 rutas con: ID de relación, ref, nombre, operador, color |
| `our_stops_osm_ids.json` | 405 KB | Mapeo de nuestros paraderos a sus IDs reales en OSM (tras la subida) |
| `relaciones_con_paradas.osm` | 4.8 MB | Archivo OSM con las 214 relaciones modificadas, listo para subir via JOSM |

## Cómo verificar en OpenStreetMap

Para ver los paraderos asignados a una ruta específica (ejemplo: C-10):

1. Ir a [openstreetmap.org](https://www.openstreetmap.org)
2. Buscar la relación por ID (ej: [relación 19967562](https://www.openstreetmap.org/relation/19967562))
3. En la pestaña "Miembros" se ven las paradas con rol `platform`

O usar esta consulta Overpass para ver todas las rutas con sus paradas:

```
[out:json][timeout:60];
relation["network"="Transporte Público Urbano Trujillo"]["type"="route"]["route"="bus"](-8.23,-79.13,-7.99,-78.94);
out body;
>;
out skel qt;
```

## Estado de la carga

- **Piloto completado**: Ruta C-10 M ida (relación 19967562) — 22 paradas asignadas y subidas a OSM
- **213 rutas restantes**: archivo `relaciones_con_paradas.osm` pendiente de subir via JOSM
