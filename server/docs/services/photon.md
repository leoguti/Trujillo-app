# Photon — Geocoder

Servidor de [Photon](https://photon.komoot.io) (de Komoot) para autocompletar
direcciones y geocoding inverso. Convierte texto libre como *"av. España 1234"*
en coordenadas que la app móvil puede usar como origen/destino.

- **Repo:** [trufi-association/trufi-server-photon](https://github.com/trufi-association/trufi-server-photon)
- **Local:** [`../../photon/`](../../photon/) (submódulo, branch `main`)
- **Container:** `photon`
- **Puerto:** `2322` (sin exponer al exterior; va vía YARP)

## Endpoints

- `GET /api?q=<query>` — búsqueda forward
- `GET /api?q=<query>&limit=N` — limitar resultados
- `GET /reverse?lat=<lat>&lon=<lon>` — geocoding inverso

## Datos de entrada

Photon usa un **índice Elasticsearch precomputado** que se descarga de
GraphHopper. **NO se commitea al repo** — son varios GB.

```
photon_data/
└── elasticsearch/
    ├── nodes/...
    └── indices/...
```

El índice se descarga e instala con `init.sh`.

## Configuración

### Variables de entorno

Sin variables custom — la config va en el Dockerfile + `init.sh`.

### País

El índice está atado al país que se descargue. Para Trujillo se usa el
de **Perú** (`pe`). Para cambiar:

```bash
ssh root@trujillo.trufi.dev
cd /root/photon
docker compose down
rm -rf photon_data/
./init.sh   # selecciona el ISO code (ej. `bo`, `us`, `pe`)
docker compose up -d --build
```

### Memoria

Default: `mem_limit: 2g`. Ajustar según tamaño del país:

| País | Memoria sugerida |
|---|---|
| Perú, Bolivia, Ecuador (chico-medio) | 2 GB |
| Brasil, EEUU (grande) | 4-8 GB |

### Healthcheck

```yaml
test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:2322/api?q=test"]
interval: 30s
timeout: 10s
retries: 3
start_period: 60s
```

## Despliegue

### Primera vez (descarga del índice)

```bash
ssh root@trujillo.trufi.dev
cd /root/photon

./init.sh                          # descarga interactiva del índice
docker compose up -d --build
```

> ⚠️ El download del índice puede tardar varios minutos (depende del país y la red).

### Reinicio sin tocar datos

```bash
ssh root@trujillo.trufi.dev 'cd /root/photon && docker compose restart'
```

### Actualizar el índice

GraphHopper publica índices nuevos periódicamente (incluyen cambios de OSM).

```bash
ssh root@trujillo.trufi.dev
cd /root/photon
docker compose down
rm -rf photon_data/
./init.sh   # selecciona PE de nuevo, baja la última versión
docker compose up -d --build
```

## Observabilidad

```bash
# Estado del container
docker ps --filter name=photon

# Logs
docker logs -f photon

# Probar geocoding
curl 'http://localhost:2322/api?q=plaza+de+armas+trujillo&limit=5'
```

## Troubleshooting

### El container se cuelga al arrancar
Suele ser falta de RAM al cargar el índice. Subir `mem_limit` en el compose.

### Resultados pobres / sin resultados
- Revisar que el país sea el correcto (PE para Trujillo).
- Photon depende de la calidad del OSM en la zona — si el barrio está poco
  mapeado, no van a aparecer direcciones.

### Disco lleno
El índice puede ser grande (varios GB). Verificar con `du -sh photon_data`.
