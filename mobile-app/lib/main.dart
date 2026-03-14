import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:trufi_core_about/trufi_core_about.dart';
import 'package:trufi_core_feedback/trufi_core_feedback.dart';
import 'package:trufi_core_home_screen/trufi_core_home_screen.dart';
import 'package:trufi_core_maps/trufi_core_maps.dart';
import 'package:trufi_core_navigation/trufi_core_navigation.dart';
import 'package:trufi_core_poi_layers/trufi_core_poi_layers.dart';
import 'package:trufi_core_routing/trufi_core_routing.dart'
    show RoutingEngineManager, IRoutingProvider, Otp28RoutingProvider;
import 'package:trufi_core_saved_places/trufi_core_saved_places.dart';

import 'services/analytics_header_provider.dart';
import 'package:trufi_core_search_locations/trufi_core_search_locations.dart';
import 'package:trufi_core_settings/trufi_core_settings.dart';
import 'package:trufi_core_transport_list/trufi_core_transport_list.dart';
import 'package:trufi_core_ui/trufi_core_ui.dart';
import 'package:trufi_core_utils/trufi_core_utils.dart' show OverlayManager;
import 'package:url_launcher/url_launcher.dart';

import 'l10n/app_localizations.dart';

const _defaultCenter = LatLng(-8.1116, -79.0288);
const _appName = 'Trujillo MiRuta';
const _deepLinkScheme = 'trujillomiruta';
const _cityName = 'Trujillo';
const _countryName = 'Perú';
const _emailContact = 'info@munitrujillo.gob.pe';
const _feedbackUrl = 'https://www.trufi-association.org/feedback/';
const _facebookUrl = 'https://www.facebook.com/munitruGMCRR';
const _instagramUrl = 'https://www.instagram.com/muni.trujillo';
const _xTwitterUrl = 'https://x.com/MPT_Trujillo';
const _tiktokUrl = 'https://www.tiktok.com/@munitrujillo';
const _youtubeUrl = 'https://www.youtube.com/@muniprovincialtrujillo';
const _mapsBaseUrl = 'https://maps.trujillo.trufi.dev';

final _analyticsHeader = AnalyticsHeaderProvider();

// Routing engines
final List<IRoutingProvider> _routingEngines = [
  Otp28RoutingProvider(
    endpoint: 'https://otp.trujillo.trufi.dev',
    displayName: 'OTP 2.8',
    planHeaderProvider: _analyticsHeader.provider,
    showWheelchairOption: false,
  ),
];

// Map engines - offline + online
final List<ITrufiMapEngine> _mapEngines = [
  if (!kIsWeb) ...[
    OfflineMapLibreEngine(
      engineId: 'offline_osm_liberty',
      nameBuilder: (ctx) => AppLocalizations.of(ctx)!.mapStandard,
      descriptionBuilder: (ctx) => AppLocalizations.of(ctx)!.mapStandardDesc,
      config: OfflineMapConfig(
        mbtilesAsset: 'assets/offline/trujillo.mbtiles',
        styleAsset: 'assets/offline/styles/osm-liberty/style.json',
        spritesAssetDir: 'assets/offline/styles/osm-liberty/',
        fontsAssetDir: 'assets/offline/fonts/',
        fontMapping: {
          'RobotoRegular': 'Roboto Regular',
          'RobotoMedium': 'Roboto Medium',
          'RobotoCondensedItalic': 'Roboto Condensed Italic',
        },
        fontRanges: [
          '0-255',
          '256-511',
          '512-767',
          '768-1023',
          '1024-1279',
          '1280-1535',
          '8192-8447',
          '8448-8703',
        ],
      ),
    ),
    OfflineMapLibreEngine(
      engineId: 'offline_osm_bright',
      nameBuilder: (ctx) => AppLocalizations.of(ctx)!.mapLight,
      descriptionBuilder: (ctx) => AppLocalizations.of(ctx)!.mapLightDesc,
      config: OfflineMapConfig(
        mbtilesAsset: 'assets/offline/trujillo.mbtiles',
        styleAsset: 'assets/offline/styles/osm-bright/style.json',
        spritesAssetDir: 'assets/offline/styles/osm-bright/',
        fontsAssetDir: 'assets/offline/fonts/',
        fontMapping: {
          'OpenSansRegular': 'Open Sans Regular',
          'OpenSansBold': 'Open Sans Bold',
          'OpenSansItalic': 'Open Sans Italic',
        },
        fontRanges: [
          '0-255',
          '256-511',
          '512-767',
          '768-1023',
          '1024-1279',
          '1280-1535',
          '8192-8447',
          '8448-8703',
        ],
      ),
    ),
  ],
];
// ========================================

