# TileServer GL — Mapas vectoriales

Sirve los **vector tiles** que renderiza la app móvil. Una sola .mbtiles
contiene toda la cartografía de Trujillo en formato Mapbox Vector Tiles.

- **Repo:** [trufi-association/trufi-server-tileserver-gl](https://github.com/trufi-association/trufi-server-tileserver-gl)
- **Local:** [`../../tileserver-gl/`](../../tileserver-gl/) (submódulo, branch `main`)
- **Container:** `trufi-tileserver-gl`
- **Imagen:** `maptiler/tileserver-gl:latest`
- **Puerto:** `80` (interno; expuesto vía YARP)

## Endpoints

- `GET /` — UI web del tileserver
- `GET /styles/<style>/{z}/{x}/{y}.png` — raster
- `GET /styles/<style>.json` — style JSON
- `GET /data/<source>/{z}/{x}/{y}.pbf` — vector tiles directos
- `GET /health` — healthcheck

## Estilos disponibles

```
data/styles/
├── osm-bright/
├── maptiler-basic/
├── osm-liberty/
├── positron/
├── dark-matter/
└── fiord-color/
```

Cada uno con su `style.json`. La app móvil consume `osm-bright` por defecto.

## Datos de entrada

| Archivo | Tamaño | En el repo |
|---|---|---|
| `trujillo.mbtiles` | 4.7 MB | [`server/data/trujillo.mbtiles`](../../data/trujillo.mbtiles) |

> Hay **dos** copias en el server: `/root/tileserver-gl/data/trujillo.mbtiles`
> (la real, 4.8 MB) y `/root/tileserver-gl/trujillo.mbtiles` (un stub
> antiguo de 536 KB). Solo la primera se usa. Limpieza pendiente.

### Cómo se generó

Con [trufi-mbtiles-generator](https://github.com/trufi-association/trufi-mbtiles-generator)
desde el OSM extract, o con [OpenMapTiles](https://openmaptiles.org/) directamente.
El repo de tileserver-gl tiene instrucciones detalladas.

## Configuración

`data/config.json` define qué fuentes y estilos sirve. Ejemplo:

```json
{
  "options": { "paths": { "root": "/data" } },
  "data": { "trujillo": { "mbtiles": "trujillo.mbtiles" } },
  "styles": {
    "osm-bright": { "style": "styles/osm-bright/style.json" }
  }
}
```

## Despliegue

### Primera vez

```bash
ssh root@trujillo.trufi.dev
cd /root/tileserver-gl

# Setup interactivo (define bbox y mbtiles)
./init.sh BBOX=-79.10,-8.20,-78.96,-8.05 /path/to/trujillo.mbtiles

docker compose up -d --build
```

### Cambio del .mbtiles

```bash
# Subir el nuevo desde el repo
scp server/data/trujillo.mbtiles \
  root@trujillo.trufi.dev:/root/tileserver-gl/data/

# Reiniciar
ssh root@trujillo.trufi.dev 'cd /root/tileserver-gl && docker compose restart'
```

### Cambio de estilo

Editar el `style.json` correspondiente o agregar uno nuevo en `data/styles/`,
luego reiniciar el container.

## Observabilidad

```bash
docker ps --filter name=trufi-tileserver-gl
docker logs -f trufi-tileserver-gl
curl http://localhost:80/health   # desde dentro del server
```

## Troubleshooting

### Healthcheck unhealthy pero el servicio responde
Es el caso actual — el script interno `node healthcheck.js` falla pero
`GET /` responde 200. El servicio funciona; el chequeo es lo roto.

### Tiles no aparecen en la app
- Verificar que la URL del tile en la app apunte al dominio correcto
- Confirmar el estilo: la app consume el JSON, no las tiles directas
- Revisar que el `.mbtiles` tenga el bbox de Trujillo

### Bots escaneando vulnerabilidades
Los logs muestran muchos GETs a `.env`, `.git/config`, etc. Es ruido normal
en internet abierta. El tileserver no expone esos archivos. Considerar fail2ban
si molesta en logs.
