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

## Estructura de builds

```
build/
├── app/outputs/
│   ├── flutter-apk/
│   │   └── app-release.apk      ← APK firmado
│   └── bundle/release/
│       └── app-release.aab      ← AAB firmado
└── ios/iphoneos/
    └── Runner.app                ← iOS app (sin firma)
```
