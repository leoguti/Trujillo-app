/**
 * Peru - Trujillo
 * GTFS generation script
 * Filters routes with hash=* tag
 */

import { osmToGtfs, OSMPBFReader } from '../trufi-gtfs-builder';
import * as path from 'path';

async function main() {
  console.log('Starting GTFS generation for Trujillo, Peru...');
  console.log('Using PBF file: /home/leonardo-gutierrez/GTFSTRUJILLO/rutas_trujillo.pbf');
  console.log('Filtering routes with hash=* tag only');

  const pbfPath = '/home/leonardo-gutierrez/GTFSTRUJILLO/rutas_trujillo.pbf';

  // Check if PBF file exists
  if (!require('fs').existsSync(pbfPath)) {
    throw new Error(`PBF file not found: ${pbfPath}`);
  }

  // Create a custom reader to log what's being loaded
  const reader = new OSMPBFReader(pbfPath);
  console.log('\nLoading data from PBF...');

  // Test loading to see what we have
  const testRoutes = await reader.getRoutes(['bus', 'share_taxi', 'minibus']);
  const testWays = await reader.getWays();
  const testStops = await reader.getStops();

  console.log(`Found in PBF: ${Object.keys(testRoutes).length} routes, ${Object.keys(testWays).length} ways, ${Object.keys(testStops).length} stops`);

  // Count routes with hash
  let routesWithHash = 0;
  for (const routeId in testRoutes) {
    const route = testRoutes[routeId];
    if (route.tags && route.tags.hash !== undefined) {
      routesWithHash++;
    }
  }
  console.log(`Routes with hash tag: ${routesWithHash}\n`);

  try {
    await osmToGtfs({
      outputFiles: {
        outputDir: path.join(__dirname, '..', 'out', 'trujillo'),
        gtfs: true,
        gtfsZip: true,
        readme: true,
        routes: true,  // Export routes as GeoJSON for debugging
        stops: true,   // Export stops as GeoJSON for debugging
        log: true,     // Export log file for debugging
      },
      geojsonOptions: {
        osmDataGetter: new OSMPBFReader(pbfPath),
        transformTypes: ['bus', 'share_taxi', 'minibus'],
        skipRoute: (route: any) => {
          // The code does: if (!skipRoute(route)) continue;
          // So: skipRoute=true → process route, skipRoute=false → skip route
          // We want to process routes WITH hash tag
          const hasHash = route.tags && route.tags.hash !== undefined;
          return hasHash; // Return true when hash exists, so route gets processed
        },
      },
      gtfsOptions: {
        agencyTimezone: 'America/Lima',
        agencyUrl: 'https://www.trujillo.gob.pe/',
        cityName: 'trujillo',
        defaultCalendar: () => 'Mo-Su 05:00-23:00',
        frequencyHeadway: () => 300, // 5 minutes
        vehicleSpeed: () => 24,
        skipStopsWithinDistance: 100, // 100 meters between stops
        fakeStops: (routeFeature: any) => false, // Generate synthetic stops from route geometry
        stopNameBuilder: (stops: any) => {
          if (!stops || stops.length === 0) {
            stops = ['Sin nombre'];
          }
          return stops.join(' y ');
        },
        defaultFares: { currencyType: 'PEN' },
        feed: {
          publisherUrl: 'https://trufi-association.org',
          publisherName: 'Trufi Association',
          lang: 'es',
          version: new Date().toUTCString(),
          contactEmail: 'contact@trufi-association.org',
          contactUrl: 'https://trufi-association.org',
          startDate: '20251222',
          endDate: '20261221',
          id: 'trujillo-peru',
        },
      },
    });

    console.log('✅ GTFS generation completed successfully!');
    console.log(`📁 Output files are in: ${path.join(__dirname, '..', 'out', 'trujillo')}`);
  } catch (error) {
    console.error('❌ Error generating GTFS:', error);
    process.exit(1);
  }
}

// Run the script
main();
