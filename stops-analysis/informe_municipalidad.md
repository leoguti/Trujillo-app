# Informe: Estado de Paraderos de Transporte Público de Trujillo

**Para:** Gerencia de Transporte Metropolitano de Trujillo
**De:** Leonardo Gutierrez - Trufi
**Fecha:** 2026-02-13 (actualizado)
**Asunto:** Estado de la carga de paraderos a OpenStreetMap, problemas encontrados y datos requeridos

---

## 1. Resumen Ejecutivo

Se procesaron los 1,858 registros de paraderos proporcionados por la Gerencia (archivo KMZ) y se cargaron a **OpenStreetMap** aquellos que pasaron los controles de calidad. El resultado:

| Concepto | Cantidad |
|----------|----------|
| Registros recibidos (KMZ) | 1,858 |
| Paradas únicas (deduplicadas) | 1,645 |
| **Cargadas a OpenStreetMap** | **1,405** |
| Descartadas por estar al lado izquierdo de la vía | 124 |
| Descartadas por estar fuera de toda ruta | 33 |
| Descartadas por duplicidad (< 20m entre ellas) | 74 |
| Solo en GTFS, no en datos del municipio | 91 |

Las 1,405 paradas cargadas se pueden visualizar en OpenStreetMap mediante la siguiente consulta:

**Enlace Overpass Turbo (copiar y pegar en el navegador):**
```
https://overpass-turbo.eu/?Q=node%5B%22source%22%3D%22Gerencia%20de%20Transporte%20Metropolitano%20de%20Trujillo%22%5D%28-8.23%2C-79.13%2C-7.99%2C-78.94%29%3Bout%20body%3B&R
```

Al abrir el enlace, hacer clic en "Ejecutar" (Run) para ver todas las paradas en el mapa.

---

## 2. Lo Que Se Hizo

### 2.1 Procesamiento de los datos KML

1. Se extrajeron los 1,858 registros del archivo KMZ proporcionado
2. Se deduplicaron registros que aparecían en múltiples capas (umbral: 10m) → 1,645 únicas
3. Se validó cada parada contra la geometría de las rutas del GTFS:
   - Se construyó una zona de cobertura de 20m alrededor de cada ruta
   - Se verificó que la parada estuviera del **lado derecho** de la vía (sentido de circulación en Perú)
   - Se descartaron paradas al lado izquierdo, fuera de ruta, y duplicadas

### 2.2 Carga a OpenStreetMap

- **1,377 paradas nuevas** creadas en OpenStreetMap
- **28 paradas fusionadas** con paradas que ya existían en OSM (se enriqueció la información sin mover su ubicación)
- Cada parada tiene el código de referencia del municipio (tag `ref`) para permitir trazabilidad
- Las paradas están etiquetadas según el estándar PTv2 (Public Transport Version 2) de OpenStreetMap

### 2.3 Asignación a rutas (completada)

Se asignaron las 1,405 paradas a las 214 relaciones de ruta en OpenStreetMap. Esto permite que aplicaciones de navegación y transporte muestren qué paradas corresponden a qué ruta, en el orden correcto del recorrido.

---

## 3. Problemas Encontrados — Acción Requerida

### 3.1 CRITICO: 11 códigos de paraderos duplicados

Se encontraron **11 códigos asignados a dos paraderos distintos** en diferentes ubicaciones. Esto impide identificar unívocamente cada paradero.

#### 9 códigos PE con colisión entre capas

Estos códigos aparecen en las capas "Consolidado" y "Puntos_Paraderos" asignados a paraderos a **más de 4 km de distancia** entre sí:

| Código | Paradero A (lat, lon) | Capa A | Paradero B (lat, lon) | Capa B | Distancia |
|--------|----------------------|--------|----------------------|--------|-----------|
| PE-237 | -8.0496012, -79.0563403 | Consolidado | -8.1065488, -79.0214104 | Puntos_Paraderos | 7,408 m |
| PE-238 | -8.0656021, -79.0449278 | Consolidado | -8.1062447, -79.0213554 | Puntos_Paraderos | 5,211 m |
| PE-239 | -8.0667633, -79.0452012 | Consolidado | -8.1047149, -79.0194718 | Puntos_Paraderos | 5,083 m |
| PE-240 | -8.0684283, -79.0448327 | Consolidado | -8.1042749, -79.0193401 | Puntos_Paraderos | 4,875 m |
| PE-241 | -8.1029616, -79.0176466 | Puntos_Paraderos | -8.0679315, -79.0475825 | Consolidado | 5,102 m |
| PE-242 | -8.0705267, -79.0433503 | Consolidado | -8.1023748, -79.0173110 | Puntos_Paraderos | 4,556 m |
| PE-243 | -8.0719115, -79.0416660 | Consolidado | -8.1009813, -79.0155783 | Puntos_Paraderos | 4,324 m |
| PE-244 | -8.0737571, -79.0412500 | Consolidado | -8.1005072, -79.0153155 | Puntos_Paraderos | 4,123 m |
| PE-247 | -8.0971849, -79.0117809 | Puntos_Paraderos | -8.0821358, -79.0492040 | Consolidado | 4,447 m |

