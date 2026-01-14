# KMZ to GeoJSON Converter

TypeScript library and CLI for converting KMZ (Google Earth) files to GeoJSON format with stop/station structure.

## Installation

```bash
npm install
```

## Quick Start

### CLI

```bash
# Basic conversion (input/ → out/)
npm run convert

# Specify directories
npm run convert -- -i ./my_kmz -o ./result

# With prefix for stop_id
npm run convert -- --prefix TRUJILLO

# Without combined file
npm run convert -- --no-combine
```

### As a Library

```typescript
import {
  convertKmzToGeoJson,
  convertKmzDirectory,
  combineFeatureCollections
} from './src';

// Convert a single file
const result = await convertKmzToGeoJson('./input/file.kmz');
console.log(result.featureCollection);

// Convert entire directory
const results = await convertKmzDirectory({
  inputDir: './input',
  outputDir: './out',
  combineOutput: true,
  includeSourceFile: true,
  stopIdPrefix: 'TRU'
});
```

## Project Structure

```
trujillo-kmz/
├── input/              # Input KMZ files
├── out/                # Generated GeoJSON files
├── src/
│   ├── index.ts        # Main exports
│   ├── types.ts        # Type definitions
│   ├── converter.ts    # Conversion logic
│   └── cli.ts          # Command line interface
├── package.json
├── tsconfig.json
└── README.md
```

## Output Format

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "stop_id": "PM99",
        "stop_name": "PM-99",
        "source_file": "P-Moche",
        "description": "..."
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-78.978, -8.187]
      }
    }
  ]
}
```

## CLI Options

| Option | Alias | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input directory | `./input` |
| `--output` | `-o` | Output directory | `./out` |
| `--combine` | `-c` | Generate combined file | `true` |
| `--no-combine` | | Do not generate combined file | |
| `--prefix` | `-p` | Prefix for stop_id | |
| `--combined-name` | | Name for combined file | `all_stops.geojson` |
| `--help` | `-h` | Show help | |

## API

### `convertKmzToGeoJson(kmzPath, options?)`

Converts a single KMZ file to GeoJSON.

```typescript
const result = await convertKmzToGeoJson('./file.kmz', {
  stopIdPrefix: 'STOP',
  includeSourceFile: true
});
```

### `convertKmzDirectory(options)`

Converts all KMZ files in a directory.

```typescript
const results = await convertKmzDirectory({
  inputDir: './input',
  outputDir: './out',
  combineOutput: true,
  combinedFileName: 'all_stops.geojson',
  includeSourceFile: true,
  stopIdPrefix: 'TRU'
});
```

### `combineFeatureCollections(collections)`

Combines multiple FeatureCollections into one.

```typescript
const combined = combineFeatureCollections([fc1, fc2, fc3]);
```

### Helper Functions

- `generateStopId(name, index, prefix?)` - Generates a normalized ID
- `parseCoordinates(coordString)` - Parses KML coordinates to GeoJSON format
- `extractKmlFromKmz(kmzPath)` - Extracts KML from a KMZ file

## Types

```typescript
interface StopProperties {
  stop_id: string;
  stop_name: string;
  source_file?: string;
  description?: string;
}

interface StopFeature {
  type: 'Feature';
  properties: StopProperties;
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [longitude, latitude]
  };
}

interface StopsFeatureCollection {
  type: 'FeatureCollection';
  features: StopFeature[];
}

interface ConversionOptions {
  inputDir: string;
  outputDir: string;
  combineOutput?: boolean;
  combinedFileName?: string;
  includeSourceFile?: boolean;
  stopIdPrefix?: string;
}

interface ConversionResult {
  fileName: string;
  stopsCount: number;
  featureCollection: StopsFeatureCollection;
  errors?: string[];
}
```

## Development

```bash
# Build TypeScript
npm run build

# Run directly with ts-node
npm run convert
```

## License

MIT
