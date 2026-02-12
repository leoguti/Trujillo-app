# Carga de Paraderos a OpenStreetMap

Proceso de importación de 1,405 paraderos de bus a OpenStreetMap, desde los datos proporcionados por la Gerencia de Transporte Metropolitano de Trujillo.

## Resultado

| Tipo | Cantidad |
|------|----------|
| Paradas nuevas creadas | 1,377 |
| Paradas fusionadas con existentes en OSM | 28 |
| **Total cargadas** | **1,405** |

## Esquema de etiquetado (PTv2)

Cada parada se etiquetó según el estándar [Public Transport Version 2](https://wiki.openstreetmap.org/wiki/Public_transport) de OpenStreetMap:

```
highway=bus_stop
public_transport=platform
bus=yes
network=Transporte Público Urbano Trujillo
ref=<código del municipio>          (ej: PAT-102)
source=Gerencia de Transporte Metropolitano de Trujillo
```

Para las 28 fusiones con paradas existentes, se agregó `source:ref` en vez de `source` para no sobrescribir la fuente original.

## Lógica de conflación

El script `preparar_osm.py` compara cada parada KML con las paradas que ya existían en OSM:

1. Si hay una parada OSM existente a menos de **25m**: se fusiona (se agregan tags sin mover la posición)
2. Si no hay parada cercana: se crea un nodo nuevo

Las 28 fusiones se revisaron manualmente. 4 fusiones con distancia entre 25-35m se incluyeron tras verificación visual.

## Archivos

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `preparar_osm.py` | 21 KB | Script principal que genera el archivo .osm |
| `paradas_trujillo.osm` | 496 KB | Archivo OSM subido via JOSM (1,405 nodos) |
| `reporte_preparacion_osm.csv` | 82 KB | Reporte detallado de cada parada: acción tomada, distancia a OSM existente, categoría |
| `auditoria_osm.md` | 11 KB | Auditoría de calidad del archivo antes de subir |
| `estrategia_import_osm.md` | 15 KB | Documento de estrategia de importación (fuentes, metodología, plan de conflación) |

## Auditoría pre-carga

Antes de subir, se realizó una auditoría exhaustiva (ver `auditoria_osm.md`). Correcciones aplicadas:

1. Tag `name` removido de los 1,377 nodos nuevos (solo queda `ref`)
2. Refs con espacios limpiados (PM-83, PM-82)
3. `network` agregado a todos los nodos
4. `source:ref` usado en las 28 fusiones en vez de `source`

## Verificación

Consulta Overpass para ver todas las paradas cargadas:

```
[out:json][timeout:25];
node["source"="Gerencia de Transporte Metropolitano de Trujillo"](-8.23,-79.13,-7.99,-78.94);
out body;
```

[Abrir en Overpass Turbo](https://overpass-turbo.eu/?Q=node%5B%22source%22%3D%22Gerencia%20de%20Transporte%20Metropolitano%20de%20Trujillo%22%5D%28-8.23%2C-79.13%2C-7.99%2C-78.94%29%3Bout%20body%3B&R)
