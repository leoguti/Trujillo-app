# 🗺️ Visualizador de Trips - GTFS Trujillo

## ✨ Características

El visualizador actualizado permite:

- ✅ **Seleccionar cualquier ruta** de las 79 disponibles
- ✅ **Ver todos los trips** de una ruta (210 trips totales)
- ✅ **Visualizar la geometría** de la ruta en el mapa
- ✅ **Mostrar todas las paradas** asignadas con números de secuencia
- ✅ **Diferenciar paradas sintéticas** (amarillo) de regulares (verde)
- ✅ **Toggle para ocultar/mostrar paradas**
- ✅ **Popups con información** de cada parada
- ✅ **Estadísticas en tiempo real** por trip

## 📊 Datos Incluidos

- **210 trips** completos
- **2,180 paradas** únicas
- **79 rutas** diferentes
- **Geometrías completas** de todas las shapes
- **Paradas sintéticas** identificadas (415 total)

## 🚀 Cómo Usar

### Opción 1: Abrir directamente
```bash
# En navegador, abrir:
file:///home/leonardo-gutierrez/GTFSTRUJILLO/GTFSv2/trips_visualizer.html
```

### Opción 2: Servidor local
```bash
cd /home/leonardo-gutierrez/GTFSTRUJILLO/GTFSv2
python3 -m http.server 8000
# Luego abrir: http://localhost:8000/trips_visualizer.html
```

## 🎯 Uso del Visualizador

1. **Seleccionar Ruta**: Elegir una ruta del dropdown (ej: M-01 C, C-15 P1)
2. **Seleccionar Trip**: Elegir un trip específico de esa ruta
3. **Ver en Mapa**: 
   - Línea azul = Ruta del trip
   - Círculos verdes = Paradas regulares
   - Círculos amarillos = Paradas sintéticas
   - Números blancos = Secuencia de paradas
4. **Interactuar**:
   - Click en parada = Ver información (stop_id, nombre, secuencia)
   - Botón "Ocultar Paradas" = Toggle de visibilidad
   - Panel de estadísticas = Info del trip actual

## 📁 Archivos

- `trips_visualizer.html` - **7.6 MB** - Visualizador interactivo
- `trip_[id]_stops.json` - 210 archivos con datos de cada trip
- `stops_with_ids_final.json` - Master de todas las paradas

## 🎨 Leyenda

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Parada regular |
| 🟡 Amarillo | Parada sintética (generada) |
| 🔵 Azul | Geometría de la ruta |

## ⚡ Rendimiento

- Tamaño: 7.6 MB (incluye todos los datos inline)
- Carga: ~2-3 segundos en navegadores modernos
- Rendering: Optimizado para 100+ paradas por trip

## 🔧 Tecnologías

- **Leaflet.js** - Visualización de mapas
- **OpenStreetMap** - Tiles de mapa base
- **JavaScript vanilla** - Lógica de interacción
- **CSS3** - Estilos responsivos

## 📝 Notas

- El visualizador contiene TODOS los datos inline (no requiere archivos externos)
- Funciona offline después de la primera carga
- Compatible con Chrome, Firefox, Safari, Edge

---
**Generado**: 2026-01-09  
**Trips incluidos**: 210/210  
**Estado**: ✅ Funcional