**Acción requerida:** Asignar un código nuevo a uno de los dos paraderos de cada par.

#### 1 código PL-53 duplicado en Laredo

| Código | Paradero A (lat, lon) | Paradero B (lat, lon) | Distancia |
|--------|----------------------|----------------------|-----------|
| PL-53 | -8.0849631, -78.9555310 | -8.0823828, -78.9553352 | 288 m |

**Acción requerida:** Asignar un código diferente a uno de los dos.

#### 2 paraderos sin código ("PL-Existente")

| Código | Paradero A (lat, lon) | Paradero B (lat, lon) | Distancia |
|--------|----------------------|----------------------|-----------|
| PL-Existente | -8.0924662, -78.9672482 | -8.0927534, -78.9672582 | 32 m |

**Acción requerida:** Confirmar si son paraderos reales y asignarles códigos, o indicar si deben eliminarse.

---

### 3.2 CRITICO: Rutas sin paraderos en sus puntos de inicio y fin

#### El problema

Cuando un pasajero quiere planificar un viaje usando una aplicación de transporte (como Google Maps o Moovit), la aplicación necesita saber dónde empieza y dónde termina cada ruta de bus. Esta información viene de los **paraderos de inicio y fin de ruta** (también llamados "terminales").

En los datos proporcionados por la Gerencia, **muchas rutas no tienen paraderos registrados cerca de sus puntos de inicio o de fin**. Esto significa que, para la aplicación, la ruta "aparece" y "desaparece" en medio del camino, sin un punto claro donde el pasajero pueda tomar o dejar el bus.

Para el sistema GTFS (el formato que usan Google Maps y otras aplicaciones), habíamos creado paradas temporales (con códigos "GT-...") en esos puntos de inicio y fin. Sin embargo, **estas paradas temporales no se pueden publicar en OpenStreetMap** porque OpenStreetMap es un mapa colaborativo mundial que refleja la realidad — solo se pueden agregar paraderos que existan físicamente. Al publicar los paraderos oficiales de la Gerencia en OpenStreetMap, los paraderos ficticios quedaron expuestos como inconsistencias que deben resolverse.

**Esto es especialmente crítico para las rutas que van hacia otros municipios** (Laredo, Moche, Salaverry, zonas rurales), donde los tramos finales de la ruta no tienen ningún paradero registrado y el GTFS dependía enteramente de paradas ficticias.

#### Análisis: ¿qué tan grave es el problema?

Se analizaron las **214 rutas** del sistema para medir la distancia entre el punto de inicio/fin de cada ruta y el paradero más cercano que nos proporcionó la Gerencia. Los resultados:

| Situación | Cantidad de rutas | % del total |
|-----------|------------------|-------------|
| Tienen paradero cerca del inicio y fin (< 200m) | 144 | 67% |
| Brecha moderada en algún extremo (200m a 1 km) | 50 | 23% |
| **Brecha grave en algún extremo (más de 1 km)** | **20** | **9%** |

Las 144 rutas con paradero a menos de 200m de sus terminales están bien — el pasajero puede identificar fácilmente dónde tomar el bus. Las 50 con brecha moderada son manejables. Pero las 20 con brecha grave son un problema serio.

#### Las 5 rutas más críticas

Las 20 rutas con brecha grave corresponden en realidad a **5 líneas de bus** (cada línea tiene varias relaciones por sentido ida/vuelta y variantes). Todas son rutas largas que van desde Trujillo hacia sectores rurales alejados:

