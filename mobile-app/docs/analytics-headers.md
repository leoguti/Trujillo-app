# Headers de Analytics - Trujillo Mobility

## Que se hizo

Cada vez que un usuario busca una ruta en la app, se envian automaticamente
headers HTTP con informacion de ubicacion. Estos headers permiten analizar
patrones de viaje sin modificar el cuerpo de la peticion GraphQL.

Los headers se agregan al request que va al servidor OTP
(`otp.trujillo.trufi.dev`).

---

## Headers nuevos

Todos los headers empiezan con `x-` y se envian en cada busqueda de ruta:

| Header | Descripcion | Ejemplo |
|--------|-------------|---------|
| `x-origin-lat` | Latitud del punto de origen | `-8.123544450889383` |
| `x-origin-lng` | Longitud del punto de origen | `-78.99603068794154` |
| `x-origin-h3` | Indice H3 del origen (resolucion 15, ~1 metro) | `8f8f53ae8418c42` |
| `x-origin-district` | ID de relacion OSM del distrito de origen | `1968056` (Trujillo) |
| `x-destination-lat` | Latitud del punto de destino | `-8.089943702951487` |
| `x-destination-lng` | Longitud del punto de destino | `-79.0683311635458` |
| `x-destination-h3` | Indice H3 del destino (resolucion 15, ~1 metro) | `8f8f53af101ed8a` |
| `x-destination-district` | ID de relacion OSM del distrito de destino | `1968006` (Huanchaco) |

---

## Que es H3

H3 es un sistema de Uber que divide el mundo en hexagonos. Cada hexagono
tiene un codigo unico. Usamos resolucion 15 (la mas precisa, ~1 metro).

Para ver un H3 en el mapa, usar este sitio:
- https://observablehq.com/@nrabinowitz/h3-index-inspector

Pegar el codigo (por ejemplo `8f8f53ae8418c42`) y se muestra el hexagono
en el mapa.

Se puede bajar la resolucion desde el lado del consumidor de datos, por ejemplo
para agrupar por zonas mas grandes:

| Resolucion | Tamano aprox. | Uso tipico |
|------------|---------------|------------|
| 7 | ~2.6 km | Vista de ciudad |
| 9 | ~360 m | Vista de barrio |
| 11 | ~50 m | Vista de cuadra |
| 15 | ~1 m | Precision maxima (lo que enviamos) |

---

## Que es el ID de distrito

Es el ID de la relacion OSM (OpenStreetMap) del distrito. Cada distrito
de Trujillo tiene un ID unico. La app tiene un mapa (GeoJSON) con los
limites de los 18 distritos y determina automaticamente en cual distrito
cae cada punto.

Distritos incluidos:

| Distrito | ID OSM |
|----------|--------|
| Trujillo | 1968056 |
| Huanchaco | 1968006 |
| La Esperanza | 1968014 |
| El Porvenir | 1968000 |
| Florencia de Mora | 1968001 |
| Victor Larco Herrera | 1968062 |
| Laredo | 1968015 |
| Moche | 1968022 |
| Salaverry | 1968039 |
| Simbal | 1968051 |
| Poroto | 1968035 |
| Chicama | 1967993 |
| Viru | 1968061 |
| Otuzco | 1968026 |
| Salpo | 1968040 |
| Sinsicap | 1968052 |
| La Cuesta | 1968013 |
| Paranday | 1968031 |

Si un punto esta fuera de estos distritos, el header se envia vacio.

---

## Donde ver los datos

### API de Analytics

Los headers se guardan automaticamente en el servidor de analytics.

**Endpoint para consultar logs:**
```
https://analytics.trujillo.trufi.dev/analytics-api/Logs?headerContains=x-origin-district&limit=100&offset=0
```

**Parametros:**
- `headerContains=x-origin-district` — filtra solo los requests que tienen nuestros headers de analytics
- `limit` — cuantos registros traer
- `offset` — desde que registro empezar (para paginacion)

**Documentacion Swagger (todos los endpoints disponibles):**
```
https://analytics.trujillo.trufi.dev/analytics-api/swagger/index.html
```

### Ejemplo real de produccion

Asi se ve un request real en el log de analytics:

```json
{
  "requestHeaders": {
    "x-origin-lat": ["-8.123544450889383"],
    "x-origin-lng": ["-78.99603068794154"],
    "x-origin-h3": ["8f8f53ae8418c42"],
    "x-origin-district": ["1968056"],
    "x-destination-lat": ["-8.089943702951487"],
    "x-destination-lng": ["-79.0683311635458"],
    "x-destination-h3": ["8f8f53af101ed8a"],
    "x-destination-district": ["1968006"]
  }
}
```

En este ejemplo el usuario busco una ruta desde el distrito de Trujillo
(1968056) hasta Huanchaco (1968006).

---

## Que datos tiene cada registro del log

Cada entrada del log tiene toda la informacion del request y la respuesta.
Estos son los campos principales:

| Campo | Que contiene |
|-------|-------------|
| `id` | Numero unico del registro |
| `method` | Siempre `POST` |
| `uri` | `/otp/routers/default/index/graphql` |
| `host` | `otp.trujillo.trufi.dev` |
| `ip` | IP del usuario |
| `userAgent` | `Dart/3.11 (dart:io)` (la app Flutter) |
| `statusCode` | `200` si fue exitoso |
| `requestHeaders` | Los 8 headers `x-` con H3, distrito y coordenadas |
| `body` | La consulta GraphQL con los parametros de busqueda |
| `responseBody` | La respuesta completa con las rutas encontradas |
| `receivedAt` | Fecha y hora exacta (ej: `2026-02-16T10:05:33Z`) |

