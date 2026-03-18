# Trujillo MiRuta

Aplicacion de transporte publico para Trujillo, Peru. Construida con [Trufi Core](https://github.com/trufi-association/trufi-core) v5.5.0.

## Requisitos

- [FVM](https://fvm.app) (Flutter Version Management)
- Android Studio (ultima version)
- Xcode (ultima version, solo para iOS)

## Instalacion

```bash
# Instalar la version correcta de Flutter
fvm install

# Obtener dependencias
fvm flutter pub get

# Correr en dispositivo conectado
fvm flutter run
```

## Build

### Android APK (release firmado)

```bash
fvm flutter build apk --release
```

El APK queda en `build/app/outputs/flutter-apk/app-release.apk`.

### Android App Bundle (para Play Store)

```bash
fvm flutter build appbundle --release
```

El AAB queda en `build/app/outputs/bundle/release/app-release.aab`.

### iOS (sin firma)

```bash
fvm flutter build ios --release --no-codesign
```

El `.app` queda en `build/ios/iphoneos/Runner.app`.

## Firma Android

- El certificado es autofirmado (self-signed), lo cual es normal para apps Android. Google Play acepta certificados autofirmados.
- Si se sube a Google Play, Google recomienda usar **Play App Signing** donde Google gestiona la clave de firma final y esta clave se usa solo como clave de subida (upload key).
- El certificado debe tener minimo 25 anos de validez (requisito de Google Play).
- El keystore y `key.properties` son archivos sensibles. No compartir publicamente ni incluir en el repositorio.

## Firma iOS

- El `Runner.app` compilado con `--no-codesign` **no se puede instalar directamente** en un dispositivo sin firmarlo con un certificado de Apple Developer valido.
- **Para distribuir en App Store:** Abrir el proyecto en Xcode, configurar el Team de Apple Developer, y hacer Archive > Distribute.
- **Para testing en dispositivo:** Firmar ad-hoc con un perfil de aprovisionamiento que incluya los UDIDs de los dispositivos de prueba.

## FVM (Flutter Version Management)

Este proyecto usa [FVM](https://fvm.app) para fijar la version de Flutter. La version esta definida en `.fvmrc`.

```bash
# Instalar fvm
dart pub global activate fvm

# Instalar la version de Flutter del proyecto
fvm install

# Verificar version activa
fvm flutter --version
```

Todos los comandos de Flutter deben ejecutarse con `fvm flutter` en vez de `flutter` para asegurar la version correcta.

## Estructura del proyecto

```
lib/
  main.dart              # Configuracion y punto de entrada
  l10n/                  # Traducciones (es, en)
  services/              # Servicios (analytics, etc.)
assets/
  routing/               # GTFS zip para ruteo offline
  pois/                  # Paraderos en GeoJSON
  offline/               # Mapas offline (mbtiles + estilos)
  branding/              # Logos de socios
  geo/                   # Limites de distritos
android/                 # Archivos de plataforma Android
ios/                     # Archivos de plataforma iOS
stop_pois_extractor/     # Extractor de paraderos desde GTFS
```

## Descargas

- [Google Play Store](https://play.google.com/store/apps/details?id=dev.trufi.trujillo)
- [Web](https://trujillo.trufi.dev)

## Links

- [Trufi Association](https://www.trufi-association.org)
- [Trufi Core](https://github.com/trufi-association/trufi-core)
- [trufi-gtfs-builder](https://github.com/trufi-association/trufi-gtfs-builder)
