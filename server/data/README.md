# `server/data/` — Datos de input del servidor

Snapshot de los **inputs canónicos** que alimentan los servicios en
`trujillo.trufi.dev`. Solo están aquí los archivos de los que dependen
los containers y que **no se regeneran solos**. Los archivos derivados
(`graph.obj` de OTP, índice de Photon) **no** se commitean — los servicios
los reconstruyen al arrancar.

## Archivos

| Archivo | Tamaño | Servicio | Origen en el server |
|---|---|---|---|
| `trujillo.gtfs.zip` | 18 MB | `otp` | `/root/otp/data/trujillo.gtfs.zip` |
| `trujillo.osm.pbf` | 2.3 MB | `otp` | `/root/otp/data/trujillo.osm.pbf` |
| `trujillo.mbtiles` | 4.8 MB | `tileserver-gl` | `/root/tileserver-gl/data/trujillo.mbtiles` |

> El `gtfs-rt-proxy` usa una **versión simplificada** del GTFS, que vive
> dentro del propio servicio: [`../gtfs-rt-proxy/data/trujillo.gtfs.zip`](../gtfs-rt-proxy/data/trujillo.gtfs.zip).

## ¿Qué NO está aquí (a propósito)?

| Archivo | Por qué no | Cómo aparece |
|---|---|---|
| `graph.obj` (OTP, ~20 MB) | Lo regenera OTP al levantar, a partir de `trujillo.gtfs.zip` + `trujillo.osm.pbf` | `docker compose up` |
| `photon_data/` (Photon, ~varios GB) | Índice gigantesco de geocoder; se reconstruye con `init.sh` | Ver README de photon |
| Backups `.bak`, demos `kigali.*` | Ruido/legacy en el server | — |

## Refrescar la data desde el server

Cuando el GTFS o el OSM cambien en el server, sincronizá este folder
con `scp`:

```bash
SERVER=root@trujillo.trufi.dev
scp $SERVER:/root/otp/data/trujillo.gtfs.zip          server/data/
scp $SERVER:/root/otp/data/trujillo.osm.pbf           server/data/
scp $SERVER:/root/tileserver-gl/data/trujillo.mbtiles server/data/
scp $SERVER:/root/gtfs-rt-proxy/data/trujillo.gtfs.zip server/gtfs-rt-proxy/data/
```

Después podés commitear los cambios para que el repo siga reflejando
producción.

## Subir data desde el repo al server

Si trabajás en el GTFS localmente y querés desplegarlo, invertí el `scp`:

```bash
SERVER=root@trujillo.trufi.dev
scp server/data/trujillo.gtfs.zip          $SERVER:/root/otp/data/
scp server/data/trujillo.osm.pbf           $SERVER:/root/otp/data/
scp server/data/trujillo.mbtiles           $SERVER:/root/tileserver-gl/data/
scp server/gtfs-rt-proxy/data/trujillo.gtfs.zip $SERVER:/root/gtfs-rt-proxy/data/
```

> **Cuidado:** esto **sobreescribe** los archivos en el server. Asegurate
> de haber probado los cambios en local antes. Si subiste GTFS u OSM,
> hay que reiniciar OTP para regenerar el graph (ver siguiente sección).

## Notas

- Estos archivos son binarios — los diffs de git no son útiles. Si el
  GTFS crece mucho en el futuro considerar [Git LFS](https://git-lfs.com/).
- `trujillo.osm.pbf` viene de un extract de OpenStreetMap del área de
  Trujillo; se puede regenerar con `osmium extract` si hace falta.
- `trujillo.mbtiles` se genera con [Tilemaker](https://github.com/systemed/tilemaker)
  desde el mismo `.osm.pbf`. El proceso está en el repo
  [`trufi-server-tileserver-gl`](https://github.com/trufi-association/trufi-server-tileserver-gl).
