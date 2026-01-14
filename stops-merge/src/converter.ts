/**
 * KMZ/KML to GeoJSON Conversion Module
 *
 * This module provides functions to extract data from KMZ and KML files
 * and convert them to GeoJSON format with stop/station structure.
 *
 * Supports:
 * - KMZ files (zipped KML, typically from ESRI/ArcGIS)
 * - KML files with HTML descriptions (ESRI format)
 * - KML files with ExtendedData (OSM/overpass-turbo format)
 *
 * @example
 * ```typescript
 * import { convertToGeoJson, convertDirectory } from './converter';
 *
 * // Convert a single file (KMZ or KML)
 * const result = await convertToGeoJson('input/file.kmz');
 * const result2 = await convertToGeoJson('input/file.kml');
 *
 * // Convert all files in a directory
 * const results = await convertDirectory({
 *   inputDir: './input',
 *   outputDir: './out',
 *   combineOutput: true
 * });
 * ```
 */

import AdmZip from 'adm-zip';
import { XMLParser } from 'fast-xml-parser';
import * as fs from 'fs';
import * as path from 'path';
import {
  StopsFeatureCollection,
  StopFeature,
  StopProperties,
  Coordinates,
  ConversionOptions,
  ConversionResult,
  KmlPlacemark,
  ParsedDescription
} from './types';

/**
 * Normalizes a field name to snake_case
 *
 * @param fieldName - Original field name (possibly in Spanish with spaces)
 * @returns Normalized snake_case field name
 */
export function normalizeFieldName(fieldName: string): string {
  return fieldName
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove accents
    .replace(/[^a-z0-9\s]/g, '')     // Only alphanumeric and spaces
    .trim()
    .replace(/\s+/g, '_');           // Spaces to underscores
}

/**
 * Parses HTML description from ESRI/ArcGIS KML export
 * Extracts key-value pairs from HTML tables
 *
 * @param html - HTML string from KML description
 * @returns Object with parsed field values
 */
export function parseHtmlDescription(html: string | undefined): ParsedDescription {
  if (!html) return {};

  const result: ParsedDescription = {};

  // Match table rows with two cells: <td>key</td><td>value</td>
  // This regex handles the ESRI HTML table format
  const rowRegex = /<tr[^>]*>\s*<td[^>]*>([^<]+)<\/td>\s*<td[^>]*>([^<]*)<\/td>\s*<\/tr>/gi;

  let match;
  while ((match = rowRegex.exec(html)) !== null) {
    const key = match[1].trim();
    let value = match[2].trim();

    // Skip empty keys or Field## placeholders with null values
    if (!key || key.startsWith('Field') || value === '&lt;Null&gt;' || value === '<Null>') {
      continue;
    }

    // Decode HTML entities
    value = value
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");

    // Skip null values
    if (value === '<Null>' || value === 'Null' || !value) {
      continue;
    }

    const normalizedKey = normalizeFieldName(key);
    if (normalizedKey) {
      result[normalizedKey] = value;
    }
  }

  return result;
}

/**
 * Generates a stop_id from the stop name
 *
 * @param name - Stop name
 * @param index - Numeric index as fallback
 * @param prefix - Optional ID prefix
 * @returns Normalized stop ID
 */
export function generateStopId(name: string | undefined, index: number, prefix?: string): string {
  if (!name) {
    return `${prefix || 'STOP'}_${String(index).padStart(3, '0')}`;
  }

  // Normalize the name to create a valid ID
  const normalized = name
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove accents
    .replace(/[^A-Z0-9\s]/g, '')     // Only alphanumeric and spaces
    .trim()
    .replace(/\s+/g, '_')            // Spaces to underscores
    .substring(0, 30);               // Limit length

  if (!normalized) {
    return `${prefix || 'STOP'}_${String(index).padStart(3, '0')}`;
  }

  return prefix ? `${prefix}_${normalized}` : normalized;
}

/**
 * Parses a KML coordinate string to GeoJSON format
 *
 * KML uses format: "longitude,latitude,altitude" (altitude is optional)
 * GeoJSON uses format: [longitude, latitude]
 *
 * @param coordString - Coordinate string in KML format
 * @returns Coordinates in GeoJSON format or null if invalid
 */
export function parseCoordinates(coordString: string | undefined): Coordinates | null {
  if (!coordString) return null;

  const cleaned = coordString.trim();
  const parts = cleaned.split(',').map(p => parseFloat(p.trim()));

  if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1])) {
    return null;
  }

  // GeoJSON: [longitude, latitude]
  return [parts[0], parts[1]];
}

/**
 * Extracts KML content from a KMZ file
 *
 * KMZ files are ZIP archives containing a doc.kml file
 *
 * @param kmzPath - Path to the KMZ file
 * @returns KML file content as string
 */
