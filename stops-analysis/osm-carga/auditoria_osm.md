# Auditoría Exhaustiva: paradas_trujillo.osm

**Fecha:** 2026-02-12
**Archivo auditado:** `paradas_trujillo.osm` (468 KB)
**Reporte auxiliar:** `reporte_preparacion_osm.csv` (83 KB)
**Propósito:** Verificar que los datos están listos para subir a OpenStreetMap

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| XML válido | PASS |
| Nodos totales | 1,405 (1,377 nuevos + 28 merges) |
| IDs únicos | PASS |
| Coordenadas en rango | PASS (4 outliers legítimos en Huanchaco) |
| Coordenadas duplicadas | PASS (ninguna) |
| Nodos muy cercanos (<5m) | PASS (ninguno) |
| PTv2 compliance | PASS |
| **Tag `name` con códigos** | **CRITICO — corregir** |
| **Refs duplicados** | **CRITICO — 11 duplicados** |
| **Refs con espacios/placeholders** | **CORREGIR — 4 nodos** |
| **Tag `network` faltante** | **MAYOR — agregar** |
| **Source en merges** | **MENOR — revisar** |
| 4 merges >25m | REVISAR manualmente |

---

## 1. Validez XML y Estructura

- XML bien formado, parsea sin errores
- Elemento raíz: `<osm version="0.6" generator="paraderos_trujillo">`
- **1,377 nodos nuevos** (IDs -1 a -1377, secuenciales sin huecos)
- **28 nodos modificados** (IDs positivos reales, todos con `action="modify"` y `version`)
- **0 ways** (todos los merges fueron con nodos, no ways)
- Todos los IDs son únicos

---

## 2. PTv2 Compliance — PASS

Los 1,405 nodos tienen el triplete correcto:
- `public_transport=platform`
- `highway=bus_stop`
- `bus=yes`

No se encontraron tags deprecados (`amenity=bus_station`, etc.).

---

## 3. CRITICO: Tag `name` contiene códigos, no nombres reales

### Problema
Los **1,377 nodos nuevos** tienen `name == ref` (el código municipal como nombre):
```xml
<tag k="name" v="PAT-102"/>
<tag k="ref" v="PAT-102"/>
```

En OSM, `name` debe ser el nombre legible para humanos (ej: "Av. España / Jr. Pizarro"), **no** un código de referencia. Si no se conoce el nombre real, `name` debe omitirse.

### Impacto
- Los stops aparecerán en el mapa como "PAT-102" en vez de un nombre útil
- Viola las convenciones de etiquetado de OSM
- Podría generar rechazo de la comunidad OSM

### Solución
En `preparar_osm.py`, función `generate_osm_xml`, cambiar:
```python
# ACTUAL (incorrecto):
if kml["nombre"]:
    etree.SubElement(node, "tag", k="name", v=kml["nombre"])
    etree.SubElement(node, "tag", k="ref", v=kml["nombre"])

# CORREGIDO:
if kml["nombre"]:
    etree.SubElement(node, "tag", k="ref", v=kml["nombre"])
    # NO poner el código como name — omitir name si no hay nombre real
```

### Nodos merge afectados
- 27 de 28 merges conservan correctamente su nombre original de OSM (ej: "Avenida Peru", "Jiron Independencia")
- **1 merge problemático**: nodo `5069523013` tiene `name="AMS-36"` (código como nombre). Probablemente ya estaba así en OSM.

---

## 4. CRITICO: 11 Refs Duplicados

### 9 duplicados PE-* (diferentes paradas, mismo código)

| Ref | Nodo A | Nodo B | Distancia entre ellos |
|-----|--------|--------|----------------------|
| PE-237 | -62 (Consolidado) | -507 (Puntos_Paraderos) | 7,409m |
| PE-238 | -63 | -508 | 5,211m |
| PE-239 | -64 | -509 | 5,083m |
| PE-240 | -65 | -1314 | 4,875m |
| PE-241 | -510 | -716 | 5,102m |
| PE-242 | -66 | -511 | 4,556m |
| PE-243 | -67 | -512 | 4,324m |
| PE-244 | -717 | -1315 | 4,123m |
| PE-247 | -513 | -718 | 4,447m |

**Causa**: Colisión de numeración entre capas KML (Consolidado vs Puntos_Paraderos). Son paradas genuinamente diferentes a kilómetros de distancia con el mismo código asignado por el municipio.