### Datos del body (la busqueda del usuario)

El campo `body` contiene los parametros que el usuario uso para buscar la ruta:

```json
{
  "variables": {
    "fromPlace": "Ubicacion seleccionada::-8.1235,-78.9960",
    "toPlace": "Ubicacion seleccionada::-8.0899,-79.0683",
    "numItineraries": 5,
    "date": "2026-02-16",
    "time": "06:05",
    "walkSpeed": 1.33,
    "walkReluctance": 2.0,
    "transportModes": [
      {"mode": "TRANSIT"},
      {"mode": "WALK"}
    ]
  }
}
```

| Variable | Que significa |
|----------|--------------|
| `fromPlace` | Punto de origen (nombre + coordenadas) |
| `toPlace` | Punto de destino (nombre + coordenadas) |
| `numItineraries` | Cuantas opciones de ruta se pidieron (normalmente 5) |
| `date` | Fecha del viaje |
| `time` | Hora del viaje |
| `walkSpeed` | Velocidad al caminar en m/s (1.33 = velocidad normal) |
| `walkReluctance` | Que tanto evitar caminar (2.0 = normal, mas alto = menos caminata) |
| `transportModes` | Tipos de transporte (TRANSIT = bus, WALK = caminar) |

### Datos del responseBody (las rutas encontradas)

La respuesta tiene las rutas que OTP encontro. Ejemplo real:

**Itinerario 1 — Solo caminando**
- Duracion: 2 horas 6 min
- Distancia caminando: 9,868 m
- Buses: ninguno

**Itinerario 2 — 2 buses**
- Duracion: 1 hora 16 min
- Distancia caminando: 2,958 m
- Buses: M-35 D (EL ICARO) + M-05 H (HUANCHACO S.A.)

**Itinerario 3 — 2 buses**
- Duracion: 1 hora 11 min
- Distancia caminando: 2,704 m
- Buses: C-29 A (CABALLITO DE TOTORA) + M-04 A (HUANCHACO S.A.)

Cada itinerario tiene esta informacion:

| Campo | Descripcion |
|-------|-------------|
| `duration` | Duracion total en segundos |
| `walkTime` | Tiempo caminando en segundos |
| `walkDistance` | Distancia caminando en metros |
| `waitingTime` | Tiempo esperando bus en segundos |
| `legs` | Lista de tramos (cada tramo es caminar o un bus) |

Cada tramo (`leg`) de bus tiene:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| `mode` | Tipo de transporte | `BUS` o `WALK` |
| `route.shortName` | Codigo de la ruta | `C-29 A` |
| `route.longName` | Nombre completo de la ruta | `Sector Las Lomas → Los Sauces de Barraza` |
| `route.agency.name` | Empresa de transporte | `CABALLITO DE TOTORA S.A.` |
| `from.stop.name` | Paradero de subida | nombre o `unnamed` |
| `to.stop.name` | Paradero de bajada | nombre o `unnamed` |
| `startTime` | Hora de subida (timestamp) | `1771240994000` |
| `endTime` | Hora de bajada (timestamp) | `1771241580000` |
| `duration` | Duracion del tramo en segundos | `586` |
| `distance` | Distancia del tramo en metros | `3284.82` |
| `intermediatePlaces` | Paraderos intermedios | lista de paradas |

### Que se puede analizar con estos datos

Combinando los headers `x-` con los bodies, se puede obtener:

- **Rutas mas buscadas** — entre que distritos viaja la gente
- **Empresas mas usadas** — que empresas de bus aparecen mas en las rutas sugeridas
- **Lineas de bus mas frecuentes** — cuales codigos de ruta (C-29, M-35, etc.) se sugieren mas
- **Horarios pico** — a que horas se buscan mas rutas (`date` + `time`)
- **Patrones por zona** — usando H3 se puede hacer mapas de calor de origenes/destinos
- **Distancia caminando** — cuanto tienen que caminar los usuarios para llegar al bus
- **Tiempos de viaje** — duracion promedio por par de distritos
- **Cobertura** — detectar zonas donde el usuario queda fuera de los distritos conocidos (header vacio)

---

## Archivos del proyecto

| Archivo | Que hace |
|---------|----------|
| `lib/services/analytics_header_provider.dart` | Arma los headers con H3, distrito y coordenadas |
| `lib/services/district_service.dart` | Carga el mapa de distritos y determina en cual cae un punto |
| `assets/geo/distritos_trujillo.geojson` | Limites de los 18 distritos (datos de OpenStreetMap) |
| `lib/main.dart` | Conecta el header provider al routing engine |

### Dependencias agregadas

- `h3_flutter: ^0.7.1` — Calculo de indices H3 (funciona en Android, iOS y Web)

---

## Como funciona internamente

1. El usuario busca una ruta (origen → destino)
2. Antes de enviar el request a OTP, se ejecuta el `planHeaderProvider`
3. El provider calcula:
   - H3 del origen y destino (usando la libreria h3_flutter)
   - Distrito del origen y destino (buscando en que poligono cae el punto)
4. Se agregan los 8 headers al request HTTP
5. OTP procesa la ruta normalmente (ignora los headers extra)
6. El servidor de analytics captura los headers para analisis