| Ruta | Destino lejano | Distancia sin paraderos | Largo total de la ruta |
|------|---------------|------------------------|----------------------|
| **C-15 P1** | Sector Huayabito / Sector Tres Cruces | **Los últimos 17 a 23 km no tienen ningún paradero** | 47 a 52 km |
| **C-30 C** | Sector Cushmun | **Los últimos 30 km no tienen ningún paradero** | 50 a 53 km |
| **C-31 P** | Sector Huangabal | **Los últimos 18 a 29 km no tienen ningún paradero** | 47 a 59 km |
| **C-32 S** | Mucha / Sector Collambay | **Los últimos 24 a 32 km no tienen ningún paradero** | 52 a 62 km |
| **C-33 P2** | Sector Platanar | **Los últimos 29 km no tienen ningún paradero** | 53 a 55 km |

**¿Qué significa esto en la práctica?** Imaginemos la ruta C-32 S que va de Palermo a Mucha. El bus recorre 62 km, pero los últimos 32 km no tienen un solo paradero registrado. Para un pasajero que quiere ir a Mucha, la aplicación de transporte no le puede indicar dónde bajarse — simplemente no hay información de paraderos en esa zona.

#### Rutas con brecha moderada — puntos terminales compartidos

Además de las 5 rutas críticas, se detectaron puntos terminales compartidos por varias rutas donde falta un paradero:

| Punto terminal | Rutas que llegan ahí | Brecha |
|---------------|---------------------|--------|
| **Avenida Libertad** (Salaverry) | M-07, M-08, M-09, M-10, M-12, M-36 (12 relaciones) | ~350 m |
| **Ciudad de Dios** | C-17, M-13 (3 relaciones) | ~390 m |
| **Sector Cerrito La Virgen** | C-28, M-04 (7 relaciones) | ~250-350 m |
| **Vía Panamericana** (sur) | M-35 (5 relaciones) | ~518 m |
| **Sector Taquila** | C-12 (2 relaciones) | ~538 m |

Agregar un solo paradero en cada uno de estos puntos resolvería el problema para múltiples rutas a la vez.

#### Acción requerida

La Gerencia debe proporcionarnos la ubicación real de los paraderos de inicio y fin de cada ruta. Necesitamos:

**Urgente (5 rutas rurales sin cobertura):**
1. Paraderos a lo largo y al final de la ruta **C-15 P1** (hacia Huayabito / Tres Cruces)
2. Paraderos a lo largo y al final de la ruta **C-30 C** (hacia Cushmun)
3. Paraderos a lo largo y al final de la ruta **C-31 P** (hacia Huangabal)
4. Paraderos a lo largo y al final de la ruta **C-32 S** (hacia Mucha / Collambay)
5. Paraderos a lo largo y al final de la ruta **C-33 P2** (hacia Platanar)

**Importante (5 puntos terminales compartidos — resuelven 29 rutas):**
6. Paradero en **Avenida Libertad** (Salaverry) — resuelve 6 rutas metropolitanas
7. Paradero en **Ciudad de Dios** — resuelve 2 rutas
8. Paradero en **Sector Cerrito La Virgen** — resuelve 4 rutas
9. Paradero en **Vía Panamericana** (sector sur, inicio de rutas M-35) — resuelve 5 rutas
10. Paradero en **Sector Taquila** — resuelve 2 rutas

Para cada paradero necesitamos:
- Coordenadas (latitud, longitud)
- Código de referencia

Sin esta información, las rutas quedarán incompletas y las aplicaciones de transporte no podrán ofrecer indicaciones correctas a los pasajeros en esos tramos.

---

### 3.3 Paradas descartadas por ubicación incorrecta

Se descartaron 231 paradas del KMZ por los siguientes motivos:

#### 124 paradas al lado izquierdo de la vía

Estas paradas están ubicadas al lado contrario al sentido de circulación. En Perú se circula por la derecha, por lo que los paraderos deben estar a la derecha de la vía en el sentido de marcha del bus.

**Posibles causas:**
- Error en la toma de coordenadas GPS
- La parada corresponde al sentido contrario de la ruta y no fue asignada correctamente

**Acción requerida:** Revisar estas 124 paradas y confirmar si deben reubicarse al lado correcto de la vía o si corresponden a otra ruta. La lista completa está disponible bajo solicitud.

#### 33 paradas fuera de toda ruta

Estas paradas están a más de 20 metros de cualquier ruta conocida.

**Posibles causas:**
- La ruta correspondiente no está en el GTFS actual
- Error de coordenadas

**Acción requerida:** Verificar si estas paradas corresponden a rutas no incluidas en el sistema actual.

#### 74 paradas duplicadas

Pares de paradas a menos de 20 metros de distancia entre sí, en el mismo lado de la calle, sin una vía de por medio. Se conservó una de cada par y se descartó la otra.

---

## 4. Resumen de Acciones Requeridas

