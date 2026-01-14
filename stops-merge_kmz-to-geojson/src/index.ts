/**
 * kmz-to-geojson
 *
 * Library for converting KMZ files to GeoJSON format with stop/station structure.
 *
 * @example
 * ```typescript
 * import {
 *   convertKmzToGeoJson,
 *   convertKmzDirectory,
 *   combineFeatureCollections
 * } from 'kmz-to-geojson';
 *
 * // Convert a single file
 * const result = await convertKmzToGeoJson('./my-file.kmz');
 * console.log(result.featureCollection);
 *
 * // Convert entire directory
 * const results = await convertKmzDirectory({
 *   inputDir: './input',
 *   outputDir: './output',
 *   combineOutput: true,
 *   includeSourceFile: true
 * });
 * ```
 *
 * @packageDocumentation
 */

// Export main functions
export {
  convertKmzToGeoJson,
  convertKmzDirectory,
  combineFeatureCollections,
  generateStopId,
  parseCoordinates,
  extractKmlFromKmz,
  parseHtmlDescription,
  normalizeFieldName
} from './converter';

// Export types
export type {
  Coordinates,
  PointGeometry,
  StopProperties,
  StopFeature,
  StopsFeatureCollection,
  ConversionOptions,
  ConversionResult,
  KmlPlacemark,
  ParsedDescription
} from './types';
