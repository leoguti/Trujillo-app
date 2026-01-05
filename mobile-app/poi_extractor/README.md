# Kigali POI Extractor

Extracts Points of Interest from OpenStreetMap data for the Kigali Mobility app.

## Setup

1. Download the Kigali OSM data (PBF format) and place it in this directory as `kigali.osm.pbf`
2. Install dependencies:

```bash
npm install
```

## Usage

Extract POIs to the app's assets folder:

```bash
npm run extract
```

This will create GeoJSON files in `../assets/pois/` with the following categories:
- transport.geojson
- food.geojson
- shopping.geojson
- healthcare.geojson
- education.geojson
- finance.geojson
- tourism.geojson
- recreation.geojson
- government.geojson
- religion.geojson
- emergency.geojson
- accommodation.geojson

## Data Source

Get the PBF file from:
- Geofabrik: https://download.geofabrik.de/africa/rwanda.html
- BBBike: https://extract.bbbike.org/ (for custom Kigali extract)
