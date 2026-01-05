import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:trufi_core_about/trufi_core_about.dart';
import 'package:trufi_core_fares/trufi_core_fares.dart';
import 'package:trufi_core_feedback/trufi_core_feedback.dart';
import 'package:trufi_core_home_screen/trufi_core_home_screen.dart';
import 'package:trufi_core_maps/trufi_core_maps.dart';
import 'package:trufi_core_navigation/trufi_core_navigation.dart';
import 'package:trufi_core_poi_layers/trufi_core_poi_layers.dart';
import 'package:trufi_core_saved_places/trufi_core_saved_places.dart';
import 'package:trufi_core_search_locations/trufi_core_search_locations.dart';
import 'package:trufi_core_settings/trufi_core_settings.dart';
import 'package:trufi_core_transport_list/trufi_core_transport_list.dart';
import 'package:trufi_core_ui/trufi_core_ui.dart';

// Trujillo, Peru - City center coordinates (Plaza de Armas)
const _defaultCenter = LatLng(-8.1116, -79.0288);

void main() {
  runTrufiApp(
    AppConfiguration(
      appName: 'Trujillo Mobility',
      deepLinkScheme: 'trujillomobility',
      socialMediaLinks: const [
        SocialMediaLink(
          url: 'https://facebook.com/trufiapp',
          icon: Icons.facebook,
          label: 'Facebook',
        ),
        SocialMediaLink(
          url: 'https://x.com/trufiapp',
          icon: Icons.close,
          label: 'X (Twitter)',
        ),
        SocialMediaLink(
          url: 'https://instagram.com/trufiapp',
          icon: Icons.camera_alt_outlined,
          label: 'Instagram',
        ),
      ],
      providers: [
        ChangeNotifierProvider(
          create: (_) => MapEngineManager(
            engines: [
              MapLibreEngine(
                styleString: 'https://maps.trujillo.trufi.dev/styles/osm-bright/style.json',
                darkStyleString: 'https://maps.trujillo.trufi.dev/styles/fiord-color/style.json',
              ),
              FlutterMapEngine(),
            ],
            defaultCenter: _defaultCenter,
          ),
        ),
        BlocProvider(
          create: (_) => SearchLocationsCubit(
            searchLocationService: PhotonSearchService(
              baseUrl: 'https://photon.trujillo.trufi.dev',
              biasLatitude: _defaultCenter.latitude,
              biasLongitude: _defaultCenter.longitude,
            ),
          ),
        ),
      ],
      screens: [
        HomeScreenTrufiScreen(
          config: HomeScreenConfig(
            otpEndpoint: 'https://otp.trujillo.trufi.dev',
            appName: 'Trujillo Mobility',
            deepLinkScheme: 'trujillomobility',
            poiLayersManager: POILayersManager(
              assetsBasePath: 'assets/pois',
              defaultEnabledSubcategories: {
                POICategory.tourism: {'museum', 'attraction', 'viewpoint'},
                POICategory.food: {'restaurant', 'cafe'},
                POICategory.transport: {'bus_station', 'bus_stop'},
              },
            ),
          ),
          onStartNavigation: (context, itinerary, locationService) {
            NavigationScreen.showFromItinerary(
              context,
              itinerary: itinerary,
              locationService: locationService,
              mapEngineManager: MapEngineManager.read(context),
            );
          },
        ),
        SavedPlacesTrufiScreen(),
        TransportListTrufiScreen(
          config: TransportListOtpConfig(
            otpEndpoint: 'https://otp.trujillo.trufi.dev',
          ),
        ),
        FaresTrufiScreen(
          config: FaresConfig(
            currency: 'PEN',
            lastUpdated: DateTime(2025, 1, 1),
            fares: [
              const FareInfo(
                transportType: 'Combi',
                icon: Icons.directions_bus,
                regularFare: '1.50',
                studentFare: '0.80',
                seniorFare: '0.80',
              ),
              const FareInfo(
                transportType: 'Microbús',
                icon: Icons.directions_bus,
                regularFare: '1.20',
                studentFare: '0.60',
                seniorFare: '0.60',
              ),
              const FareInfo(
                transportType: 'Mototaxi',
                icon: Icons.two_wheeler,
                regularFare: '3.00-8.00',
              ),
            ],
          ),
        ),
        FeedbackTrufiScreen(
          config: FeedbackConfig(
            feedbackUrl: 'https://www.trufi-association.org/feedback/',
          ),
        ),
        SettingsTrufiScreen(),
        AboutTrufiScreen(
          config: AboutScreenConfig(
            appName: 'Trujillo Mobility',
            cityName: 'Trujillo',
            countryName: 'Perú',
            emailContact: 'info@trufi-association.org',
          ),
        ),
      ],
    ),
  );
}