| # | Prioridad | Acción | Impacto |
|---|-----------|--------|---------|
| 1 | **Urgente** | Enviar paraderos de las 5 rutas rurales sin cobertura (C-15, C-30, C-31, C-32, C-33) | Sin esto, tramos de 17 a 32 km quedan sin paraderos — las aplicaciones no pueden dar indicaciones en esas zonas |
| 2 | **Urgente** | Enviar paraderos en 5 puntos terminales compartidos (Av. Libertad, Ciudad de Dios, Cerrito La Virgen, Vía Panamericana, Taquila) | Un solo paradero en cada punto resuelve el problema para hasta 6 rutas a la vez (29 rutas en total) |
| 3 | **Alta** | Corregir 11 códigos duplicados | Dos paraderos distintos no pueden tener el mismo código — impide la trazabilidad (ver sección 3.1) |
| 4 | **Media** | Confirmar 2 paraderos "PL-Existente" | No tienen código asignado — indicar si son reales (ver sección 3.1) |
| 5 | **Media** | Revisar 124 paradas al lado izquierdo de la vía | Confirmar si son errores de ubicación o corresponden al sentido contrario |
| 6 | **Baja** | Verificar 33 paradas fuera de ruta | Confirmar si corresponden a rutas no incluidas en el sistema |

---

## 5. Asignación de Paraderos a Rutas — Resultados

### ¿Qué es la asignación de paraderos a rutas?

Cargar los paraderos al mapa es solo el primer paso. Para que una aplicación de transporte pueda decirle al pasajero "tome la ruta C-10 en el paradero PM-124", es necesario indicar **qué paraderos pertenecen a qué ruta**. A esto le llamamos "asignación".

Se procesaron las **214 rutas** del sistema, recorriendo cada una de principio a fin y verificando qué paraderos se encuentran a lo largo del camino, del lado derecho de la vía (donde el pasajero espera al bus) y a menos de 20 metros de la ruta.

### Resultados de la asignación

| Concepto | Cantidad |
|----------|----------|
| Rutas procesadas | 214 |
| Rutas con al menos un paradero asignado | **214 (100%)** |
| Total de asignaciones paradero→ruta | **10,172** |
| Paraderos únicos asignados a al menos una ruta | **1,398** de 1,405 |
| Paraderos no asignados a ninguna ruta | 7 |
| Promedio de paraderos por ruta | 48 |

### ¿Qué significa esto?

Cada una de las 214 rutas ahora tiene un listado ordenado de paraderos. Esto permite que las aplicaciones de transporte muestren al pasajero la secuencia completa de paradas de cada ruta.

Un mismo paradero puede pertenecer a varias rutas — por ejemplo, un paradero en la Avenida España puede ser utilizado por 5 o 6 rutas diferentes que pasan por esa avenida. El total de 10,172 asignaciones refleja esto: 1,398 paraderos distribuidos entre 214 rutas.

Adicionalmente, 29 rutas que realizan bucles o recorridos que pasan dos veces por la misma calle tienen paraderos que aparecen dos veces en la secuencia — una por cada paso del bus. Esto es correcto y necesario para que la aplicación muestre la secuencia real del recorrido.

Los 7 paraderos que no quedaron asignados a ninguna ruta están en zonas donde la geometría de la ruta pasa a más de 20 metros del paradero. Esto puede deberse a pequeñas imprecisiones en el trazado de la ruta o en la ubicación del paradero, y no es un problema grave.

### Control de calidad: paradas en calles paralelas

Se implementó un control de calidad adicional que detecta paradas que, aunque están dentro de los 20 metros de una ruta, están **mucho más cerca de otra vía**. Estas son paradas que geográficamente pertenecen a una calle paralela, no a la ruta en cuestión.

Se detectaron y corrigieron **83 asignaciones incorrectas** (24 paraderos físicos) donde la parada estaba a más de 15 metros de la ruta asignada pero a menos de 10 metros de otra ruta. Ejemplo: un paradero a 19 metros de la ruta M-21 pero a solo 1 metro de la ruta M-02 — claramente pertenece a la calle de la M-02, no de la M-21.

---

## 6. Medida Preventiva: Rutas Suspendidas en GTFS

### El problema

Las 5 rutas rurales con brechas graves (C-15, C-30, C-31, C-32, C-33) tienen tramos de 17 a 32 km sin ningún paradero registrado. Anteriormente, se habían creado paraderos ficticios (con código "GT-...") en el sistema GTFS para completar estos extremos de ruta.

