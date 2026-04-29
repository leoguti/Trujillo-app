# web-landing

Página web pública del proyecto. La que se sirve en `https://trujillo.trufi.dev/`
cuando alguien entra desde un browser. Apunta a las tiendas (Google Play /
App Store) y muestra los socios del proyecto.

- **Container:** `web-landing`
- **Imagen:** `nginx:alpine`
- **Puerto:** `80` (interno; expuesto vía YARP)
- **Stack:** HTML + CSS + JS vanilla, sin framework

## Estructura

```
web-landing/
├── docker-compose.yml
├── nginx.conf            # config simple de nginx
├── trufi-proxy.json      # registro en YARP
├── index.html            # markup principal
├── style.css
├── l10n/
│   ├── es.json           # traducciones español
│   └── en.json           # traducciones inglés
├── app-logo.png
├── MPT-logo-04.png       # logos de socios
├── MTC-logo.png
├── PROMOVILIDAD-logo.png
├── GIZ-logo.jpg
├── SECO-logo.jpg
├── appstore.png          # badges de tiendas
└── googleplay.png
```

## Configuración

### nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
}
```

### trufi-proxy.json

```json
{
  "name": "web-landing",
  "description": "Static landing page for Trujillo MiRuta app",
  "container": "web-landing",
  "port": 80,
  "analytics": false
}
```

> `analytics: false` — no se loggean los accesos a la landing en la DB
> (al contrario de OTP/photon/tileserver, que sí se loggean).

## Despliegue

```bash
ssh root@trujillo.trufi.dev
cd /root/web-landing
docker compose up -d
```

> No requiere build; usa `nginx:alpine` directamente y monta los archivos.

## Cambios al contenido

Editar localmente en este folder, commitear, luego sincronizar al server:

```bash
# Opción A: rsync manual
rsync -avz --exclude='.git' \
  ./server/web-landing/ \
  root@trujillo.trufi.dev:/root/web-landing/

# Opción B: pullear en el server (si tenés git ahí — en este server no aplica
# porque /root/web-landing no es un repo git; está como copia plana)
```

Después en el server:

```bash
ssh root@trujillo.trufi.dev 'cd /root/web-landing && docker compose restart'
```

> Cambios en `index.html`/`style.css`/`l10n/*` no necesitan rebuild — nginx
> los lee del volumen montado al instante. Pero conviene reiniciar para
> evitar cache del browser.

## Internacionalización (l10n)

`l10n/es.json` y `l10n/en.json` contienen los textos. El JS de `index.html`
detecta el idioma del browser y aplica las traducciones.

Para agregar idioma:

1. Crear `l10n/<código>.json` (ej. `qu.json` para quechua) con las mismas keys
2. Agregar el botón en el toggle del header

## Observabilidad

```bash
docker ps --filter name=web-landing
docker logs -f web-landing

# Probar localmente desde el server
curl -I http://localhost/   # (vía YARP que proxea al container)
```

## Troubleshooting

### Cambios no se reflejan
nginx + browser cache. Probar:
- Hard reload (Cmd+Shift+R)
- Reiniciar el container
- Verificar que el volume del compose está apuntando al folder correcto

### Logos rotos
Verificar nombres exactos (case-sensitive en el server). Y que están en
el volume mount (`./html` según el compose actual — **revisar discrepancia**:
los archivos están en la raíz del folder, no en `html/`. Si nginx no
sirve, probablemente el mount necesita ajuste).

### Discrepancia de paths (estado actual)

El `docker-compose.yml` monta `./html:/usr/share/nginx/html:ro`, pero los
archivos están en la raíz de la carpeta, no en `./html/`. En el server
puede estar resuelto de otra forma (symlink, sub-folder real). Pendiente
de verificar/normalizar.
