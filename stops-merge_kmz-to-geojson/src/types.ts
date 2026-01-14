/**
 * Types for KMZ to GeoJSON conversion
 */

/** Coordinates in [longitude, latitude] format */
export type Coordinates = [number, number];

/** GeoJSON Point geometry */
export interface PointGeometry {
  type: 'Point';
  coordinates: Coordinates;
}

/** Parsed description fields from HTML */
export interface ParsedDescription {
  [key: string]: string | undefined;
}

/** Stop properties with dynamic fields from description */
export interface StopProperties {
  /** Unique stop identifier */
  stop_id: string;
  /** Human-readable stop name */
  stop_name: string;
  /** Source file (optional) */
  source_file?: string;
  /** Additional dynamic fields parsed from description */
  [key: string]: string | undefined;
}

/** GeoJSON Feature for a stop */
export interface StopFeature {
  type: 'Feature';
  properties: StopProperties;
  geometry: PointGeometry;
}

/** GeoJSON FeatureCollection with stops */
export interface StopsFeatureCollection {
  type: 'FeatureCollection';
  features: StopFeature[];
}

/** Conversion configuration options */
export interface ConversionOptions {
  /** Input directory containing KMZ files */
  inputDir: string;
  /** Output directory for GeoJSON files */
  outputDir: string;
  /** Generate a combined file with all stops */
  combineOutput?: boolean;
  /** Combined file name (default: 'all_stops.geojson') */
  combinedFileName?: string;
  /** Include source file name in properties */
  includeSourceFile?: boolean;
  /** Prefix for generated stop_id values */
  stopIdPrefix?: string;
}

/** Placemark extracted from KML */
export interface KmlPlacemark {
  name?: string;
  description?: string;
  coordinates?: string;
  Point?: {
    coordinates?: string;
  };
}

/** Conversion result for a single file */
export interface ConversionResult {
  /** Processed file name */
  fileName: string;
  /** Number of stops found */
  stopsCount: number;
  /** Resulting FeatureCollection */
  featureCollection: StopsFeatureCollection;
  /** Errors encountered (if any) */
  errors?: string[];
}
