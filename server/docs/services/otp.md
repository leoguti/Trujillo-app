# OTP — OpenTripPlanner

Motor de ruteo multimodal. Combina el GTFS estático con el feed en tiempo real
para responder consultas tipo *"¿cómo llego de A a B en transporte público?"*.

- **Repo:** [trufi-association/trufi-server-otp](https://github.com/trufi-association/trufi-server-otp)
- **Local:** [`../../otp/`](../../otp/) (submódulo, branch `main`)
- **Container:** `otp`
- **Puerto:** `8080`
- **Versión OTP:** `2.8.1` (configurable, ver `Dockerfiles/`)

## Endpoints

- `GET /otp/` — health
- `GET /otp/routers/default/index/graphql` — API GraphQL principal (la que consume la app)
- `GET /otp/routers/default/plan` — API legacy de planificación
- Documentación oficial: https://docs.opentripplanner.org

## Datos de entrada

OTP necesita **dos archivos** + el feed en tiempo real:

| Archivo | Origen | En el repo |
|---|---|---|
| `trujillo.gtfs.zip` | itinerario estático (rutas, paraderos, horarios) | [`server/data/trujillo.gtfs.zip`](../../data/trujillo.gtfs.zip) |
| `trujillo.osm.pbf` | extract de OpenStreetMap | [`server/data/trujillo.osm.pbf`](../../data/trujillo.osm.pbf) |
| GTFS-RT live | posiciones de buses ahora mismo | vía `gtfs-rt-proxy` (poll cada 30s) |

> El archivo `graph.obj` (~20 MB) que ves en `/root/otp/data/` del server **no se commitea**.
> OTP lo regenera de los inputs anteriores cada vez que arranca.

## Configuración

`Dockerfiles/2.8.1/config/otp-config.json`:

```json
{
  "otpFeatures": {
    "GtfsGraphQlApi": true
  }
}
```

`Dockerfiles/2.8.1/config/router-config.json` define los streams GTFS-RT.
La URL del proxy está hardcoded ahí. Para cambiarla, editar y rebuild.

### Variables de entorno

| Var | Default | Descripción |
|---|---|---|
| `JAVA_MAX_MEMORY` | `-Xmx2G` | RAM máxima para la JVM |
| `otpversion` | `2.8.1` | Versión a buildear (carpeta dentro de `Dockerfiles/`) |

### Healthcheck

```yaml
test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/otp/"]
interval: 30s
timeout: 10s
start_period: 120s   # OTP tarda en arrancar (rebuild de graph)
retries: 3
```

## Despliegue

### Primera vez (build de graph)

```bash
ssh root@trujillo.trufi.dev
cd /root/otp

# Init.sh ayuda a configurar volúmenes y descargar OTP
./init.sh --gtfs /root/otp/data/trujillo.gtfs.zip --pbf /root/otp/data/trujillo.osm.pbf

docker compose up -d --build
```

### Cambio de GTFS o OSM

```bash
# 1. Subir el archivo nuevo (ej. desde el repo local):
SERVER=root@trujillo.trufi.dev
scp server/data/trujillo.gtfs.zip $SERVER:/root/otp/data/
scp server/data/trujillo.osm.pbf  $SERVER:/root/otp/data/

# 2. En el server, borrar el graph viejo para forzar rebuild:
ssh root@trujillo.trufi.dev 'rm /root/otp/data/graph.obj'

# 3. Reiniciar OTP. Va a tardar ~2-3 min en regenerar el graph.
ssh root@trujillo.trufi.dev 'cd /root/otp && docker compose restart'

# 4. Mirar los logs para confirmar:
ssh root@trujillo.trufi.dev 'docker logs -f otp'
```

### Cambio de versión de OTP

```bash
# Edita docker-compose.yml o exporta la variable
otpversion=2.7.0 docker compose up -d --build
```

## Observabilidad

```bash
# Estado del container
docker ps --filter name=otp

# Logs en vivo
docker logs -f otp

# Health (desde dentro del server)
curl -s http://localhost:8080/otp/

# Probar una consulta GraphQL
curl -s 'http://localhost:8080/otp/routers/default/index/graphql' \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ routes { gtfsId shortName } }"}' | head -c 500
```

## Troubleshooting

### OTP no levanta — el graph no se construye
Mirá los logs. Si dice "Could not find GTFS data", revisa que los archivos
estén en `/root/otp/data/` y que el mount del compose apunte ahí.

### OTP responde pero no hay tiempo real
Significa que el polling al `gtfs-rt-proxy` está fallando.
- Verificá que ambos containers están en la red `trufi-server`
- Probá `curl http://gtfs-rt-proxy:8000/gtfsrt.proto` desde dentro del container otp

### Out of memory (OOM)
Subir `JAVA_MAX_MEMORY` y `mem_limit` en `docker-compose.yml`. Para Trujillo
2 GB suele ser suficiente.

### Graph build muy lento
Normal en primera vez (puede tardar 5-10 min). Subsecuentes son más rápidas
porque OTP cachea estructuras en disco. Si querés rebuild forzado, borrá
`graph.obj` antes del restart.
