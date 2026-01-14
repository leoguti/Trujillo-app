#!/usr/bin/env node

/**
 * CLI for converting KMZ files to GeoJSON
 *
 * Usage:
 *   npx ts-node src/cli.ts [options]
 *
 * Options:
 *   --input, -i     Input directory (default: ./input)
 *   --output, -o    Output directory (default: ./out)
 *   --combine, -c   Generate combined file (default: true)
 *   --prefix, -p    Prefix for stop_id
 *   --help, -h      Show help
 */

import * as path from 'path';
import { convertKmzDirectory } from './converter';
import { ConversionOptions } from './types';

function printHelp(): void {
  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║              KMZ to GeoJSON Converter                         ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
  npx ts-node src/cli.ts [options]
  npm run convert -- [options]

Options:
  --input, -i <dir>     Input directory containing KMZ files
                        (default: ./input)

  --output, -o <dir>    Output directory for GeoJSON files
                        (default: ./out)

  --combine, -c         Generate combined file with all stops
                        (default: true)

  --no-combine          Do not generate combined file

  --prefix, -p <str>    Prefix for generated stop_id values
                        (e.g.: --prefix TRU → TRU_CENTRAL_STATION)

  --combined-name <str> Name for the combined file
                        (default: all_stops.geojson)

  --help, -h            Show this help

Examples:
  # Basic conversion
  npm run convert

  # Specify directories
  npm run convert -- -i ./my_kmz -o ./result

  # With custom prefix
  npm run convert -- --prefix TRUJILLO

  # Without combined file
  npm run convert -- --no-combine
`);
}

function parseArgs(args: string[]): ConversionOptions {
  const options: ConversionOptions = {
    inputDir: './input',
    outputDir: './out',
    combineOutput: true,
    combinedFileName: 'all_stops.geojson',
    includeSourceFile: true
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);

      case '--input':
      case '-i':
        options.inputDir = args[++i] || options.inputDir;
        break;

      case '--output':
      case '-o':
        options.outputDir = args[++i] || options.outputDir;
        break;

      case '--combine':
      case '-c':
        options.combineOutput = true;
        break;

      case '--no-combine':
        options.combineOutput = false;
        break;

      case '--prefix':
      case '-p':
        options.stopIdPrefix = args[++i];
        break;

      case '--combined-name':
        options.combinedFileName = args[++i];
        break;
    }
  }

  // Resolve absolute paths
  options.inputDir = path.resolve(options.inputDir);
  options.outputDir = path.resolve(options.outputDir);

  return options;
}

async function main(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║              KMZ to GeoJSON Converter v1.0.0                  ║
╚═══════════════════════════════════════════════════════════════╝
`);

  const args = process.argv.slice(2);
  const options = parseArgs(args);

  console.log('📋 Configuration:');
  console.log(`   Input:   ${options.inputDir}`);
  console.log(`   Output:  ${options.outputDir}`);
  console.log(`   Combine: ${options.combineOutput ? 'Yes' : 'No'}`);
  if (options.stopIdPrefix) {
    console.log(`   Prefix:  ${options.stopIdPrefix}`);
  }
  console.log('');

  try {
    const results = await convertKmzDirectory(options);

    if (results.length === 0) {
      console.log('\n❌ No files processed');
      process.exit(1);
    }

    // Final summary
    const totalStops = results.reduce((sum, r) => sum + r.stopsCount, 0);
    const totalErrors = results.reduce((sum, r) => sum + (r.errors?.length || 0), 0);

    console.log('\n' + '═'.repeat(60));
    console.log('📊 Summary:');
    console.log(`   Files processed: ${results.length}`);
    console.log(`   Total stops:     ${totalStops}`);
    if (totalErrors > 0) {
      console.log(`   Warnings:        ${totalErrors}`);
    }
    console.log('═'.repeat(60));
    console.log('\n✅ Conversion completed successfully\n');

  } catch (error) {
    console.error('\n❌ Error during conversion:', error);
    process.exit(1);
  }
}

main();
