# Análisis y Carga de Paraderos de Trujillo

Análisis espacial de los paraderos de transporte público de Trujillo, comparando tres fuentes de datos, y carga de los resultados a OpenStreetMap.

## Contexto

La Gerencia de Transporte Metropolitano de Trujillo proporcionó un archivo KMZ con 1,858 registros de paraderos. Al compararlo con nuestro feed GTFS (605 paradas) y los datos existentes en OpenStreetMap (196 paradas), se identificaron **835 paradas faltantes** en el GTFS que estaban correctamente posicionadas.

## Pipeline de datos

```
KMZ del municipio (1,858 registros)
        │
        ▼
Extracción y deduplicación → 1,645 únicas
        │
        ├── Comparación con GTFS (605 paradas, umbral 50m)
        ├── Comparación con OSM (196 paradas)
        └── Validación espacial:
            ├── Buffer de 20m alrededor de cada ruta
            ├── Detección lado derecho (producto cruz en UTM 17S)
            └── Detección de duplicados (<20m sin segmento entre ellos)
        │
        ▼
Clasificación en 8 categorías → mapa interactivo
        │
        ▼
Carga a OpenStreetMap → 1,405 paradas
        │
        ▼
Asignación a relaciones de ruta → 10,017 asignaciones en 214 rutas
```

## Clasificación de paraderos (8 categorías)

| Color | Código | Cantidad | Significado |
|-------|--------|----------|-------------|
| 🟢 Verde | `green` | 570 | KML + GTFS + lado derecho de la ruta (correcto) |
| 🫒 Oliva | `green_olive` | 21 | KML + GTFS + lado izquierdo (revisar) |
| 🟡 Amarillo | `yellow` | 2 | KML + GTFS + fuera de toda ruta |
| 🔵 Cian | `cyan` | 835 | Solo KML + lado derecho (faltaban en GTFS) |
| 🟠 Naranja | `orange` | 124 | Solo KML + lado izquierdo (lado incorrecto) |
| 🔴 Rojo | `red` | 33 | Solo KML + fuera de toda ruta (inválidas) |
| 🟣 Púrpura | `purple` | 91 | Solo en GTFS (no aparecen en datos del municipio) |
| 🩷 Rosa | `pink` | 74 | Duplicadas (< 20m, sin segmento de ruta entre ellas) |

## Resultados principales

- **1,405 paradas** cargadas a OpenStreetMap (1,377 nuevas + 28 fusionadas con existentes)
- **10,017 asignaciones** paradero → ruta
- **1,368 paraderos** únicos asignados a al menos una ruta
- **214 rutas** con paraderos asignados (promedio: 47 paraderos por ruta)

## Relaciones de ruta en OpenStreetMap

Una "relación de ruta" es una estructura en OpenStreetMap que dice: *"el bus C-10 recorre estas calles y para en estos paraderos, en este orden"*. Sin esta información, las aplicaciones de navegación y transporte no pueden mostrar qué buses paran en qué paraderos.

Las 214 relaciones de ruta del sistema de transporte de Trujillo ya existían en OSM con la geometría del recorrido, pero no tenían las paradas asignadas. Este proyecto asignó las paradas a cada ruta.

## Estructura del directorio

```
stops-analysis/
├── fuente-kml/      ← Datos originales del municipio (KMZ + CSV extraído)
├── analisis/        ← Resultados del análisis espacial y mapa interactivo
├── osm-carga/       ← Scripts y archivos de la carga a OpenStreetMap
├── osm-rutas/       ← Asignación de paradas a relaciones de ruta
└── reportes/        ← Informes para el municipio y reportes de calidad
```

Cada subcarpeta tiene su propio README con documentación detallada.

## Verificación en OpenStreetMap

Para ver todas las paradas cargadas, abrir esta consulta en Overpass Turbo:

```
[out:json][timeout:25];
node["source"="Gerencia de Transporte Metropolitano de Trujillo"](-8.23,-79.13,-7.99,-78.94);
out body;
```

[Abrir en Overpass Turbo](https://overpass-turbo.eu/?Q=node%5B%22source%22%3D%22Gerencia%20de%20Transporte%20Metropolitano%20de%20Trujillo%22%5D%28-8.23%2C-79.13%2C-7.99%2C-78.94%29%3Bout%20body%3B&R)

## Dependencias técnicas

- Python 3.12, Shapely 2.1.2, PyProj 3.6.1
- Sistema de coordenadas: WGS84 (EPSG:4326) para almacenamiento, UTM 17S (EPSG:32717) para operaciones métricas
- Mapa interactivo: Leaflet 1.9.4 (autocontenido en el HTML)
