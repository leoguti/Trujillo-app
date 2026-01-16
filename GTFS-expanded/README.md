# GTFS Trujillo

Proyecto para generar archivos GTFS del sistema de transporte público de Trujillo, Perú usando OpenStreetMap.

## Estructura

```
GTFS/
├── src/                    # Scripts TypeScript
│   └── trujillo.ts        # Script principal de generación
├── trufi-gtfs-builder/     # Submódulo del generador GTFS
├── out/                    # Archivos GTFS generados
│   └── trujillo/
├── ignored_routes.txt      # Rutas excluidas del GTFS
├── package.json
└── tsconfig.json
```

## Instalación

```bash
cd GTFS
npm install
```

## Uso

### Generar GTFS

```bash
npm start
```

### Rutas ignoradas

Para excluir rutas específicas del GTFS, añade sus IDs de relación OSM al archivo `ignored_routes.txt`:

```txt
# Rutas ignoradas del GTFS de Trujillo
# Una ID de relación OSM por línea
# Las líneas que comienzan con # son comentarios

19962318
19962323
19972501
19972495
```

Las rutas en este archivo serán excluidas automáticamente durante la generación del GTFS.

## Salida

Los archivos GTFS se generan en:
```
GTFS/out/trujillo/
├── gtfs/                  # Archivos GTFS estándar
│   ├── agency.txt
│   ├── routes.txt
│   ├── trips.txt
│   ├── stops.txt
│   ├── stop_times.txt
│   ├── shapes.txt
│   ├── calendar.txt
│   ├── frequencies.txt
│   ├── fare_attributes.txt
│   ├── fare_rules.txt
│   └── feed_info.txt
├── routes/                # GeoJSON por ruta individual
├── trujillo.gtfs.zip      # GTFS comprimido
├── stops.json             # Información de paradas
├── log.json               # Log de procesamiento
└── README.md              # Documentación generada
```

## Configuración

El sistema de transporte de Trujillo está configurado con:
- **Zona horaria:** `America/Lima`
- **Moneda:** `PEN` (Soles peruanos)
- **Horario:** Lunes-Domingo, 05:00-23:00
- **Frecuencia:** 5 minutos (300 segundos)
- **Velocidad promedio:** 24 km/h
- **Distancia entre paradas sintéticas:** 100 metros
- **Filtro:** Solo rutas con tag `hash=*` en OSM
- **Rutas activas:** ~210 rutas (excluyendo las ignoradas)
- **Paradas sintéticas:** ~6,400 paradas generadas automáticamente

## Fuente de datos

Los datos provienen de OpenStreetMap:
- **Archivo PBF:** `rutas_trujillo.pbf` (ubicado en la raíz del proyecto)
- **Área:** Trujillo, Perú
- **Tipos de transporte:** bus, share_taxi, minibus
