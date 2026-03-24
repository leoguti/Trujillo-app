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
  String get mapFiord => 'Fiord';

  @override
  String get mapFiordDesc => 'Dark blue map';

  @override
  String get aboutTitle => 'More about Trujillo Mi Ruta';

  @override
  String get aboutDescription =>
      'Mi Ruta Trujillo is a digital application that makes it easier to get around the city by public transport. It allows users to look up routes and locate stops to better plan each trip, save time, and reach their destination with greater clarity.\n\nThis application was developed with the support of German development cooperation, implemented by the Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH, and Switzerland, through its Economic Cooperation, within the framework of the Cities in Motion (CIMO) project. Its implementation was carried out with the support of the Ministry of Transport and Communications of Peru (MTC), through PROMOVILIDAD, and in coordination with the Provincial Municipality of Trujillo.';

  @override
  String get aboutContactTitle => 'Contact';

  @override
  String get aboutContactSubtitle => 'Send us your feedback';

  @override
  String get aboutPartnersTitle => 'Project partners';

  @override
  String get aboutOpenSourceNotice =>
      'This application is built with open source software under the GPL-3.0 license.';
}
