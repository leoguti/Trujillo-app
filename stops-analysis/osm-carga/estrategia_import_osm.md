# Importación de Paraderos de Bus de Trujillo a OpenStreetMap

## Estrategia, Fuentes de Datos y Metodología

**Autor:** [Tu nombre / usuario OSM]
**Fecha:** 2026-02-12
**Área:** Trujillo Metropolitano, La Libertad, Perú
**Archivo de importación:** `paradas_trujillo.osm`

---

## 1. Objetivo

Incorporar a OpenStreetMap las paradas de bus (paraderos) del sistema de transporte público urbano de Trujillo, a partir de datos oficiales proporcionados por la **Gerencia de Transporte Metropolitano de Trujillo**.

El resultado: **1,377 paradas nuevas** y **28 fusiones** con paradas ya existentes en OSM.

---

## 2. Fuentes de Datos

### 2.1 Datos del municipio (fuente primaria)

- **Formato:** Archivo KMZ con 6 capas de puntos
- **Proveedor:** Gerencia de Transporte Metropolitano de Trujillo
- **Contenido:** 1,858 registros de paraderos con código de referencia (ej: PAT-102, PM-121), coordenadas, capa de origen, nombre del elaborador y supervisor
- **Capas:**

| Capa | Registros |
|------|-----------|
| Consolidado | 976 |
| Puntos_Paraderos | 546 |
| Moche | 128 |
| LAREDO | 109 |
| DATA SET Victor Larco | 54 |
| Paraderos_Salaverry | 45 |

### 2.2 GTFS (fuente secundaria)

- **Formato:** GTFS (General Transit Feed Specification)
- **Contenido:** 605 paradas y 210 shapes (trazados de ruta) del sistema de transporte
- **Uso:** Validación cruzada de paradas KML y geometría de rutas para análisis espacial

### 2.3 OpenStreetMap (datos existentes)

- **Consulta:** Overpass API con `out meta` (para obtener versiones de nodos)
- **Resultado:** 195 paradas existentes en el área
  - 101 `public_transport=platform`
  - 64 `amenity=bus_station` (probablemente mal etiquetadas)
  - 29 `public_transport=stop_position`
  - 2 `highway=bus_stop` (solo PTv1)

---

## 3. Pipeline de Procesamiento

### 3.1 Extracción y parseo del KML

```
KMZ del municipio
  → Descomprimir → doc.kml
  → Parsear con xml.etree.ElementTree
  → Extraer Placemarks con geometría Point
  → 1,858 registros brutos
```

**Nota técnica:** El KMZ tenía `xsi:schemaLocation` sin declarar `xmlns:xsi`. Se inyectó la declaración de namespace antes del parseo.

### 3.2 Deduplicación entre capas

Las 6 capas del KML tenían solapamientos (misma parada en múltiples capas). Se deduplicó por proximidad:

- **Umbral:** 10 metros (haversine)
- **Resultado:** 1,858 → **1,645 paradas únicas**

### 3.3 Clasificación en 8 categorías

Cada parada se clasificó según tres criterios:
1. Si tiene match con una parada GTFS (distancia < 50m)
2. Si está dentro del buffer de 20m alrededor de alguna ruta
3. Si está del lado correcto de la calle (derecha, tránsito por la derecha en Perú)

#### Análisis espacial

- **Proyección:** WGS84 → UTM zona 17S (EPSG:32717) para operaciones métricas
- **Buffer de ruta:** 20m alrededor de cada shape GTFS, unión con `unary_union`, simplificación con tolerancia 2m
- **Lado de calle:** Producto cruzado del vector de dirección de ruta con el vector al punto. En UTM (x=este, y=norte): `cross < 0` = derecha (válido), `cross > 0` = izquierda (inválido)

#### Detección de duplicadas

Para cada par de paradas a menos de 20m, se verificó si hay un segmento de ruta entre ellas (signos opuestos del producto cruzado). Si no hay ruta entre ellas → duplicadas (mismo lado de la calle, muy cerca).

#### Resultado: 8 categorías

