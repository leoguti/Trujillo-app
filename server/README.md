# `server/` — Infraestructura de trujillo.trufi.dev

Esta carpeta refleja exactamente qué corre en el servidor de producción.
Cada subcarpeta es un servicio Docker independiente. Las que apuntan a
repositorios externos están como **submódulos git**.

## Servicios

| Carpeta | Repositorio | Tipo | Puerto | Función | Doc detallada |
|---|---|---|---|---|---|
| [`otp/`](./otp/) | [trufi-server-otp](https://github.com/trufi-association/trufi-server-otp) | submódulo | `:8080` | Planificador de viajes OpenTripPlanner | [→ otp.md](./docs/services/otp.md) |
| [`server/`](./server/) | [trufi-server](https://github.com/trufi-association/trufi-server) | submódulo | `:80` `:443` | Reverse proxy YARP + DB de requests | [→ yarp.md](./docs/services/yarp.md) |
| [`photon/`](./photon/) | [trufi-server-photon](https://github.com/trufi-association/trufi-server-photon) | submódulo | `:2322` | Geocodificador de direcciones | [→ photon.md](./docs/services/photon.md) |
| [`tileserver-gl/`](./tileserver-gl/) | [trufi-server-tileserver-gl](https://github.com/trufi-association/trufi-server-tileserver-gl) | submódulo | interno | Mapas vectoriales para la app | [→ tileserver-gl.md](./docs/services/tileserver-gl.md) |
| [`gtfs-rt-proxy/`](./gtfs-rt-proxy/) | (en este repo) | local | `:8001` | Enriquece feed GTFS-RT con `trip_id` | [→ README](./gtfs-rt-proxy/README.md) |
| [`web-landing/`](./web-landing/) | (en este repo) | local | `:80` (vía YARP) | Landing pública del proyecto | [→ README](./web-landing/README.md) |

## Documentación

- **Por servicio:** [`docs/services/`](./docs/services/) — un markdown por cada
  servicio con endpoints, configuración, comandos de despliegue y troubleshooting
- **Operaciones generales:** [`docs/operations.md`](./docs/operations.md) —
  health check global, deploy, backups, diagnóstico común
- **Datos de input:** [`data/README.md`](./data/README.md) — qué archivos
  necesita cada servicio y cómo refrescarlos
- **Presentación visual:** [`../docs/`](../docs/) — sitio HTML estilo
  PowerPoint con la arquitectura

## Data de input

Los inputs canónicos (GTFS, OSM, mbtiles) viven en [`data/`](./data/) — ~26 MB
en total. Para refrescar (pull desde el server):

```bash
SERVER=root@trujillo.trufi.dev
scp $SERVER:/root/otp/data/trujillo.gtfs.zip          server/data/
scp $SERVER:/root/otp/data/trujillo.osm.pbf           server/data/
scp $SERVER:/root/tileserver-gl/data/trujillo.mbtiles server/data/
scp $SERVER:/root/gtfs-rt-proxy/data/trujillo.gtfs.zip server/gtfs-rt-proxy/data/
```

Para subir cambios al server, invertir el origen y destino del `scp`.
Detalle por archivo en [`data/README.md`](./data/README.md).

Los archivos derivados (`graph.obj` de OTP, índice de Photon) **no** se
commitean — los servicios los reconstruyen al levantar.

## Trabajar con submódulos

```bash
# Clonar desde cero con todo
git clone --recurse-submodules https://github.com/leoguti/GTFS-Trujillo.git

# Si ya clonaste sin --recurse
git submodule update --init --recursive

# Traer el último main de cada submódulo
git submodule update --remote --merge
```

Los submódulos están configurados con `branch = main`. El commit que
registra este repo refleja el snapshot del último `git add` — para
moverlos al HEAD de su rama, usar `git submodule update --remote`.

## Despliegue rápido

Cada servicio se despliega independientemente. Cheat sheet:

```bash
ssh root@trujillo.trufi.dev
cd /root/<servicio>
git pull                      # si el folder tiene .git
docker compose up -d --build
```

Detalles por servicio en [`docs/services/`](./docs/services/) y operaciones
cross-cutting en [`docs/operations.md`](./docs/operations.md).

## Healthcheck rápido

```bash
ssh root@trujillo.trufi.dev '
  docker ps --format "table {{.Names}}\t{{.Status}}"
'
```

Hay dos healthchecks "falsos negativos" conocidos (servicio sano pero el
test interno está roto): `server-server-1` y `trufi-tileserver-gl`. Detalle
en sus respectivos docs.

## El pipeline GTFS-RT — qué hace especial este sistema

La app móvil necesita posiciones de vehículos en tiempo real, pero el feed
que publica el driver app a S3 **no incluye `trip_id`** — un dato que OTP
necesita. El servicio [`gtfs-rt-proxy/`](./gtfs-rt-proxy/) cruza el feed
con el GTFS estático para inyectar el `trip_id` correcto antes de que OTP
lo consuma.

```
driver app  →  S3 (.proto)  →  gtfs-rt-proxy [enrich]  →  OTP  →  app móvil
```

Detalle completo en [`gtfs-rt-proxy/README.md`](./gtfs-rt-proxy/README.md)
y la presentación visual en [`/docs`](../docs/).
