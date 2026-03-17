# Trujillo MiRuta - Guia de Build

## Requisitos

- Flutter 3.41+ (canal stable)
- Android SDK (API 24+)
- Xcode 15+ (para iOS)
- CocoaPods (para iOS)
- Java 17 (incluido con Android Studio)

## Android

### 1. Crear keystore (solo la primera vez)

```bash
keytool -genkey -v \
  -keystore android/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload \
  -dname "CN=Trujillo MiRuta, OU=Development, O=Trufi Association, L=Trujillo, ST=La Libertad, C=PE"
```

> Si `keytool` no se encuentra, usar el de Android Studio:
> `/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/keytool`

### 2. Crear `android/key.properties`

```properties
storePassword=TU_PASSWORD
keyPassword=TU_PASSWORD
keyAlias=upload
storeFile=../upload-keystore.jks
```

> Tanto `key.properties` como `upload-keystore.jks` estan en `.gitignore`.

### 3. Build APK

```bash
flutter build apk --release
```

Salida: `build/app/outputs/flutter-apk/app-release.apk`

### 4. Build AAB (App Bundle para Google Play)

```bash
flutter build appbundle --release
```

Salida: `build/app/outputs/bundle/release/app-release.aab`

### Nota sobre firma condicional

El `build.gradle.kts` esta configurado para firmar automaticamente si `key.properties` existe. Si no existe, usa la firma de debug. Esto permite hacer builds sin keystore para desarrollo/testing.

---

## iOS

### 1. Build sin firma (para que el cliente firme)

```bash
flutter build ios --release --no-codesign
```

Salida: `build/ios/iphoneos/Runner.app`

### 2. Build con firma propia

Si tienes cuenta de Apple Developer configurada en Xcode:

```bash
open ios/Runner.xcworkspace
```

Desde Xcode:
1. Seleccionar el target **Runner**
2. En **Signing & Capabilities**, configurar tu Team
3. **Product > Archive**
4. Distribuir desde el **Organizer**

---

## Comandos utiles

```bash
# Limpiar cache de build
flutter clean

# Reinstalar dependencias
flutter pub get

# Build de debug para testing
flutter run

# Ver dispositivos conectados
flutter devices

# Incrementar version (editar pubspec.yaml)
# version: 1.0.0+6  →  version: 1.0.1+7
#          ^^^^^  ^       (name)  (code, debe incrementar siempre)
```

## Generar .zip de entrega

Después de generar los 3 binarios, crear un .zip con los binarios + archivos de firma para entrega:

```bash
# Obtener version desde pubspec.yaml (ej: 1.0.0+6)
VERSION=$(grep '^version:' pubspec.yaml | sed 's/version: //')

# Crear carpeta temporal y copiar archivos
mkdir -p /tmp/trujillo-build
cp build/app/outputs/flutter-apk/app-release.apk /tmp/trujillo-build/
cp build/app/outputs/bundle/release/app-release.aab /tmp/trujillo-build/
cp -R build/ios/iphoneos/Runner.app /tmp/trujillo-build/
cp android/key.properties /tmp/trujillo-build/
cp android/upload-keystore.jks /tmp/trujillo-build/

# Crear zip con nombre versionado
cd /tmp
zip -r "trujillo-miruta_v${VERSION}.zip" trujillo-build/
rm -rf /tmp/trujillo-build
```

El .zip resultante (ej: `trujillo-miruta_v1.0.0+6.zip`) contiene:

```
trujillo-build/
├── app-release.apk          ← APK firmado
├── app-release.aab          ← AAB firmado (Google Play)
├── Runner.app/               ← iOS app (sin firma)
├── key.properties            ← Config de firma Android
└── upload-keystore.jks       ← Keystore de firma Android
```