| Categoría | Cantidad | Criterio | Decisión |
|-----------|----------|----------|----------|
| **green** | 570 | KML + GTFS + lado derecho | Subir a OSM |
| green_olive | 21 | KML + GTFS + lado izquierdo | No subir (revisar) |
| yellow | 2 | KML + GTFS + fuera de ruta | No subir |
| **cyan** | 835 | Solo KML + lado derecho | Subir a OSM |
| orange | 124 | Solo KML + lado izquierdo | No subir (lado equivocado) |
| red | 33 | Solo KML + fuera de ruta | No subir (inválida) |
| purple | 91 | Solo en GTFS | No subir (no viene del municipio) |
| pink | 74 | Duplicada (< 20m sin ruta entre ellas) | No subir |

**Paradas seleccionadas para OSM: 570 (green) + 835 (cyan) = 1,405**

### 3.4 Conflación con paradas OSM existentes

Para cada una de las 1,405 paradas KML seleccionadas, se buscaron paradas OSM existentes cercanas para decidir si crear una nueva o fusionar.

#### Algoritmo de conflación

```
Para cada parada KML:
  1. Buscar paradas OSM a < 30m (índice espacial cKDTree sobre coordenadas UTM)
  2. Excluir bus_station (terminales) y stop_position del merge
     → Solo merge con platform o bus_stop
  3. Para cada candidato, verificar con producto cruzado que estén del mismo
     lado de la calle
     → Si están en lados opuestos → rechazar y probar siguiente candidato
  4. El candidato más cercano del mismo lado → merge
  5. Si no hay candidatos válidos → crear nueva

Resolución de conflictos:
  Si 2+ paradas KML quieren merge con 1 misma parada OSM
  → la más cercana gana, las demás se crean como nuevas
```

#### Resultado de la conflación

| Acción | Cantidad | Detalle |
|--------|----------|---------|
| Crear nueva | 1,377 | Sin match OSM cercano |
| Fusionar | 28 | Match con parada OSM existente (mismo lado, < 30m) |
| Rechazos por lado opuesto | 6 | Candidato OSM a < 30m pero en lado contrario de la calle |
| Conflictos resueltos | 0 | Ningún caso de 2 KML compitiendo por 1 OSM |

---

## 4. Esquema de Etiquetado (Tagging)

### 4.1 Paradas nuevas (1,377 nodos)

```xml
<node id="-1" lat="-8.0639341" lon="-79.0188810" visible="true">
  <tag k="public_transport" v="platform"/>
  <tag k="bus"              v="yes"/>
  <tag k="highway"          v="bus_stop"/>
  <tag k="network"          v="Transporte Público Urbano Trujillo"/>
  <tag k="source"           v="Gerencia de Transporte Metropolitano de Trujillo"/>
  <tag k="ref"              v="PAT-102"/>
</node>
```

| Tag | Valor | Justificación |
|-----|-------|---------------|
| `public_transport` | `platform` | PTv2: plataforma donde espera el pasajero |
| `bus` | `yes` | Tipo de transporte |
| `highway` | `bus_stop` | Compatibilidad con PTv1 |
| `network` | `Transporte Público Urbano Trujillo` | Red de transporte (consistente con relaciones existentes) |
| `source` | `Gerencia de Transporte Metropolitano de Trujillo` | Origen de los datos |
| `ref` | *(código municipal)* | Código asignado por el municipio (ej: PAT-102, PM-121) |

**Nota:** No se incluye tag `name` porque los datos del municipio solo contienen códigos de referencia, no nombres descriptivos de las paradas. En OSM, `name` debe ser un nombre legible para humanos (ej: "Av. España / Jr. Pizarro"), no un código. El tag `ref` es el apropiado para códigos de referencia.

### 4.2 Paradas fusionadas (28 nodos)

Para las fusiones, se aplicó la siguiente política:

| Aspecto | Política |
|---------|----------|
| Posición geográfica | Se conserva la de OSM (no se mueve el nodo) |
| Tags existentes de OSM | Se conservan todos intactos |
| Tags nuevos (platform, bus, highway, network) | Se agregan solo si no existían |
| `ref` | Se agrega/sobreescribe con el código del municipio |
| `source:ref` | Se agrega como "Gerencia de Transporte..." (no `source`, para no atribuir la geometría al municipio) |
| `name` | Se conserva el nombre original de OSM |

#### Ejemplo de nodo fusionado