export function extractKmlFromKmz(kmzPath: string): string {
  const zip = new AdmZip(kmzPath);
  const entries = zip.getEntries();

  // Find the KML file (usually doc.kml)
  const kmlEntry = entries.find(entry =>
    entry.entryName.toLowerCase().endsWith('.kml')
  );

  if (!kmlEntry) {
    throw new Error(`No KML file found inside: ${kmzPath}`);
  }

  return kmlEntry.getData().toString('utf8');
}

/**
 * Reads KML content directly from a KML file
 *
 * @param kmlPath - Path to the KML file
 * @returns KML file content as string
 */
export function readKmlFile(kmlPath: string): string {
  return fs.readFileSync(kmlPath, 'utf8');
}

/**
 * Parses ExtendedData from OSM/overpass-turbo style KML
 * Extracts key-value pairs from <Data name="key"><value>val</value></Data>
 *
 * @param extendedData - ExtendedData object from parsed KML
 * @returns Object with parsed field values
 */
export function parseExtendedData(extendedData: any): ParsedDescription {
  if (!extendedData) return {};

  const result: ParsedDescription = {};
  let dataItems = extendedData.Data;

  if (!dataItems) return result;

  // Ensure it's an array
  if (!Array.isArray(dataItems)) {
    dataItems = [dataItems];
  }

  for (const item of dataItems) {
    // Get the name attribute (could be @_name or name depending on parser config)
    const name = item['@_name'] || item.name;
    if (!name) continue;

    // Get the value
    let value = item.value;
    if (value === undefined || value === null) continue;

    // Convert to string if needed
    value = String(value).trim();
    if (!value) continue;

    // Skip internal OSM metadata fields starting with @
    if (name.startsWith('@')) continue;

    const normalizedKey = normalizeFieldName(name);
    if (normalizedKey) {
      result[normalizedKey] = value;
    }
  }

  return result;
}

/**
 * Extracts all Placemarks from a parsed KML object
 *
 * @param kmlObject - Parsed KML object
 * @returns Array of found placemarks
 */
function extractPlacemarks(obj: any): KmlPlacemark[] {
  const placemarks: KmlPlacemark[] = [];

  function addPlacemark(p: any): void {
    if (p.Point) {
      placemarks.push({
        name: p.name,
        description: p.description,
        Point: p.Point,
        ExtendedData: p.ExtendedData
      });
    }
  }

  function traverse(current: any): void {
    if (!current || typeof current !== 'object') return;

    if (Array.isArray(current)) {
      current.forEach(item => traverse(item));
      return;
    }

    // If we find a Placemark with Point, add it
    if (current.Point) {
      addPlacemark(current);
    }

    // Traverse all properties
    for (const key of Object.keys(current)) {
      if (key === 'Placemark') {
        const pm = current[key];
        if (Array.isArray(pm)) {
          pm.forEach(p => addPlacemark(p));
        } else if (pm) {
          addPlacemark(pm);
        }
      } else {
        traverse(current[key]);
      }
    }
  }

  traverse(obj);
  return placemarks;
}

/**
 * Determines file type from extension
 */
function getFileType(filePath: string): 'kmz' | 'kml' | null {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.kmz') return 'kmz';
  if (ext === '.kml') return 'kml';
  return null;
}

/**
 * Converts a KMZ or KML file to GeoJSON
 *
 * @param filePath - Path to the KMZ or KML file
 * @param options - Conversion options
 * @returns Conversion result with FeatureCollection
 */
export async function convertToGeoJson(
  filePath: string,
  options?: Partial<ConversionOptions>
): Promise<ConversionResult> {
  const fileType = getFileType(filePath);
  const ext = fileType === 'kmz' ? '.kmz' : '.kml';
  const fileName = path.basename(filePath, ext);
  const errors: string[] = [];
  const features: StopFeature[] = [];

  try {
    // Get KML content based on file type
    let kmlContent: string;
    if (fileType === 'kmz') {
      kmlContent = extractKmlFromKmz(filePath);
    } else if (fileType === 'kml') {
      kmlContent = readKmlFile(filePath);
    } else {
      throw new Error(`Unsupported file type: ${filePath}`);
    }

    // Parse the XML
    const parser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
      textNodeName: '#text'
    });

    const kmlObject = parser.parse(kmlContent);

    // Extract all placemarks
    const placemarks = extractPlacemarks(kmlObject);

    // Convert each placemark to feature
    placemarks.forEach((placemark, index) => {
      const coordString = placemark.Point?.coordinates;
      const coordinates = parseCoordinates(coordString);

      if (!coordinates) {
        errors.push(`Placemark "${placemark.name || index}" has no valid coordinates`);
        return;
      }

      // Parse fields from HTML description OR ExtendedData
      let parsedFields = parseHtmlDescription(placemark.description);

      // If no fields from HTML, try ExtendedData (OSM/overpass-turbo format)
      if (Object.keys(parsedFields).length === 0 && placemark.ExtendedData) {
        parsedFields = parseExtendedData(placemark.ExtendedData);
      }

      // Use codigo_paradero if available, otherwise generate from name
      const stopCode = parsedFields.codigo_de_paradero || parsedFields.codigo;
      const stopId = stopCode
        ? generateStopId(stopCode, index + 1, options?.stopIdPrefix)
        : generateStopId(placemark.name, index + 1, options?.stopIdPrefix);

      // Use nombre_popular or nombre_de_via if available
      const stopName = parsedFields.nombre_popular_del_paradero
        || parsedFields.nombre_de_via
        || placemark.name
        || `Stop ${index + 1}`;

      const properties: StopProperties = {
        stop_id: stopId,
        stop_name: stopName,
        ...parsedFields  // Spread all parsed fields
      };

      if (options?.includeSourceFile) {
        properties.source_file = fileName;
      }

      const feature: StopFeature = {
        type: 'Feature',
        properties,
        geometry: {
          type: 'Point',
          coordinates
        }
      };

      features.push(feature);
    });

  } catch (error) {
    errors.push(`Error processing ${filePath}: ${error}`);
  }

  const featureCollection: StopsFeatureCollection = {
    type: 'FeatureCollection',
    features
  };

  return {
    fileName,
    stopsCount: features.length,
    featureCollection,
    errors: errors.length > 0 ? errors : undefined
  };
}