### 1 duplicado PL-53
- Nodos -254 y -1045, ambos en capa LAREDO, **287m de distancia**. Paradas diferentes con mismo código.

### 1 duplicado PL-Existente
- Nodos -282 y -283, ambos en capa LAREDO, **32m de distancia**. "Existente" parece ser un nombre placeholder (no es código real). Revisar si deben eliminarse o renombrarse.

### Solución
- Desambiguar agregando sufijo (ej: PE-237a / PE-237b)
- O consultar al municipio por los códigos correctos
- Los `PL-Existente` deben ser eliminados o recibir códigos reales

---

## 5. CORREGIR: Refs con espacios y placeholders

| Nodo | Ref actual | Corrección |
|------|-----------|------------|
| -284 | `PM-  83` (doble espacio) | `PM-83` |
| -285 | `PM- 82` (espacio simple) | `PM-82` |
| -282 | `PL-Existente` (placeholder) | Eliminar o asignar código |
| -283 | `PL-Existente` (placeholder) | Eliminar o asignar código |

### Refs no estándar (aceptables si son intencionales)
- `PM-SC3`, `PM-SC4`, `PM-SC6` — posiblemente "Sin Clasificar"
- `PVL-SC3`, `PVL-SC-HUAMAN` — posiblemente auxiliares

---

## 6. MAYOR: Tag `network` faltante

Ninguno de los 1,405 nodos tiene `network`. Según las rutas OSM existentes en Trujillo, la red es `"Transporte Público Urbano Trujillo"`. Agregar este tag vincularía las paradas con la red de transporte.

**Solución**: Agregar a `NEW_STOP_TAGS` en `preparar_osm.py`:
```python
"network": "Transporte Público Urbano Trujillo",
```

**Nota**: `operator` no se agrega porque cada parada puede ser servida por múltiples operadores.

---

## 7. MENOR: Source tag en nodos merge

- 22 de 28 merges recibieron `source="Gerencia de Transporte Metropolitano de Trujillo"`
- 6 conservaron su source original (Kaart Ground Survey, etc.)

El comportamiento es correcto (`setdefault` no sobreescribe). Sin embargo, para los 22 que no tenían source, atribuir la geometría al municipio es impreciso — solo el `ref` viene del municipio.

**Solución sugerida**: Para merges, usar `source:ref` en vez de `source`:
```python
# En merges:
merged_tags.setdefault("source:ref", "Gerencia de Transporte Metropolitano de Trujillo")
# En vez de:
merged_tags.setdefault("source", "Gerencia de Transporte Metropolitano de Trujillo")
```

---

## 8. Análisis de Merges (28 fusiones)

### Distribución por distancia
| Rango | Cantidad | Confianza |
|-------|----------|-----------|
| 0-10m | 9 | Muy alta |
| 10-15m | 7 | Alta |
| 15-20m | 5 | Razonable |
| 20-25m | 3 | Borderline |
| **>25m** | **4** | **Revisar** |

**Min**: 0.8m, **Max**: 27.9m, **Media**: 14.6m, **Mediana**: 12.3m

### 4 merges a revisar manualmente (>25m)

| KML | OSM ID | Distancia | Nombre OSM |
|-----|--------|-----------|------------|
| PM-7 | 12121157801 | 27.9m | Jirón José Galvez |
| PM-60 | 12121155299 | 27.7m | Avenida de La Marina |
| AMS-36 | 5069523013 | 27.7m | *(sin nombre)* |
| PM-121 | 5082686253 | 27.5m | Panamericana Norte |

### 6 rechazos correctos por lado opuesto
El algoritmo rechazó correctamente 6 candidatos OSM que estaban al lado opuesto de la calle:

| KML | OSM rechazado | Distancia | Acción |
|-----|--------------|-----------|--------|
| PM-20 | 12121157804 | 8.2m | Creado como nuevo |
| PM-24 | 12121157805 | 24.4m | Creado como nuevo |
| AMS-46 | 5067622117 | 27.0m | Creado como nuevo (AMS-47 sí se fusionó con este OSM) |
| MAVE-353 | 11896286020 | 29.2m | Creado como nuevo |
| NPT-200 | 11910518838 | 28.8m | Creado como nuevo |
| NPT-207 | 4649094889 | 21.8m | Creado como nuevo |

