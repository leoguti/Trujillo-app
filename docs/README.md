# `docs/` · Presentación de MiRuta Trujillo

Presentación web tipo PowerPoint. HTML estático, sin build step, lista para **GitHub Pages**.

## Vista previa local

```bash
# desde la raíz del repo
python3 -m http.server -d docs 8000
# abre http://localhost:8000
```

## Cómo navegar

| Acción | Tecla / gesto |
|---|---|
| Siguiente slide | `→` `↓` `Espacio` `PageDown` · click siguiente · swipe izq |
| Anterior slide | `←` `↑` `PageUp` · click anterior · swipe der |
| Inicio / fin | `Home` / `End` |
| Vista general (todas las slides) | `Esc` · botón cuadrícula |
| Pantalla completa | `F` · botón fullscreen |
| Saltar a slide N | tecla numérica `1`–`9` |
| Cambiar tema | botón sol/luna |
| Compartir slide específico | URL con hash, ej. `…/#5` |

## Slides

1. **Cover** — título y socios
2. **¿Qué es MiRuta?** — resumen + screenshots
3. **Arquitectura** — diagrama Mermaid del sistema
4. **Servicios** — 6 cards con OTP, gtfs-rt-proxy, photon, etc.
5. **Pipeline GTFS-RT** — flujo paso a paso
6. **El truco del trip_id** — código del enrich
7. **App móvil** — galería de screenshots
8. **Operaciones** — deploy, monitoreo
9. **Cifras** — números del sistema
10. **Cierre** — gracias y contacto

## Publicar en GitHub Pages

1. **Settings → Pages**
2. **Build and deployment → Source**: `Deploy from a branch`
3. **Branch**: `main`, **Folder**: `/docs`
4. Listo en 1–2 minutos en `https://leoguti.github.io/GTFS-Trujillo/`

Para dominio custom (ej. `docs.trujillo.trufi.dev`):
- Registro `CNAME` apuntando a `leoguti.github.io`
- Settings → Pages → Custom domain → escribir el dominio
- Activar `Enforce HTTPS` cuando se valide

## Estructura

```
docs/
├── index.html         markup de las 10 slides
├── styles.css         design system + animaciones
├── app.js             nav, hash routing, overview, fullscreen, Mermaid
├── assets/
│   ├── brand/         app-logo, logo SVG
│   ├── logos/         logos de socios
│   └── screenshots/   capturas iPhone
└── README.md          este archivo
```

## Editar contenido

- **Texto y secciones**: `index.html`, cada slide es `<section class="slide" data-slide="N">`
- **Diagrama de arquitectura**: bloque `<pre class="mermaid">` en slide 3 ([sintaxis](https://mermaid.js.org/syntax/flowchart.html))
- **Colores**: variables CSS al inicio de `styles.css` (`--accent`, `--grad-1`, etc.)
- **Agregar slide nueva**: copiar un `<section class="slide">`, ajustar `data-slide` y `data-title`, incrementar el conteo

## Atajos del presentador

- Compartir slide específica: copiar la URL con `#N` (ej. `https://…/#5`)
- Bypass del idle: el "hint" inferior se desvanece tras 4s de inactividad
- Modo presentador: presionar `F` para fullscreen y `Esc` para vista general