```xml
<node id="5082686253" lat="-8.0931170" lon="-79.0119150" version="8" action="modify">
  <!-- Tags originales de OSM preservados -->
  <tag k="name"             v="Panamericana Norte"/>
  <tag k="shelter"          v="yes"/>
  <tag k="bench"            v="yes"/>
  <tag k="lit"              v="no"/>
  <tag k="source"           v="Reconocimiento terrestre cartográfico realizado por Kaart en 2017"/>
  <!-- ... más tags originales ... -->

  <!-- Tags agregados por la fusión -->
  <tag k="public_transport" v="platform"/>
  <tag k="bus"              v="yes"/>
  <tag k="highway"          v="bus_stop"/>
  <tag k="network"          v="Transporte Público Urbano Trujillo"/>
  <tag k="ref"              v="PM-121"/>
  <tag k="source:ref"       v="Gerencia de Transporte Metropolitano de Trujillo"/>
</node>
```

### 4.3 Listado completo de las 28 fusiones

| Código municipal | OSM ID | Nombre en OSM | Distancia | Categoría |
|-----------------|--------|---------------|-----------|-----------|
| PM-121 | 5082686253 | Panamericana Norte | 27.5m | green |
| PM-59 | 8743805428 | Avenida Perú | 6.3m | green |
| PM-60 | 12121155299 | Avenida de La Marina | 27.7m | green |
| AMEO-74 | 11910645397 | Calle 26 | 12.0m | green |
| AMN-20 | 11910518849 | Avenida del Ejército | 22.3m | green |
| AMS-47 | 5067622117 | Avenida Victor Larco Herrera | 12.3m | green |
| AMS-49 | 11910359975 | Prolongación Cesar Vallejo | 8.4m | green |
| AMS-50 | 11910359976 | Calle Australia | 5.8m | green |
| AMS-52 | 11910518853 | Calle Calcuchimac | 2.6m | green |
| ESP-10 | 5099494790 | Avenida Perú | 0.8m | green |
| ESP-12 | 4937067022 | Avenida Del Ejército | 18.9m | green |
| ESP-13 | 11895968651 | Avenida del Ejército | 3.8m | green |
| ESP-14 | 11895957225 | Calle Agricultura | 10.9m | green |
| ESP-15 | 11895957224 | Jirón Estete | 9.2m | green |
| ESP-5 | 5099440457 | Jirón Independencia | 12.3m | green |
| ROM-369 | 11910518834 | Calle Salaverry | 18.8m | green |
| ROM-370 | 11910518835 | Calle Santiago de Chile | 6.9m | green |
| PH-111 | 11911534030 | Calle Alfonso Ugarte | 11.9m | cyan |
| PH-13 | 12121155280 | Avenida la Rivera | 23.4m | cyan |
| PM-7 | 12121157801 | Jirón José Galvez | 27.9m | cyan |
| PS-52 | 12121157807 | Avenida de La Marina | 8.8m | cyan |
| AMS-36 | 5069523013 | *(sin nombre)* | 27.7m | cyan |
| EJER-410 | 12121155277 | Avenida del Ejército | 15.7m | cyan |
| ESP-11 | 11895953681 | Avenida Perú | 14.4m | cyan |
| ESP-9 | 5099494791 | Jirón Unión | 18.2m | cyan |
| JPT-138 | 11910518831 | Avenida Jesús de Nazareth | 18.4m | cyan |
| NPT-198 | 11896286019 | Avenida Teodoro Valcárcel | 23.4m | cyan |
| VLHT-98 | 11910359970 | Avenida los Colibries | 11.2m | cyan |

---

## 5. Umbrales de Distancia Utilizados

| Umbral | Uso | Justificación |
|--------|-----|---------------|
| 10 m | Deduplicación KML entre capas | Dos registros a < 10m en capas distintas son la misma parada |
| 20 m | Buffer de ruta / detección de duplicadas | Distancia máxima razonable entre una parada y la línea central de la vía |
| 30 m | Conflación KML ↔ OSM | Más conservador que KML↔GTFS. Evita fusiones incorrectas con paradas lejanas |
| 50 m | Match KML ↔ GTFS | Umbral estándar para identificar la misma parada física en dos datasets |

---

## 6. Herramientas y Dependencias

