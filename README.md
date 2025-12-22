# GTFS Trujillo

Generador de GTFS para el sistema de transporte público de Trujillo, Perú.

## Descripción

Este proyecto genera archivos GTFS (General Transit Feed Specification) a partir de datos de OpenStreetMap para las rutas de transporte público de Trujillo. Filtra automáticamente solo las rutas que tienen el tag `hash=*` en OSM.

## Basado en Rutometro

Este generador está basado en [Rutometro](https://github.com/trufi-association/rutometro), un proyecto de código abierto desarrollado por Trufi Association para generar archivos GTFS de ciudades usando OpenStreetMap.

**Cambio de estrategia**: A diferencia del Rutometro original que descarga datos directamente desde la API de Overpass, este proyecto utiliza un archivo PBF local pre-filtrado manualmente. Esto permite un procesamiento más rápido y evita problemas de timeout con la API de Overpass.

## Requisitos

- Node.js 18+
- npm
- Archivo PBF con datos de OSM de Trujillo (filtrado con `hash=*`)

## Preparación del archivo PBF

### Consulta Overpass para JOSM

Para obtener los datos de Trujillo desde OpenStreetMap, usa esta consulta en JOSM:

```
[out:xml][timeout:90][bbox:{{bbox}}];
(
  nwr["hash"];
);
(._;>;);
out meta;
```

**Importante**: Esta consulta debe ejecutarse en JOSM con la opción **"Download referrers"** o asegurándose de que `(._;>;);` incluya todos los ways y nodes de las relaciones.

### Exportar desde JOSM

1. Ejecuta la consulta de Overpass en JOSM
2. Verifica que se hayan descargado las relaciones, ways y nodes
3. Exporta como archivo `.osm.pbf`
4. Coloca el archivo en: `/home/leonardo-gutierrez/GTFSTRUJILLO/rutas_trujillo.pbf`

El archivo debe contener:
- **Relaciones** de tipo `route` con tag `hash=*`
- **Ways** (vías) que son miembros de esas relaciones
- **Nodes** (nodos) que componen esos ways

## Instalación

```bash
cd gtfs-trujillo/GTFS
npm install
```

## Uso

Para generar el GTFS de Trujillo:

```bash
npm start
```

El archivo GTFS se generará en: `GTFS/out/trujillo/trujillo.gtfs.zip`

## Configuración

El script está configurado para Trujillo, Perú:

- **Zona horaria**: America/Lima
- **Moneda**: PEN (Soles)
- **Horario de servicio**: Lunes a Domingo, 05:00-23:00
- **Frecuencia**: Cada 5 minutos
- **Velocidad promedio**: 24 km/h
- **Distancia mínima entre paradas**: 100 metros
- **Generación de paradas sintéticas**: Habilitada (crea paradas automáticamente a lo largo de las rutas)

## Archivos generados

El proceso genera:

- **trujillo.gtfs.zip**: Archivo GTFS estándar listo para usar (~1MB)
  - `agency.txt` - Información de la agencia
  - `calendar.txt` - Calendario de servicio
  - `fare_attributes.txt` & `fare_rules.txt` - Tarifas
  - `feed_info.txt` - Metadatos del feed
  - `frequencies.txt` - Frecuencias de servicio
  - `routes.txt` - Rutas
  - `shapes.txt` - Geometrías de las rutas
  - `trips.txt` - Viajes
  - `stops.txt` - Paradas

- **README.md**: Resumen de rutas procesadas con links a OSM
- **log.json**: Log detallado del procesamiento
- **stops.json**: GeoJSON con todas las paradas generadas
- **routes/**: Carpeta con GeoJSON de cada ruta individual
- **gtfs/**: Archivos GTFS individuales

## Estadísticas actuales

- **213 rutas** procesadas
- **212 rutas correctas** ✅
- **1 ruta con error** (sin tag `ref`)
- **~4.5MB** de geometrías de rutas (shapes.txt)

## Tecnologías utilizadas

- [Rutometro](https://github.com/trufi-association/rutometro) - Proyecto base
- [trufi-gtfs-builder](https://github.com/trufi-association/trufi-gtfs-builder) - Librería de generación GTFS
- TypeScript
- Node.js
- OpenStreetMap

## Créditos

- **Trufi Association** - Desarrollo de Rutometro y trufi-gtfs-builder
- **OpenStreetMap contributors** - Datos de transporte público de Trujillo
- Datos bajo licencia ODbL de OpenStreetMap

## Licencia

ISC
