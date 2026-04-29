# gtfs-rt-proxy

El servicio más crítico del pipeline en tiempo real. Lee el feed GTFS-RT
que publica el driver app a S3, **enriquece cada vehículo inyectando el
`trip_id`**, y lo expone listo para que OTP lo consuma.

> Sin este proxy, OTP no sabe a qué viaje específico corresponde cada
> bus que reporta posición — y por lo tanto no puede mostrar ETAs.

- **Container:** `gtfs-rt-proxy` (+ `gtfs-rt-simulator` opcional)
- **Puerto:** `8001` (mapeado desde `:8000` interno, en `127.0.0.1`)
- **Stack:** Python 3 + Flask + protobuf

## Endpoints

| Endpoint | Qué devuelve |
|---|---|
| `GET /` | metadata: modo (sim/prod), upstream, endpoints |
| `GET /gtfsrt.proto` | feed GTFS-RT enriquecido (lo que polea OTP) |
| `GET /healthz` | healthcheck con stats del último ciclo |

## Flujo

```
S3 / simulador  ──►  fetch  ──►  enrich(feed)  ──►  cache 5s  ──►  /gtfsrt.proto
                                  │
                                  └─ schedule.match(route_id, direction_id, start_time)
                                            │
                                            └─ trip.trip_id = matched_trip_id
```

`enrich()` (en `app.py`):

```python
match = schedule.match(trip.route_id, trip.direction_id, trip.start_time)
if match is None:
    skipped_no_schedule += 1
    continue

matched_trip_id, aligned = match
trip.trip_id = matched_trip_id
trip.start_time = aligned
```

`schedule.py` carga el GTFS estático (en `data/trujillo.gtfs.zip`) y construye
un índice `(route_id, direction_id, hora aproximada) → trip_id`.

## Configuración

Variables del compose (con defaults razonables):

| Variable | Default | Descripción |
|---|---|---|
| `SIMULATED` | `false` | Si `true`, lee del simulador local en vez de S3 |
| `UPSTREAM_URL_PROD` | URL S3 fija | feed real del driver app |
| `UPSTREAM_URL_SIM` | URL del simulador | usado cuando `SIMULATED=true` |
| `GTFS_PATH` | `/app/data/trujillo.gtfs.zip` | GTFS estático |
| `CACHE_TTL` | `5` | seconds de cache del feed enriquecido |
| `UPSTREAM_TIMEOUT` | `10` | timeout HTTP al fetch |

### Override local con `.env`

Crear un `.env` (gitignoreado) en `server/gtfs-rt-proxy/`:

```bash
# Para desarrollo local
SIMULATED=true
CLONE_FACTOR=3
MAX_VEHICLES=3
```

## Datos

| Archivo | Función |
|---|---|
| `data/trujillo.gtfs.zip` | GTFS estático para hacer match `route_id → trip_id` |
| `simulator/patterns.json` | Trayectorias precomputadas para el simulador |

> El GTFS aquí es una **versión simplificada** (1 MB) — diferente al de OTP
> (18 MB en `server/data/`). El proxy solo necesita lo mínimo para el match.

## Despliegue

```bash
ssh root@trujillo.trufi.dev
cd /root/gtfs-rt-proxy

# Levantar (red trufi-server tiene que existir)
docker compose up -d --build

# Reiniciar
docker compose restart

# Bajar
docker compose down
```

## Observabilidad

```bash
# Containers
docker ps --filter name=gtfs-rt

# Logs en vivo
docker logs -f gtfs-rt-proxy

# Health (devuelve stats del último enrich)
curl -s http://127.0.0.1:8001/healthz | jq

# Probar el feed (binario protobuf)
curl -s http://127.0.0.1:8001/gtfsrt.proto | wc -c

# Ver modo actual (real vs simulado)
curl -s http://127.0.0.1:8001/ | jq
```

Ejemplo de log normal cada 30s:
```
INFO gtfs-rt-proxy enriched: {'entities': 3, 'rewritten': 3, 'skipped_no_schedule': 0}
```

## El simulador (`simulator/`)

Si no hay conductores reales en la calle (ej. fines de semana, dev), se
levanta un container que **emite un feed sintético** basado en patrones
recordados de viajes reales.

- Lee `simulator/patterns.json` (~260 KB, commiteado)
- Genera FeedMessages con `clone_factor` vehículos por patrón
- Sirve en `:9000`

Activar con `SIMULATED=true` en el `.env` del proxy. Útil para:
- Probar localmente sin acceso al feed real
- Demostraciones / presentaciones
- Tests automatizados

Para regenerar `patterns.json` con nuevos datos, mirar [`simulator/README.md`](./simulator/README.md).

## Troubleshooting

### `entities_without_trip` alto en `/healthz`
El feed crudo trae vehículos sin info de `route_id`/`direction_id`. Es un
problema del driver app, no del proxy. Reportar a quien mantiene la app.

### `skipped_no_schedule` alto
El `route_id` que viene en el feed no aparece en el GTFS estático.
Sucede cuando el GTFS está desactualizado o tiene IDs distintos al feed.
Solución: actualizar `data/trujillo.gtfs.zip`.

### El cache se queda pegado
El proxy cachea por `CACHE_TTL` segundos (5 por default). Si necesitás
forzar un refresh, reiniciá el container.

### El proxy responde 502
El upstream (S3 o simulador) no contesta. Verificar conectividad. En
modo PROD probar manualmente:

```bash
curl -I https://trujillo-admin-storage.s3.us-east-1.amazonaws.com/driver/gtfsrt/pe-trujillo.proto
```
