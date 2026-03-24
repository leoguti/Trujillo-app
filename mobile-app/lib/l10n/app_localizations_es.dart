// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get mapStandard => 'Estándar';

  @override
  String get mapStandardDesc => 'Mapa estándar';

  @override
  String get mapLight => 'Claro';

  @override
  String get mapLightDesc => 'Mapa claro';

  @override
  String get mapFiord => 'Fiord';

  @override
  String get mapFiordDesc => 'Mapa azul oscuro';

  @override
  String get aboutTitle => 'Más sobre Trujillo Mi Ruta';

  @override
  String get aboutDescription =>
      'Mi Ruta Trujillo es una aplicación digital que hace más fácil moverse en transporte público por la ciudad. Permite consultar rutas y ubicar paraderos para planificar mejor cada viaje, ahorrar tiempo y llegar al destino con mayor claridad.\n\nEsta aplicación fue desarrollada con apoyo de la cooperación alemana para el desarrollo, implementada por la Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH, y Suiza, a través de su Cooperación Económica, en el marco del proyecto Ciudades en Movimiento (CIMO). Su implementación se llevó adelante con el soporte del Ministerio de Transportes y Comunicaciones del Perú (MTC), mediante PROMOVILIDAD, y en coordinación con la Municipalidad Provincial de Trujillo.';

  @override
  String get aboutContactTitle => 'Contacto';

  @override
  String get aboutContactSubtitle => 'Envíanos tus comentarios';

  @override
  String get aboutPartnersTitle => 'Socios del proyecto';

  @override
  String get aboutOpenSourceNotice =>
      'Esta aplicación está construida con software de código abierto bajo la licencia GPL-3.0.';
}
