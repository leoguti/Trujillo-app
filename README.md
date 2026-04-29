# MiRuta Trujillo

Sistema de transporte público de Trujillo, Perú: app móvil, servidor de planificación de viajes y herramientas para generar el GTFS desde OpenStreetMap.

Producción: [trujillo.trufi.dev](https://trujillo.trufi.dev) · App: [Google Play](https://play.google.com/store/apps/details?id=dev.trufi.trujillo)

## Estructura del repo

| Carpeta | Contenido | Doc |
|---|---|---|
| [mobile-app/](mobile-app/) | App Flutter (Trufi Core 5.5) — Android · iOS · Web | [README](mobile-app/README.md) |
| [server/](server/) | Stack de producción: OTP, YARP, photon, tileserver-gl, gtfs-rt-proxy, landing | [README](server/README.md) |
| [GTFS/](GTFS/) | Generador de GTFS estático desde OSM (TypeScript) | [README](GTFS/README.md) |
| [docs/](docs/) | Presentación HTML del proyecto (estilo PowerPoint, GitHub Pages) | [README](docs/README.md) |

`server/` contiene **submódulos** que apuntan a los repos de cada servicio en `trufi-association`. Ver sección de git abajo.

## Quick start

```bash
# Clonar con submódulos
git clone --recurse-submodules https://github.com/leoguti/GTFS-Trujillo.git
cd GTFS-Trujillo

# App móvil
cd mobile-app && fvm install && fvm flutter pub get && fvm flutter run

# Generar GTFS
cd GTFS && npm install && npm start

# Presentación local
python3 -m http.server -d docs 8000
```

## Comandos git útiles

### Submódulos (`server/otp`, `server/server`, `server/photon`, `server/tileserver-gl`)

```bash
# Clonar trayendo también los submódulos
git clone --recurse-submodules <url>

# Si ya clonaste sin --recurse, inicializarlos ahora
git submodule update --init --recursive

# Traer el último main de cada submódulo
git submodule update --remote --merge

# Ver estado de los submódulos (commit registrado vs HEAD remoto)
git submodule status

# Ejecutar un comando en cada submódulo
git submodule foreach 'git status'
git submodule foreach 'git pull origin main'

# Después de actualizar submódulos, registrar el nuevo commit en el repo padre
git add server/otp server/server server/photon server/tileserver-gl
git commit -m "chore: bump submodules"
```

### Branching y commits

```bash
# Estado y diferencias
git status -sb                 # vista compacta
git diff                       # cambios sin staged
git diff --staged              # cambios en staging
git log --oneline -20          # últimos 20 commits
git log --graph --oneline --all -30

# Crear y cambiar de rama
git switch -c feat/mi-feature
git switch master

# Stash (guardar cambios sin commitear)
git stash push -m "wip"
git stash list
git stash pop

# Deshacer cambios locales sin commitear (cuidado: destructivo)
git restore <archivo>          # un archivo
git restore .                  # todo el working tree
git clean -fd                  # eliminar untracked
```

### Sincronizar con remoto

```bash
git fetch --all --prune        # traer cambios sin mergear, limpiar refs muertas
git pull --rebase              # rebasear sobre el remoto en vez de mergear
git push                       # subir la rama actual
git push -u origin <rama>      # primer push de una rama nueva
```

### Inspección y arqueología

```bash
git log --follow <archivo>     # historia completa, incluso renames
git blame <archivo>            # quién tocó cada línea
git show <hash>                # diff completo de un commit
git log -S "texto"             # commits que añadieron/quitaron "texto"
git log --author="leo"         # filtrar por autor
git diff master...HEAD         # qué tiene mi rama que master no
```

### Recuperación

```bash
git reflog                     # historial completo de HEAD (rescate de commits "perdidos")
git restore --source=<hash> <archivo>   # versión de un archivo en otro commit
git revert <hash>              # crear commit que deshace otro (no destructivo)
```

### Tags y releases

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
git tag -l                     # listar tags
```

## Dominios y enlaces de operación

- **App web / landing:** https://trujillo.trufi.dev
- **OTP:** https://trujillo.trufi.dev/otp/
- **Photon:** https://trujillo.trufi.dev/photon/
- **Tileserver:** https://trujillo.trufi.dev/tileserver/
- **Servidor:** `ssh root@trujillo.trufi.dev` (cada servicio en `/root/<servicio>/`)

Healthcheck rápido y operaciones en [server/docs/operations.md](server/docs/operations.md).

## Créditos

Construido sobre [Trufi Core](https://github.com/trufi-association/trufi-core) y [OpenTripPlanner](https://www.opentripplanner.org/). Datos de [OpenStreetMap](https://www.openstreetmap.org/).