Sin embargo, estos paraderos ficticios no representan la realidad:
- No existe un paradero físico en esas ubicaciones
- No se pueden publicar en OpenStreetMap (que solo acepta datos reales)
- Generan inconsistencia entre el GTFS y OpenStreetMap

### Decisión tomada

**Estas 5 rutas serán suspendidas temporalmente del GTFS** hasta que la Gerencia proporcione las ubicaciones reales de los paraderos en esos tramos. Esto significa que:

- Las 5 rutas **no aparecerán** temporalmente en aplicaciones como Google Maps o Moovit
- Las rutas **sí permanecen** en OpenStreetMap con los paraderos que existen
- Una vez que la Gerencia envíe los paraderos faltantes, las rutas serán reactivadas inmediatamente

**¿Por qué es mejor suspenderlas?** Porque es preferible que una ruta no aparezca en la aplicación, a que aparezca con información incorrecta. Si un pasajero planifica su viaje con paraderos ficticios y al llegar no encuentra el paradero, pierde la confianza en todo el sistema.

### Rutas suspendidas

| Ruta | Destino | Motivo |
|------|---------|--------|
| C-15 P1 | Huayabito / Tres Cruces | 17-23 km sin paraderos |
| C-30 C | Cushmun | 30 km sin paraderos |
| C-31 P | Huangabal | 18-29 km sin paraderos |
| C-32 S | Mucha / Collambay | 24-32 km sin paraderos |
| C-33 P2 | Platanar | 29 km sin paraderos |

**Para reactivarlas, necesitamos que la Gerencia nos envíe las ubicaciones (coordenadas y código) de los paraderos en los tramos faltantes.**

---

## 7. Estado Actual y Próximos Pasos

### Completado
- 1,405 paraderos cargados a OpenStreetMap con código de referencia del municipio
- Paraderos validados contra geometría de rutas (lado correcto de la vía, dentro de la zona de cobertura)
- 28 paraderos fusionados con datos existentes en OSM
- **10,172 asignaciones** de paraderos a **214 rutas** completadas
- Control de calidad: 83 asignaciones incorrectas detectadas y corregidas (paradas en calles paralelas)
- 29 rutas con bucles: paraderos que aparecen dos veces en la secuencia (correcto)
- 5 rutas con brechas graves identificadas y suspendidas del GTFS como medida preventiva

### Pendiente (requiere respuesta de la Gerencia)
- **Urgente:** Paraderos de inicio y fin de ruta de las 5 rutas rurales suspendidas (C-15, C-30, C-31, C-32, C-33) — sin estos datos, estas rutas no pueden aparecer en aplicaciones de transporte
- **Urgente:** Paraderos en 5 puntos terminales compartidos (Av. Libertad, Ciudad de Dios, Cerrito La Virgen, Vía Panamericana, Taquila) — un solo paradero en cada punto resuelve hasta 6 rutas
- **Alta:** Corrección de 11 códigos duplicados
- **Media:** Confirmación de 2 paraderos "PL-Existente"
- **Media:** Revisión de 124 paraderos al lado izquierdo de la vía
- **Baja:** Verificación de 33 paraderos fuera de ruta

---

## 8. Datos Técnicos de Referencia

- **Sistema:** OpenStreetMap (openstreetmap.org)
- **Estándar de etiquetado:** Public Transport v2 (PTv2)
- **Etiqueta de fuente:** `source = Gerencia de Transporte Metropolitano de Trujillo`
- **Red:** `network = Transporte Público Urbano Trujillo`
- **Coordenadas de referencia:** Las coordenadas de este informe se pueden verificar pegándolas directamente en Google Maps (formato: `-8.0496012, -79.0563403`)

### Consulta en línea de los paraderos cargados

Para ver todos los paraderos en el mapa, abrir el siguiente enlace y hacer clic en "Ejecutar":

```
https://overpass-turbo.eu/?Q=node%5B%22source%22%3D%22Gerencia%20de%20Transporte%20Metropolitano%20de%20Trujillo%22%5D%28-8.23%2C-79.13%2C-7.99%2C-78.94%29%3Bout%20body%3B&R
```

### Consulta en línea de las rutas

Para ver todas las rutas del sistema en el mapa:

```
https://overpass-turbo.eu/?Q=relation%5B%22network%22%3D%22Transporte%20P%C3%BAblico%20Urbano%20Trujillo%22%5D%5B%22route%22%3D%22bus%22%5D%28-8.30%2C-79.20%2C-7.90%2C-78.90%29%3Bout%20geom%3B&R
```
