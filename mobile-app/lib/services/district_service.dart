import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;

/// A district parsed from the GeoJSON.
class District {
  final int osmRelationId;
  final String name;
  final String ubigeo;

  /// Polygon vertices as [lng, lat] pairs (GeoJSON order).
  final List<List<double>> coordinates;

  const District({
    required this.osmRelationId,
    required this.name,
    required this.ubigeo,
    required this.coordinates,
  });
}

/// Looks up which district a coordinate falls in using the bundled GeoJSON.
class DistrictService {
  static const _assetPath = 'assets/geo/distritos_trujillo.geojson';

  List<District>? _districts;

  /// Loads and parses the GeoJSON. Safe to call multiple times.
  Future<void> initialize() async {
    if (_districts != null) return;

    final raw = await rootBundle.loadString(_assetPath);
    final geojson = json.decode(raw) as Map<String, dynamic>;
    final features = geojson['features'] as List;

    final parsed = <District>[];
    for (final feature in features) {
      final geometry = feature['geometry'] as Map<String, dynamic>;
      if (geometry['type'] != 'LineString') continue;

      final props = feature['properties'] as Map<String, dynamic>;
      final rawId = props['@id'] as String? ?? '';
      if (!rawId.startsWith('relation/')) continue;

      final osmId = int.tryParse(rawId.replaceFirst('relation/', ''));
      if (osmId == null) continue;

      final rawCoords = geometry['coordinates'] as List;
      final coords = rawCoords
          .map<List<double>>(
            (c) => [(c as List)[0] as double, c[1] as double],
          )
          .toList();

      parsed.add(District(
        osmRelationId: osmId,
        name: props['name'] as String? ?? '',
        ubigeo: props['pe:ubigeo'] as String? ?? '',
        coordinates: coords,
      ));
    }

    _districts = parsed;
  }

  /// Returns the district containing [lat], [lng], or `null`.
  District? lookup(double lat, double lng) {
    final districts = _districts;
    if (districts == null) return null;

    for (final d in districts) {
      if (_containsPoint(d.coordinates, lng, lat)) return d;
    }
    return null;
  }

  /// Ray-casting algorithm for point-in-polygon.
  /// [polygon] is a list of [lng, lat] pairs (GeoJSON order).
  static bool _containsPoint(
    List<List<double>> polygon,
    double testLng,
    double testLat,
  ) {
    var inside = false;
    final n = polygon.length;

    for (int i = 0, j = n - 1; i < n; j = i++) {
      final xi = polygon[i][0], yi = polygon[i][1];
      final xj = polygon[j][0], yj = polygon[j][1];

      if (((yi > testLat) != (yj > testLat)) &&
          (testLng < (xj - xi) * (testLat - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }

    return inside;
  }
}
