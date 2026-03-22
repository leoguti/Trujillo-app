import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:trufi_core_about/trufi_core_about.dart';
import 'package:trufi_core_feedback/trufi_core_feedback.dart';
import 'package:trufi_core_home_screen/trufi_core_home_screen.dart';
import 'package:trufi_core_maps/trufi_core_maps.dart';
import 'package:trufi_core_navigation/trufi_core_navigation.dart'
    show NavigationScreen, NavigationLocalizations;
import 'package:trufi_core_poi_layers/trufi_core_poi_layers.dart';
import 'package:trufi_core_routing/trufi_core_routing.dart'
    show RoutingEngineManager, IRoutingProvider, Otp28RoutingProvider, RoutingLocalizations;
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
const _cityName = 'Trujillo';
const _countryName = 'Perú';
const _emailContact = 'info@munitrujillo.gob.pe';
const _feedbackUrl = 'https://forms.gle/y72KNLDdfjtXVVxc6';
const _facebookUrl = 'https://www.facebook.com/munitruGMCRR';
const _instagramUrl = 'https://www.instagram.com/muni.trujillo';
const _xTwitterUrl = 'https://x.com/MPT_Trujillo';
const _tiktokUrl = 'https://www.tiktok.com/@munitrujillo';
const _youtubeUrl = 'https://www.youtube.com/@muniprovincialtrujillo';
const _webBaseUrl = 'https://trujillo.trufi.dev';

final _analyticsHeader = AnalyticsHeaderProvider();

