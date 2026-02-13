import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import JSZip from "jszip";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const GTFS_PATH = join(
  __dirname,
  "..",
  "assets",
  "routing",
  "trujillo.gtfs.zip"
);
const OUTPUT_DIR = join(__dirname, "..", "assets", "pois");

const BUS_STOP_ICON = `<?xml version="1.0" encoding="UTF-8"?>
<svg version="1.1" id="bus" xmlns="http://www.w3.org/2000/svg" width="23" height="23" viewBox="0 0 23 23" xmlns:m="https://www.mapbox.com">
  <path d="M2 3C2 1.9 2.9 1 4 1H11C12.1 1 13 1.9 13 3V11C13 12 12 12 12 12V13C12 13.55 11.55 14 11 14C10.45 14 10 13.55 10 13V12H5V13C5 13.55 4.55 14 4 14C3.45 14 3 13.55 3 13V12C2 12 2 11 2 11V3ZM3.5 4C3.22 4 3 4.22 3 4.5V7.5C3 7.78 3.22 8 3.5 8H11.5C11.78 8 12 7.78 12 7.5V4.5C12 4.22 11.78 4 11.5 4H3.5ZM4 9C3.45 9 3 9.45 3 10C3 10.55 3.45 11 4 11C4.55 11 5 10.55 5 10C5 9.45 4.55 9 4 9ZM11 9C10.45 9 10 9.45 10 10C10 10.55 10.45 11 11 11C11.55 11 12 10.55 12 10C12 9.45 11.55 9 11 9ZM4 2.5C4 2.78 4.22 3 4.5 3H10.5C10.78 3 11 2.78 11 2.5C11 2.22 10.78 2 10.5 2H4.5C4.22 2 4 2.22 4 2.5Z" transform="translate(4 4)" fill="#000000" style="stroke-linejoin:round;stroke-miterlimit:4;" stroke="#ffffff" stroke-width="4"/>
  <path d="M2 3C2 1.9 2.9 1 4 1H11C12.1 1 13 1.9 13 3V11C13 12 12 12 12 12V13C12 13.55 11.55 14 11 14C10.45 14 10 13.55 10 13V12H5V13C5 13.55 4.55 14 4 14C3.45 14 3 13.55 3 13V12C2 12 2 11 2 11V3ZM3.5 4C3.22 4 3 4.22 3 4.5V7.5C3 7.78 3.22 8 3.5 8H11.5C11.78 8 12 7.78 12 7.5V4.5C12 4.22 11.78 4 11.5 4H3.5ZM4 9C3.45 9 3 9.45 3 10C3 10.55 3.45 11 4 11C4.55 11 5 10.55 5 10C5 9.45 4.55 9 4 9ZM11 9C10.45 9 10 9.45 10 10C10 10.55 10.45 11 11 11C11.55 11 12 10.55 12 10C12 9.45 11.55 9 11 9ZM4 2.5C4 2.78 4.22 3 4.5 3H10.5C10.78 3 11 2.78 11 2.5C11 2.22 10.78 2 10.5 2H4.5C4.22 2 4 2.22 4 2.5Z" transform="translate(4 4)" fill="#000000"/>
  <m:metadata>
    <m:parameters>
      <m:parameter m:name="background" m:type="color" m:value="#000000"/>
      <m:parameter m:name="stroke" m:type="color" m:value="#ffffff"/>
    </m:parameters>
  </m:metadata>
</svg>`;

interface Stop {
  stop_id: string;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
  stop_desc: string;
}

function parseCSV(content: string): Stop[] {
  const lines = content.trim().split("\n");
  const headers = lines[0].split(",").map((h) => h.trim());

  return lines
    .slice(1)
    .map((line) => {
      const values = line.split(",").map((v) => v.trim());
      const obj: Record<string, string> = {};
      headers.forEach((h, i) => (obj[h] = values[i] || ""));

      return {
        stop_id: obj.stop_id,
        stop_name: obj.stop_name,
        stop_lat: parseFloat(obj.stop_lat),
        stop_lon: parseFloat(obj.stop_lon),
        stop_desc: obj.stop_desc || "",
      };
    })
    .filter((s) => !isNaN(s.stop_lat) && !isNaN(s.stop_lon));
}

async function main() {
  console.log("Reading GTFS zip:", GTFS_PATH);

  const zipData = readFileSync(GTFS_PATH);
  const zip = await JSZip.loadAsync(zipData);

  const stopsFile = zip.file("stops.txt");
  if (!stopsFile) throw new Error("stops.txt not found in GTFS zip");

  const stopsContent = await stopsFile.async("string");
  const stops = parseCSV(stopsContent);

  console.log(`Found ${stops.length} stops`);

  // Clean output directory
  if (existsSync(OUTPUT_DIR)) {
    rmSync(OUTPUT_DIR, { recursive: true });
  }
  mkdirSync(OUTPUT_DIR, { recursive: true });

  // Generate GeoJSON
  const geojson = {
    type: "FeatureCollection" as const,
    features: stops.map((stop) => ({
      type: "Feature" as const,
      id: stop.stop_id,
      geometry: {
        type: "Point" as const,
        coordinates: [stop.stop_lon, stop.stop_lat],
      },
      properties: {
        id: stop.stop_id,
        name: stop.stop_name === "unnamed" ? "" : stop.stop_name,
        type: "bus_stop",
        category: "transport",
        subcategory: "bus_stop",
        ...(stop.stop_desc ? { description: stop.stop_desc } : {}),
      },
    })),
  };

  // Generate metadata
  const metadata = {
    generated: new Date().toISOString(),
    source: "gtfs:trujillo.gtfs.zip",
    categories: [
      {
        name: "transport",
        displayName: "Transport",
        "displayName:en": "Transport",
        "displayName:es": "Transporte",
        count: stops.length,
        icon: BUS_STOP_ICON,
        subcategories: [
          {
            name: "bus_stop",
            displayName: "Bus Stops",
            "displayName:en": "Bus Stops",
            "displayName:es": "Paraderos",
            defaultActive: true,
            count: stops.length,
            icon: BUS_STOP_ICON,
            color: "#1565C0",
          },
        ],
      },
    ],
  };

  writeFileSync(
    join(OUTPUT_DIR, "transport.geojson"),
    JSON.stringify(geojson, null, 2)
  );
  writeFileSync(
    join(OUTPUT_DIR, "metadata.json"),
    JSON.stringify(metadata, null, 2)
  );

  console.log(`Written ${stops.length} stops to transport.geojson`);
  console.log("Written metadata.json");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
