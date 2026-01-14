/**
 * kmz-to-geojson
 *
 * Library for converting KMZ and KML files to GeoJSON format with stop/station structure.
 *
 * Supports:
 * - KMZ files (zipped KML, typically from ESRI/ArcGIS)
 * - KML files with HTML descriptions (ESRI format)
 * - KML files with ExtendedData (OSM/overpass-turbo format)
 *
 * @example
 * ```typescript
 * import {
 *   convertToGeoJson,
 *   convertDirectory,
 *   combineFeatureCollections
 * } from 'kmz-to-geojson';
 *
 * // Convert a single file (KMZ or KML)
 * const result = await convertToGeoJson('./my-file.kmz');
 * const result2 = await convertToGeoJson('./my-file.kml');
 * console.log(result.featureCollection);
 *
 * // Convert entire directory (processes both .kmz and .kml files)
 * const results = await convertDirectory({
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
  convertToGeoJson,
  convertDirectory,
  // Legacy aliases (deprecated)
  convertKmzToGeoJson,
  convertKmzDirectory,
  // Utilities
  combineFeatureCollections,
  generateStopId,
  parseCoordinates,
  extractKmlFromKmz,
  readKmlFile,
  parseHtmlDescription,
  parseExtendedData,
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
