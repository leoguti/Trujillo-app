import { extractFromPBF, DEFAULT_CATEGORIES } from 'trufi-server-poi_extractor';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const inputFile = join(__dirname, 'kigali.osm.pbf');
const outputDir = join(__dirname, '..', 'assets', 'pois');

console.log('🚀 Extracting POIs from Kigali OSM data...');
console.log(`📂 Input: ${inputFile}`);
console.log(`📂 Output: ${outputDir}`);

try {
  const result = await extractFromPBF({
    inputFile,
    outputDir,
    categories: DEFAULT_CATEGORIES,
    verbose: true
  });

  console.log(`\n✅ Extraction complete!`);
  console.log(`📊 Total POIs extracted: ${result.metadata.total}`);
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