/**
 * Converts a KMZ file to GeoJSON (legacy alias for convertToGeoJson)
 * @deprecated Use convertToGeoJson instead
 */
export async function convertKmzToGeoJson(
  kmzPath: string,
  options?: Partial<ConversionOptions>
): Promise<ConversionResult> {
  return convertToGeoJson(kmzPath, options);
}

/**
 * Converts all KMZ and KML files in a directory
 *
 * @param options - Conversion options
 * @returns Array with results for each file
 */
export async function convertDirectory(
  options: ConversionOptions
): Promise<ConversionResult[]> {
  const { inputDir, outputDir, combineOutput, combinedFileName, includeSourceFile } = options;

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Get list of KMZ and KML files
  const files = fs.readdirSync(inputDir)
    .filter(file => {
      const lower = file.toLowerCase();
      return lower.endsWith('.kmz') || lower.endsWith('.kml');
    });

  if (files.length === 0) {
    console.log('⚠️  No KMZ or KML files found in input directory');
    return [];
  }

  const kmzCount = files.filter((f: string) => f.toLowerCase().endsWith('.kmz')).length;
  const kmlCount = files.filter((f: string) => f.toLowerCase().endsWith('.kml')).length;
  console.log(`📁 Found ${files.length} files (${kmzCount} KMZ, ${kmlCount} KML)\n`);

  const results: ConversionResult[] = [];
  const allFeatures: StopFeature[] = [];

  // Process each file
  for (const file of files) {
    const filePath = path.join(inputDir, file);
    console.log(`🔄 Processing: ${file}`);

    const result = await convertToGeoJson(filePath, {
      ...options,
      includeSourceFile: includeSourceFile || combineOutput
    });

    results.push(result);

    // Save individual file
    const outputFileName = result.fileName
      .replace(/\s+/g, '_')
      .toLowerCase() + '.geojson';
    const outputPath = path.join(outputDir, outputFileName);

    fs.writeFileSync(
      outputPath,
      JSON.stringify(result.featureCollection, null, 2),
      'utf8'
    );

    console.log(`   ✅ ${result.stopsCount} stops → ${outputFileName}`);

    if (result.errors && result.errors.length > 0) {
      result.errors.forEach(err => console.log(`   ⚠️  ${err}`));
    }

    // Accumulate features for combined file
    if (combineOutput) {
      allFeatures.push(...result.featureCollection.features);
    }
  }

  // Generate combined file if requested
  if (combineOutput && allFeatures.length > 0) {
    const combinedCollection: StopsFeatureCollection = {
      type: 'FeatureCollection',
      features: allFeatures
    };

    const combinedPath = path.join(outputDir, combinedFileName || 'all_stops.geojson');
    fs.writeFileSync(
      combinedPath,
      JSON.stringify(combinedCollection, null, 2),
      'utf8'
    );

    console.log(`\n📦 Combined file: ${combinedFileName || 'all_stops.geojson'} (${allFeatures.length} stops total)`);
  }

  return results;
}

/**
 * Converts all KMZ files in a directory (legacy alias for convertDirectory)
 * @deprecated Use convertDirectory instead
 */
export async function convertKmzDirectory(
  options: ConversionOptions
): Promise<ConversionResult[]> {
  return convertDirectory(options);
}

/**
 * Combines multiple FeatureCollections into one
 *
 * @param collections - Array of FeatureCollections to combine
 * @returns Combined FeatureCollection
 */
export function combineFeatureCollections(
  collections: StopsFeatureCollection[]
): StopsFeatureCollection {
  const allFeatures = collections.flatMap(c => c.features);

  return {
    type: 'FeatureCollection',
    features: allFeatures
  };
}
