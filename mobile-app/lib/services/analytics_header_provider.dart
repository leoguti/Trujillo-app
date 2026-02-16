import 'package:h3_flutter/h3_flutter.dart';
import 'package:trufi_core_routing/trufi_core_routing.dart'
    show RoutingLocation, PlanHeaderProvider;

import 'district_service.dart';

const _h3Resolution = 15;

/// Builds the [PlanHeaderProvider] that attaches analytics headers
/// (lat/lng, H3 index, district) to every plan request.
///
/// Initialization is lazy: the GeoJSON and H3 engine are loaded on the
/// first plan request so no explicit `initialize()` call is needed.
class AnalyticsHeaderProvider {
  final DistrictService _districtService;
  H3? _h3;
  Future<void>? _initFuture;

  AnalyticsHeaderProvider({DistrictService? districtService})
      : _districtService = districtService ?? DistrictService();

  Future<void> _ensureInitialized() {
    return _initFuture ??= _doInitialize();
  }

  Future<void> _doInitialize() async {
    _h3 = const H3Factory().load();
    await _districtService.initialize();
  }

  /// The callback to pass to [Otp28RoutingProvider.planHeaderProvider].
  PlanHeaderProvider get provider => _buildHeaders;

  Future<Map<String, String>> _buildHeaders(
    RoutingLocation from,
    RoutingLocation to,
  ) async {
    await _ensureInitialized();

    final fromLat = from.position.latitude;
    final fromLng = from.position.longitude;
    final toLat = to.position.latitude;
    final toLng = to.position.longitude;

    // H3 indexes
    final h3 = _h3!;
    final fromH3 = h3
        .geoToCell(GeoCoord(lat: fromLat, lon: fromLng), _h3Resolution)
        .toRadixString(16);
    final toH3 = h3
        .geoToCell(GeoCoord(lat: toLat, lon: toLng), _h3Resolution)
        .toRadixString(16);

    // District lookups
    final fromDistrict = _districtService.lookup(fromLat, fromLng);
    final toDistrict = _districtService.lookup(toLat, toLng);

    return {
      'X-Origin-Lat': fromLat.toString(),
      'X-Origin-Lng': fromLng.toString(),
      'X-Origin-H3': fromH3,
      'X-Origin-District': fromDistrict?.osmRelationId.toString() ?? '',
      'X-Destination-Lat': toLat.toString(),
      'X-Destination-Lng': toLng.toString(),
      'X-Destination-H3': toH3,
      'X-Destination-District': toDistrict?.osmRelationId.toString() ?? '',
    };
  }
}