// Routing engines
final List<IRoutingProvider> _routingEngines = [
  Otp28RoutingProvider(
    endpoint: 'https://otp.trujillo.trufi.dev',
    displayName: 'OTP 2.8',
    planHeaderProvider: _analyticsHeader.provider,
    showWheelchairOption: false,
    showBicycleOption: false,
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
      engineId: 'offline_fiord_color',
      nameBuilder: (ctx) => AppLocalizations.of(ctx)!.mapFiord,
      descriptionBuilder: (ctx) => AppLocalizations.of(ctx)!.mapFiordDesc,
      config: OfflineMapConfig(
        mbtilesAsset: 'assets/offline/trujillo.mbtiles',
        styleAsset: 'assets/offline/styles/fiord-color/style.json',
        spritesAssetDir: 'assets/offline/styles/fiord-color/',
        fontsAssetDir: 'assets/offline/fonts/',
        fontMapping: {
          'MetropolisRegular': 'Metropolis Regular',
          'MetropolisLight': 'Metropolis Light',
          'MetropolisLightItalic': 'Metropolis Light Italic',
          'MetropolisMediumItalic': 'Metropolis Medium Italic',
          'NotoSansRegular': 'Noto Sans Regular',
          'NotoSansItalic': 'Noto Sans Italic',
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
      localeConfig: const TrufiLocaleConfig(
        supportedLocales: [Locale('en'), Locale('es')],
        defaultLocaleIndex: 1,
      ),
      extraLocalizationsDelegates: [AppLocalizations.delegate, RoutingLocalizations.delegate, NavigationLocalizations.delegate],
      initScreenBuilder: _buildInitScreen,
      drawerFooterExtra: const _PartnerLogosRow(),
      logo: const _AppLogo(),
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
            shareBaseUrl: _webBaseUrl,
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
        TransportListTrufiScreen(
          dataProviderBuilder: (_) => GtfsTransportDataProvider(
            assetPath: 'assets/routing/trujillo.gtfs.zip',
          ),
        ),
        FeedbackTrufiScreen(config: FeedbackConfig(feedbackUrl: _feedbackUrl)),
        SettingsTrufiScreen(),
        AboutTrufiScreen(
          config: AboutScreenConfig(
            appName: _appName,
            cityName: _cityName,
            countryName: _countryName,
            emailContact: _emailContact,
            logoWidget: const _AppLogo(),
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
              // Partner logos section
              Builder(builder: (context) {
                final l10n = AppLocalizations.of(context)!;
                return AboutSectionCard(
                  icon: Icons.handshake_rounded,
                  iconColor: const Color(0xFF2F64AD),
                  title: l10n.aboutPartnersTitle,
                  child: Wrap(
                    spacing: 20,
                    runSpacing: 16,
                    alignment: WrapAlignment.center,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: const [
                      _PartnerLogo('assets/branding/MPT-logo-04.png', height: 50),
                      _PartnerLogo('assets/branding/MTC-logo.png', height: 44),
                      _PartnerLogo('assets/branding/PROMOVILIDAD-logo.png', height: 44),
                      _PartnerLogo('assets/branding/GIZ-logo.jpg', height: 40),
                      _PartnerLogo('assets/branding/SECO-logo.jpg', height: 36),
                    ],
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

class _AppLogo extends StatelessWidget {
  const _AppLogo();

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E293B) : Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Image.asset('assets/branding/app-logo.png', fit: BoxFit.contain),
    );
  }
}

class _PartnerLogo extends StatelessWidget {
  const _PartnerLogo(this.asset, {required this.height});

  final String asset;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      asset,
      height: height,
      fit: BoxFit.contain,
    );
  }
}

/// Partner logos row used in drawer footer and splash screen.
class _PartnerLogosRow extends StatelessWidget {
  const _PartnerLogosRow();

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14,
      runSpacing: 10,
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: const [
        _PartnerLogo('assets/branding/MPT-logo-04.png', height: 30),
        _PartnerLogo('assets/branding/MTC-logo.png', height: 26),
        _PartnerLogo('assets/branding/PROMOVILIDAD-logo.png', height: 26),
        _PartnerLogo('assets/branding/GIZ-logo.jpg', height: 24),
        _PartnerLogo('assets/branding/SECO-logo.jpg', height: 22),
      ],
    );
  }
}

/// Splash screen partner logos layout per CIMO branding guidelines.
class _SplashPartnerLogos extends StatelessWidget {
  const _SplashPartnerLogos();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Con el apoyo de:',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
          ),
        ),
        const SizedBox(height: 12),
        // Fila 1: MTC + PROMOVILIDAD (misma altura)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset('assets/branding/MTC-logo.png', height: 32, fit: BoxFit.contain),
            const SizedBox(width: 24),
            Image.asset('assets/branding/PROMOVILIDAD-logo.png', height: 32, fit: BoxFit.contain),
          ],
        ),
        const SizedBox(height: 12),
        // Fila 2: GIZ + SECO (misma altura)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset('assets/branding/GIZ-logo.jpg', height: 28, fit: BoxFit.contain),
            const SizedBox(width: 24),
            Image.asset('assets/branding/SECO-logo.jpg', height: 28, fit: BoxFit.contain),
          ],
        ),
      ],
    );
  }
}

/// Custom splash screen with app logo and partner logos.
Widget _buildInitScreen(
  BuildContext context,
  AppInitStep? currentStep,
  String? errorMessage,
  VoidCallback onRetry,
) {
  return DefaultInitScreen(
    currentStep: currentStep,
    errorMessage: errorMessage,
    onRetry: onRetry,
    stepTextBuilder: (step) => switch (step) {
      AppInitStep.starting => 'Iniciando',
      AppInitStep.initializingOverlays => 'Inicializando',
      AppInitStep.loadingMaps => 'Cargando mapas',
      AppInitStep.loadingRoutes => 'Cargando rutas',
      AppInitStep.preparingScreens => 'Casi listo',
    },
    logo: ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: Image.asset(
        'assets/branding/app-logo.png',
        width: 90,
        height: 90,
        fit: BoxFit.contain,
      ),
    ),
    topWidget: Padding(
      padding: const EdgeInsets.only(top: 16, left: 24, right: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Image.asset('assets/branding/MPT-logo-04.png', height: 48, fit: BoxFit.contain),
          Image.asset('assets/branding/app-logo.png', height: 48, fit: BoxFit.contain),
        ],
      ),
    ),
    bottomWidget: const Padding(
      padding: EdgeInsets.only(bottom: 24, left: 24, right: 24),
      child: _SplashPartnerLogos(),
    ),
  );
}
