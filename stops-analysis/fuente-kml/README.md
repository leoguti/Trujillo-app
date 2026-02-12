# Fuente KML — Datos del Municipio

Datos originales de paraderos proporcionados por la **Gerencia de Transporte Metropolitano de Trujillo**.

## Archivos

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `Rutas y paraderos Trujillo. (1).kmz` | 1.1 MB | Archivo original del municipio (KMZ con 6 capas) |
| `paradas_kml_completas.csv` | 139 KB | 1,858 paradas extraídas del KMZ |

## Capas del KMZ

El archivo KMZ contiene 6 capas de puntos, con solapamiento parcial entre ellas:

| Capa | Registros |
|------|-----------|
| Consolidado | 976 |
| Puntos_Paraderos | 546 |
| Moche | 128 |
| LAREDO | 109 |
| DATA SET Victor Larco | 54 |
| Paraderos_Salaverry | 45 |
| **Total** | **1,858** |

Después de deduplicar registros que aparecen en múltiples capas (umbral: 10m), quedan **1,645 paradas únicas**.

## Columnas del CSV

| Columna | Descripción |
|---------|-------------|
| `nombre` | Código de referencia del paradero (ej: PAT-102, PM-121, PE-237) |
| `lat` | Latitud (WGS84) |
| `lon` | Longitud (WGS84) |
| `capa` | Capa de origen dentro del KMZ |
| `fid` | ID interno del feature en el KML |
| `elaborado` | Nombre del elaborador (no siempre presente) |
| `supervisor` | Nombre del supervisor (no siempre presente) |

## Prefijos de códigos

- `PAT-` — Paraderos de la zona centro/consolidada
- `PM-` — Paraderos de Moche
- `PE-` — Paraderos existentes (nomenclatura alternativa)
- `PL-` — Paraderos de Laredo
- `PVL-` — Paraderos de Victor Larco
- `PS-` — Paraderos de Salaverry

## Nota técnica

El KMZ tiene `xsi:schemaLocation` sin declarar `xmlns:xsi`, lo que causa error en `xml.etree.ElementTree`. Para parsearlo correctamente, hay que inyectar `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` en el elemento raíz antes de parsear.
