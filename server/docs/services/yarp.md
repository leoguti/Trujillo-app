# YARP / trufi-server — Reverse proxy + analytics

El "frente" del sistema. Termina TLS, enruta tráfico HTTPS hacia los
servicios internos, y registra cada request en una base PostgreSQL para
analítica posterior. Construido con .NET + YARP (Yet Another Reverse Proxy
de Microsoft).

- **Repo:** [trufi-association/trufi-server](https://github.com/trufi-association/trufi-server)
- **Local:** [`../../server/`](../../server/) (submódulo, branch `main`)
- **Containers:** `server-server-1` (proxy), `server-db-1` (postgres)
- **Puertos:** `80`, `443`
- **SSL:** automático vía Let's Encrypt (LettuceEncrypt)

## Arquitectura interna

```
Cliente ─[80/443]─► YARP ──► Analytics middleware ──► Backend
                              │
                              └─[async]─► PostgreSQL (`requests` table)
```

Cada request:
1. Entra por TLS (cert auto-renovado)
2. YARP la enruta según hostname/path
3. Middleware loggea (no bloquea)
4. Va al backend (otp, photon, tileserver, web-landing, etc.)

## Routing

Cada servicio que quiere ser expuesto trae un `trufi-proxy.json`:

```json
{
  "name": "otp",
  "description": "OpenTripPlanner...",
  "container": "otp",
  "port": 8080,
  "analytics": true
}
```

El `setup.sh` del server lo lee y configura:
- Subdominio para SSL (ej. `otp.trujillo.trufi.dev`)
- Cluster YARP para forward
- Si `analytics:true`, registra los requests

## Configuración

`data/config/appsettings.json` (montado read-only) define:
- Dominios + certificados
- Routes/clusters de YARP
- Connection string a la DB
- Email para Let's Encrypt

`data/certificates/` y `data/lettuce-encrypt/` persisten los certs.
`data/postgres/` persiste la DB de analytics.

### Variables de entorno

| Var | Default | Descripción |
|---|---|---|
| `ASPNETCORE_ENVIRONMENT` | `Production` | modo .NET |
| `DATABASE_URL` | `Host=db;...` | conexión a Postgres interno |

### Healthcheck

```yaml
test: ["CMD-SHELL", "cat < /dev/tcp/localhost/80 || exit 1"]
interval: 30s
```

> ⚠️ El healthcheck **está mal configurado** en este server. El shell del
> container de .NET no soporta `/dev/tcp/...`. Aparece como `unhealthy`
> aunque el proxy funcione perfectamente. Reemplazar por `curl` o `wget`
> cuando sea convenient.

## Despliegue

### Primera vez

```bash
ssh root@trujillo.trufi.dev
cd /root/server

./setup.sh   # interactivo: pide email para Let's Encrypt
# durante el setup:
#   [1] Add external service - lee trufi-proxy.json del servicio
#   [2] Expose Analytics API - opcional

docker compose up -d
```

### Agregar un servicio nuevo

```bash
# 1. El servicio debe existir y tener su trufi-proxy.json
ssh root@trujillo.trufi.dev
cd /root/server
./setup.sh
# Seleccionar [1] Add service y apuntar al trufi-proxy.json del nuevo servicio
docker compose restart server
```

### Renovar / agregar dominios

LettuceEncrypt renueva automáticamente. Para dominios nuevos:

```bash
# Editar data/config/appsettings.json y reiniciar
ssh root@trujillo.trufi.dev 'cd /root/server && docker compose restart server'
```

## Analytics — la base de datos

Tabla `requests` con columnas: `body`, `created_at`, `device_id`, `host`, `ip`,
`method`, `received_at`, `request_content_type`, `request_headers`,
`response_body`, `response_content_type`, `response_headers`, `status_code`,
`uri`, `user_agent`.

```bash
# Acceso a la DB
ssh root@trujillo.trufi.dev
docker exec -it server-db-1 psql -U analytics -d analytics

# Ejemplos de query
SELECT host, COUNT(*) FROM requests
  WHERE created_at > now() - interval '1 hour'
  GROUP BY host;

SELECT uri, status_code FROM requests
  WHERE status_code >= 500
  ORDER BY received_at DESC LIMIT 20;
```

## Observabilidad

```bash
# Estado de ambos containers
docker ps --filter name=server-

# Logs del proxy
docker logs -f server-server-1

# Logs de la DB
docker logs -f server-db-1

# Test desde fuera
curl -I https://trujillo.trufi.dev/
```

## Troubleshooting

### Containers `unhealthy` pero todo funciona
Es el bug del healthcheck (`/dev/tcp` no existe en el shell). Si los logs
muestran 200s saliendo, el servicio está bien.

### TLS no se renueva
Mirar logs de LettuceEncrypt. Suele ser:
- Email mal configurado en `appsettings.json`
- Puerto 80 bloqueado (Let's Encrypt valida con HTTP)

### DB crece mucho
La tabla `requests` puede explotar. Considerar:
- TRUNCATE periódico de filas antiguas
- Mover analytics a otro storage (S3, ClickHouse)
- Backups regulares: `docker exec server-db-1 pg_dump -U analytics analytics > backup.sql`

### El proxy devuelve 502
El backend al que enrutar está caído o no responde. Verificar el container
del backend (`docker ps`, `docker logs`).
