# Operaciones — runbook común

Tareas operativas que aplican a múltiples servicios. Para detalles
específicos de cada uno, ir a [`services/`](./services/).

## Acceder al server

```bash
ssh root@trujillo.trufi.dev
```

> Server: Ubuntu 22.04, 1 instancia, 4 GB RAM (según `free -h`), 78 GB disco.
> Stack: Docker + Docker Compose. Todos los servicios en la red `trufi-server`.

## Estado general — health check

```bash
ssh root@trujillo.trufi.dev '
  echo "=== CONTAINERS ==="
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  echo
  echo "=== DISK ==="
  df -h | grep -v overlay
  echo
  echo "=== MEMORY ==="
  free -h
  echo
  echo "=== LOAD ==="
  uptime
'
```

Si algún container aparece `unhealthy`, revisar el doc del servicio:

| Servicio | Doc |
|---|---|
| OTP | [`services/otp.md`](./services/otp.md) |
| gtfs-rt-proxy | [`../gtfs-rt-proxy/README.md`](../gtfs-rt-proxy/README.md) |
| Photon | [`services/photon.md`](./services/photon.md) |
| TileServer GL | [`services/tileserver-gl.md`](./services/tileserver-gl.md) |
| YARP / server | [`services/yarp.md`](./services/yarp.md) |
| web-landing | [`../web-landing/README.md`](../web-landing/README.md) |

## Healthchecks "falsos negativos" conocidos

| Container | Estado | Realidad |
|---|---|---|
| `server-server-1` | unhealthy | El test usa `/dev/tcp/...` que no existe en su shell. El proxy funciona |
| `trufi-tileserver-gl` | unhealthy | El script `node healthcheck.js` falla pero `GET /` responde 200 |

## Logs

```bash
# Todos los logs en vivo (mejor con tmux/screen)
docker logs -f <container>

# Últimos N logs
docker logs --tail 100 <container>

# Logs con timestamps
docker logs -t <container>

# Logs de los últimos 30 minutos
docker logs --since 30m <container>
```

Containers principales: `otp`, `gtfs-rt-proxy`, `gtfs-rt-simulator`, `photon`,
`trufi-tileserver-gl`, `server-server-1`, `server-db-1`, `web-landing`.

## Despliegue de cambios

### Servicio que vive en este repo (gtfs-rt-proxy, web-landing)

```bash
# 1. Hacer cambios localmente
git commit -am "..."
git push

# 2. Sincronizar al server (no hay CI/CD aún)
rsync -avz --exclude='.git' --exclude='__pycache__' \
  ./server/gtfs-rt-proxy/ \
  root@trujillo.trufi.dev:/root/gtfs-rt-proxy/

# 3. Restart en el server
ssh root@trujillo.trufi.dev 'cd /root/gtfs-rt-proxy && docker compose up -d --build'
```

### Servicio que es submódulo (otp, photon, tileserver-gl, server)

El código vive en repos de `trufi-association`. En el server tienen su
propio `.git` y se actualizan con `git pull`.

```bash
ssh root@trujillo.trufi.dev
cd /root/otp     # o cualquier otro
git pull
docker compose up -d --build
```

## Refrescar la data de input (GTFS / OSM / mbtiles)

Ver [`server/data/README.md`](../data/README.md). Resumen con `scp`:

```bash
SERVER=root@trujillo.trufi.dev

# Bajar la data del server al repo (después de cambios en server)
scp $SERVER:/root/otp/data/trujillo.gtfs.zip          server/data/
scp $SERVER:/root/otp/data/trujillo.osm.pbf           server/data/
scp $SERVER:/root/tileserver-gl/data/trujillo.mbtiles server/data/
scp $SERVER:/root/gtfs-rt-proxy/data/trujillo.gtfs.zip server/gtfs-rt-proxy/data/

# Subir (invertir origen y destino) — destructivo en el server
scp server/data/trujillo.gtfs.zip $SERVER:/root/otp/data/
# ...idem para los otros archivos
```

Si actualizaste el GTFS, **OTP necesita regenerar el graph**:

```bash
ssh root@trujillo.trufi.dev '
  rm /root/otp/data/graph.obj
  cd /root/otp && docker compose restart
'
docker logs -f otp   # mirar el rebuild (~2-3 min)
```

## Backups

### PostgreSQL (analytics)

```bash
ssh root@trujillo.trufi.dev '
  docker exec server-db-1 pg_dump -U analytics analytics
' > backups/analytics-$(date +%Y%m%d).sql
```

### Certificados SSL

LettuceEncrypt los persiste en `/root/server/data/lettuce-encrypt/`. Se
re-emiten automáticamente; backup opcional pero útil para evitar
re-emisión rate limits si reinstalás todo:

```bash
rsync -avz root@trujillo.trufi.dev:/root/server/data/lettuce-encrypt/ \
  backups/lettuce-encrypt/
```

## Diagnóstico común

### Memoria al límite
El server tiene 4 GB y el uso suele ir cerca de 3 GB. **No tiene swap**.
Si OTP necesita rebuild grande puede OOM. Considerar:
- Activar swap: `swapon /swapfile` (al menos 2 GB)
- Reducir `JAVA_MAX_MEMORY` de OTP si la app no necesita tanto
- Mover photon a otra instancia si crece mucho

### Disco lleno
Suelen ser:
1. Imágenes Docker viejas: `docker image prune -a`
2. Logs de containers: `docker system prune --volumes`
3. Backups de OTP: `/root/otp/old_data/` y `*.bak.*` files
4. Photon data: `/root/photon/photon_data/` (varios GB legítimos)

### El sistema parece "lento" de repente
- `docker ps` — algún container reiniciando en loop?
- `docker stats` — algún container comiendo CPU/RAM?
- `journalctl -u docker --since "10 min ago"` — errores en docker engine?

### Reiniciar TODO el stack (último recurso)

```bash
ssh root@trujillo.trufi.dev '
  for d in /root/server /root/otp /root/gtfs-rt-proxy /root/photon /root/tileserver-gl /root/web-landing; do
    echo "=== restarting $d ==="
    cd "$d" && docker compose restart
  done
'
```
