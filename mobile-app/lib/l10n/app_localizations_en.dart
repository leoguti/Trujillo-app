// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get mapStandard => 'Standard';

  @override
  String get mapStandardDesc => 'Standard map';

  @override
  String get mapLight => 'Light';

  @override
  String get mapLightDesc => 'Light map';

  @override
  String get aboutTitle => 'More about Trujillo Mi Ruta';

  @override
  String get aboutDescription =>
      'Mi Ruta Trujillo is a digital application that allows users to plan public transport trips in the city of Trujillo, Peru. Through the platform, users can look up routes, identify stops, and learn about transport vehicle itineraries to reach their destination more quickly and efficiently. The tool uses information validated by transport authorities to provide reliable data that improves the urban mobility experience.\n\nThis application was developed within the framework of the Cities in Motion (CIMO) project, implemented by the Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) on behalf of the German Federal Ministry for Economic Cooperation and Development (BMZ), with co-financing from the Swiss State Secretariat for Economic Affairs (SECO). Development was supported by the Ministry of Transport and Communications of Peru (MTC), through the National Program for Sustainable Urban Transport (PROMOVILIDAD), in coordination with the Provincial Municipality of Trujillo.';

  @override
  String get aboutContactTitle => 'Contact';

  @override
  String get aboutContactSubtitle => 'Send us your feedback';

  @override
  String get aboutPartnersTitle => 'Project partners';
}