void main() {
  runTrufiApp(
    AppConfiguration(
      appName: _appName,
      appTagline: 'Planificador de viajes',
      deepLinkScheme: _deepLinkScheme,
      localeConfig: const TrufiLocaleConfig(
        supportedLocales: [Locale('en'), Locale('es')],
        defaultLocaleIndex: 1,
      ),
      extraLocalizationsDelegates: [AppLocalizations.delegate],
      themeConfig: TrufiThemeConfig(
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2F64AD),
            primary: const Color(0xFF2F64AD),
            primaryContainer: const Color(0xFFD8E0ED), // AZUL 15%
            onPrimaryContainer: const Color(0xFF1A3660),
            secondary: const Color(0xFF0098DA),
            secondaryContainer: const Color(0xFFE5EAF2), // AZUL 10%
            onSecondaryContainer: const Color(0xFF1A3660),
            tertiary: const Color(0xFF2F64AD),
            tertiaryContainer: const Color(0xFFE5EAF2), // AZUL 10%
            surface: const Color(0xFFF7F7F8),
            surfaceContainerHighest: const Color(0xFFE9EDF5), // AZUL ~8%
            outline: const Color(0xFFD2D3D5),
            outlineVariant: const Color(0xFFE0E1E3), // GRIS 70%
          ),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2F64AD),
            primary: const Color(0xFF7BA3D4),
            secondary: const Color(0xFF0098DA),
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
      ),
      socialMediaLinks: const [
        SocialMediaLink(
          url: _facebookUrl,
          icon: Icons.facebook,
          label: 'Facebook',
        ),
        SocialMediaLink(
          url: _instagramUrl,
          icon: Icons.camera_alt_outlined,
          label: 'Instagram',
        ),
        SocialMediaLink(
          url: _xTwitterUrl,
          icon: Icons.close,
          label: 'X (Twitter)',
        ),
        SocialMediaLink(
          url: _tiktokUrl,
          icon: Icons.music_note,
          label: 'TikTok',
        ),
        SocialMediaLink(
          url: _youtubeUrl,
          icon: Icons.play_circle_outline,
          label: 'YouTube',
        ),
      ],
      providers: [
        ChangeNotifierProvider(
          create: (_) => MapEngineManager(
            engines: _mapEngines,
            defaultCenter: _defaultCenter,
          ),
        ),
        ChangeNotifierProvider(
          create: (_) => RoutingEngineManager(engines: _routingEngines),
        ),
        ChangeNotifierProvider(
          create: (_) => OverlayManager(
            managers: [
              OnboardingManager(
                overlayBuilder: (onComplete) =>
                    OnboardingSheet(onComplete: onComplete),
              ),
              PrivacyConsentManager(
                overlayBuilder: (onAccept, onDecline) => PrivacyConsentSheet(
                  onAccept: onAccept,
                  onDecline: onDecline,
                ),
              ),
            ],
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
            appName: _appName,
            deepLinkScheme: _deepLinkScheme,
            poiLayersManager: POILayersManager(assetsBasePath: 'assets/pois'),
          ),
          onStartNavigation: (context, itinerary, locationService) {
            NavigationScreen.showFromItinerary(
              context,
              itinerary: itinerary,
              locationService: locationService,
              mapEngineManager: MapEngineManager.read(context),
            );
          },
          onRouteTap: (context, routeCode) {
            TransportDetailScreen.show(context, routeCode: routeCode);
          },
        ),
        SavedPlacesTrufiScreen(),
        TransportListTrufiScreen(),
        FeedbackTrufiScreen(config: FeedbackConfig(feedbackUrl: _feedbackUrl)),
        SettingsTrufiScreen(),
        AboutTrufiScreen(
          config: AboutScreenConfig(
            appName: _appName,
            cityName: _cityName,
            countryName: _countryName,
            emailContact: _emailContact,
            sections: [
              // CIMO-approved "about" section (replaces default Trufi Association text)
              Builder(builder: (context) {
                final l10n = AppLocalizations.of(context)!;
                final theme = Theme.of(context);
                return AboutSectionCard(
                  icon: Icons.info_rounded,
                  iconColor: const Color(0xFF2F64AD),
                  title: l10n.aboutTitle,
                  child: Text(
                    l10n.aboutDescription,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      height: 1.6,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                );
              }),
              // Open source section (default)
              Builder(builder: (context) {
                final theme = Theme.of(context);
                final aboutL10n = AboutLocalizations.of(context);
                return AboutSectionCard(
                  icon: Icons.code_rounded,
                  iconColor: Colors.green,
                  title: 'Open Source',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        aboutL10n.aboutOpenSource,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.6,
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                      const SizedBox(height: 14),
                      AboutLinkTile(
                        icon: Icons.open_in_new_rounded,
                        iconColor: Colors.deepPurple,
                        title: 'GitHub',
                        subtitle: 'trufi-association/trufi-core',
                        onTap: () => launchUrl(
                          Uri.parse('https://github.com/trufi-association/trufi-core'),
                          mode: LaunchMode.externalApplication,
                        ),
                      ),
                    ],
                  ),
                );
              }),
              // Contact section
              Builder(builder: (context) {
                final l10n = AppLocalizations.of(context)!;
                return AboutSectionCard(
                  icon: Icons.mail_rounded,
                  iconColor: Colors.orange,
                  title: l10n.aboutContactTitle,
                  child: AboutLinkTile(
                    icon: Icons.email_rounded,
                    iconColor: Colors.indigo,
                    title: _emailContact,
                    subtitle: l10n.aboutContactSubtitle,
                    onTap: () => launchUrl(
                      Uri.parse('mailto:$_emailContact?subject=$_appName Feedback'),
                      mode: LaunchMode.externalApplication,
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
      ],
    ),
  );
}