---

## 9. Coordenadas — PASS

| Métrica | Latitud | Longitud |
|---------|---------|----------|
| Mínimo | -8.2229612 | -79.1230144 |
| Máximo | -7.9929158 | -78.9482263 |
| Spread | 0.230° (~25.5 km) | 0.175° (~19.4 km) |

Todas las 1,405 paradas están dentro del área metropolitana de Trujillo.

### 4 outliers legítimos (norte de lat -8.0)
| Nodo | Ref | Lat | Lon | Nota |
|------|-----|-----|-----|------|
| -118 | PH-102 | -7.9929843 | -79.0747991 | Ruta a Huanchaco, 781m norte de -8.0 |
| -133 | PH-136 | -7.9929158 | -79.0745783 | Ruta a Huanchaco, 789m norte de -8.0 |
| -119 | PH-103 | -7.9975336 | -79.0733612 | Ruta a Huanchaco, 275m norte de -8.0 |
| -134 | PH-137 | -7.9976500 | -79.0730719 | Ruta a Huanchaco, 262m norte de -8.0 |

Son paradas legítimas en el extremo norte de la ruta a Huanchaco (prefijo PH).

---

## 10. Distribución por Prefijo de Ref

| Prefijo | Cantidad | Zona/Ruta probable |
|---------|----------|-------------------|
| PE | 266 | Panamericana Express |
| PH | 129 | Huanchaco |
| PP | 110 | — |
| PAT | 102 | — |
| PM | 94 | Panamericana Main |
| PL | 84 | Laredo |
| PFM | 64 | — |
| PVL | 39 | Victor Larco |
| PS | 34 | Salaverry |
| AMS | 24 | — |

96 prefijos distintos en total.

---

## 11. Distribución por Capa KML y Categoría

### Por capa
| Capa | Cantidad |
|------|----------|
| Consolidado | 663 |
| Puntos_Paraderos | 473 |
| Moche | 104 |
| LAREDO | 85 |
| DATA SET Victor Larco | 44 |
| Paraderos_Salaverry | 35 |
| LAREDO + Puntos_Paraderos | 1 |

### Cruce acción × categoría
| | cyan | green | TOTAL |
|------|------|-------|-------|
| merge | 11 | 17 | **28** |
| new | 824 | 553 | **1,377** |
| TOTAL | **835** | **570** | **1,405** |

---

## 12. Tags en Nodos Merge (preservación verificada)

Los 28 merges preservan correctamente todos sus tags originales:
- `shelter` (18 yes, 10 no)
- `bench`, `lit`, `advertising`, `pole`
- `tactile_writing:braille:es`, `passenger_information_display:speech_output` (accesibilidad)
- `check_date:shelter` (fecha de survey)
- `name:de`, `name:en` (nombres multilingüe en nodo 4937067022: "Bus B nach Chan Chan und Huanchaco")

Ningún tag existente fue eliminado o sobreescrito.

---

## Plan de Acción (priorizado)

### Antes de subir (obligatorio)
1. **Quitar `name` de nodos nuevos** — Solo dejar `ref` con el código municipal
2. **Desambiguar 11 refs duplicados** — PE-237 a PE-247, PL-53, PL-Existente
3. **Limpiar refs con espacios** — PM-82 y PM-83 (quitar espacios)
4. **Decidir sobre PL-Existente** — Eliminar o asignar código real

### Recomendado
5. **Agregar `network`** = "Transporte Público Urbano Trujillo" a todos los nodos
6. **Revisar 4 merges >25m** en JOSM con imágenes satelitales
7. **Usar `source:ref`** en vez de `source` para merges

### Opcional
8. Agregar `operator` si se conoce por parada
9. El nodo merge 5069523013 tiene `name="AMS-36"` (código) — considerar corregir en OSM

---

## Notas sobre el Proceso de Subida

- **Subir por lotes**: 1,377 nodos es una carga grande. Considerar dividir por zona geográfica o por capa.
- **Changeset tags**: Usar `comment` descriptivo, `source`, y `import=yes` si aplica.
- **Revisar en JOSM**: Abrir `paradas_trujillo.osm` en JOSM, activar validador, revisar warnings antes de subir.
- **Comunicar a la comunidad**: Para imports grandes, es buena práctica avisar en la lista de correo de OSM Perú.