| Herramienta | Versión | Uso |
|-------------|---------|-----|
| Python | 3.12 | Pipeline de procesamiento completo |
| Shapely | 2.1.2 | Buffer zones, unión de geometrías, simplificación |
| PyProj | 3.6.1 | Transformación WGS84 ↔ UTM 17S |
| SciPy | — | `cKDTree` para búsqueda espacial eficiente |
| NumPy | — | Arrays de coordenadas para cKDTree |
| lxml | — | Generación de XML .osm con `pretty_print` |
| Overpass API | — | Consulta de paradas OSM existentes (`out meta`) |

**Scripts:**
- `preparar_osm.py` — Pipeline completo: carga datos → consulta Overpass → conflación → genera .osm y .csv

---

## 7. Coordenadas y Proyección

- **Sistema de referencia:** WGS84 (EPSG:4326) para coordenadas geográficas
- **Proyección de trabajo:** UTM zona 17S (EPSG:32717) para todas las operaciones métricas
- **Transformación:** PyProj con `always_xy=True` para mantener orden (lon, lat) → (x, y)
- **Área cubierta:**

| | Latitud | Longitud |
|-|---------|----------|
| Mínimo | -8.2230 | -79.1230 |
| Máximo | -7.9929 | -78.9482 |

Cubre: Trujillo centro, La Esperanza, El Porvenir, Florencia de Mora, Victor Larco, Huanchaco, Laredo, Moche y Salaverry.

---

## 8. Control de Calidad

### 8.1 Validaciones automáticas realizadas

| Validación | Resultado |
|------------|-----------|
| XML bien formado | PASS |
| Todos los IDs únicos | PASS |
| Todas las coordenadas dentro del área de Trujillo | PASS |
| Cero coordenadas duplicadas | PASS |
| Cero pares de nodos a < 5m | PASS |
| PTv2 compliance (platform + bus_stop + bus=yes) en todos los nodos | PASS |
| Todos los nodos tienen `ref` | PASS |
| Todos los nodos tienen `network` | PASS |
| Tags de merge preservan originales | PASS |
| Refs con espacios limpiados | PASS (2 corregidos) |

### 8.2 Problemas conocidos

| Problema | Nodos afectados | Estado |
|----------|----------------|--------|
| 11 refs duplicados (mismo código, paradas distintas) | 22 | Reportado al municipio, pendiente respuesta |
| 2 nodos con ref "PL-Existente" (placeholder) | 2 | Incluido en reporte al municipio |

### 8.3 Revisión manual pendiente

- 4 fusiones a > 25m deben verificarse en JOSM con imágenes satelitales
- Validador de JOSM debe ejecutarse antes de la subida

---

## 9. Plan de Subida

### 9.1 Método
- **Herramienta:** JOSM
- **Archivo:** `paradas_trujillo.osm`
- **Cuenta:** [tu usuario OSM]

### 9.2 Changeset tags

```
comment=Add 1,377 bus stop platforms and enrich 28 existing stops in Trujillo, Peru from municipal data
source=Gerencia de Transporte Metropolitano de Trujillo
source:url=[URL si existe]
import=yes
```

### 9.3 Pasos posteriores (no parte del import)

1. Cuando el municipio responda sobre los 11 refs duplicados, actualizar los `ref` correspondientes
2. Agregar las paradas a las relaciones de ruta existentes (214 relaciones), ruta por ruta, verificando orden y estructura PTv2

---

## 10. Licencia y Permisos

- **Fuente:** Gerencia de Transporte Metropolitano de Trujillo
- **Tipo de datos:** Ubicación de paraderos de transporte público (datos gubernamentales)
- **Compatibilidad ODbL:** [Pendiente confirmar con la Gerencia]
- **Contacto:** [Información de contacto]

---

## 11. Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `paradas_trujillo.osm` | Archivo para JOSM (1,377 nuevos + 28 merges) |
| `reporte_preparacion_osm.csv` | Detalle de cada acción (1,405 filas) |
| `preparar_osm.py` | Script de preparación (código fuente) |
| `map_data_v4.json` | Clasificación de 8 categorías (datos intermedios) |
| `auditoria_osm.md` | Auditoría exhaustiva del archivo .osm |
| `reporte_codigos_duplicados.md` | Reporte para el municipio sobre refs duplicados |
| `mapa_paraderos.html` | Mapa interactivo Leaflet con todas las capas |
