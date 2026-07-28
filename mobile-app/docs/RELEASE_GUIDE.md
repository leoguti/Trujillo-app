# Trujillo MiRuta - Guia de Release y Firma

## Android

### Firmar un APK/AAB con otro keystore

Si el build se hizo con un keystore temporal y se necesita re-firmar con el keystore de produccion:

#### Opcion 1: Re-hacer el build con el keystore correcto

1. Reemplazar `android/upload-keystore.jks` con el keystore de produccion
2. Actualizar `android/key.properties` con las credenciales correspondientes
3. Ejecutar `flutter build apk --release` o `flutter build appbundle --release`

#### Opcion 2: Firmar un APK existente manualmente

```bash
# 1. Alinear el APK
zipalign -v -p 4 app-release.apk app-release-aligned.apk

# 2. Firmar con apksigner
apksigner sign \
  --ks produccion-keystore.jks \
  --ks-key-alias alias_del_key \
  --out app-release-firmado.apk \
  app-release-aligned.apk

# 3. Verificar la firma
apksigner verify --verbose app-release-firmado.apk
```

> `zipalign` y `apksigner` estan en `$ANDROID_HOME/build-tools/<version>/`

#### Opcion 3: Firmar un AAB con jarsigner

```bash
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore produccion-keystore.jks \
  app-release.aab alias_del_key
```

### Subir a Google Play

1. Ir a [Google Play Console](https://play.google.com/console)
2. Crear la app o seleccionarla si ya existe
3. **Release > Production > Create new release**
4. Subir el `.aab` (preferido) o `.apk`
5. Google Play re-firma el AAB con su propia key si usas **App Signing by Google Play** (recomendado)

### Observaciones Android

- **App Signing by Google Play**: Si esta activado (recomendado), Google re-firma el app al distribuir. El keystore local es solo el "upload key". Si se pierde, se puede solicitar uno nuevo a Google.
- **Bundle ID**: `dev.trufi.trujillo`
- **Min SDK**: 24 (Android 7.0)
- **Version actual**: 1.0.0+6 (versionName: 1.0.0, versionCode: 6)

---

## iOS

### Estado actual (jul 2026)

La app iOS se publica desde la cuenta personal de Samuel Rioja (Team ID `K45698KZ4W`)
y luego se transferira a la cuenta del cliente via **App Store Connect > App Transfer**.

- **Bundle ID iOS**: `app.trufi.trujillo` (registro N8YJ83T63C, App Store Apple ID `6795452859`)
- **IMPORTANTE**: el bundle ID de iOS es DISTINTO al de Android (`dev.trufi.trujillo`).
  El identificador `dev.trufi.trujillo` ya estaba registrado en otro team de Apple
  (no en Trufi Association ni en Yapa IT, que tiene la membresia vencida) y Apple
  exige unicidad global, asi que se uso `app.trufi.trujillo` siguiendo la convencion
  de las demas apps Trufi (`app.trufi.navigator`, `app.trufi.konstanz`).
- **Entitlements**: `ios/Runner/Runner.entitlements` incluye Associated Domains
  (`applinks:trujillo.trufi.dev`) para universal links.

### Build y subida (desde la cuenta actual)

```bash
cd mobile-app/ios
xcodebuild -workspace Runner.xcworkspace -scheme Runner -configuration Release \
  archive -archivePath ../build/ios/archive/Runner.xcarchive \
  -destination 'generic/platform=iOS' -allowProvisioningUpdates

xcodebuild -exportArchive -archivePath ../build/ios/archive/Runner.xcarchive \
  -exportPath ../build/ios/ipa -exportOptionsPlist <ExportOptions con method app-store-connect> \
  -allowProvisioningUpdates

xcrun altool --upload-app -f "../build/ios/ipa/Trujillo MiRuta.ipa" -t ios \
  --apiKey <KEY_ID> --apiIssuer <ISSUER_ID>
```

> La API key (.p8) vive en `~/.appstoreconnect/private_keys/`. `flutter build ipa`
> falla en el paso de export porque no pasa `-allowProvisioningUpdates`; usar los
> comandos de arriba.

### Transferencia al cliente (pendiente)

1. El cliente necesita su propia cuenta Apple Developer activa ($99/anio; cuenta
   **Organization** con DUNS si quieren que el vendedor visible sea la institucion).
2. Sin builds en revision al momento de transferir. Ratings y resenas se transfieren;
   testers de TestFlight NO.
3. Tras la transferencia, actualizar el `apple-app-site-association` con el Team ID
   del cliente (ver seccion Deep Links).

### Observaciones iOS

- **Deep Linking**: `FlutterDeepLinkingEnabled` esta activo y el entitlement de
  Associated Domains ya esta en el proyecto. Falta el archivo
  `apple-app-site-association` en el servidor (ver seccion Deep Links).

---

## Deep Links (pendiente post-publicacion)

### Android - assetlinks.json

Cuando el app este publicado en Google Play:

1. Obtener el SHA-256 del signing key:
   ```bash
   keytool -list -v -keystore tu-keystore.jks -alias tu_alias | grep SHA256
   ```
   O desde Google Play Console: **Release > Setup > App signing > SHA-256 certificate fingerprint**

2. Crear `.well-known/assetlinks.json` en el servidor (`trujillo.trufi.dev`):
   ```json
   [{
     "relation": ["delegate_permission/common.handle_all_urls"],
     "target": {
       "namespace": "android_app",
       "package_name": "dev.trufi.trujillo",
       "sha256_cert_fingerprints": ["SHA256_DEL_SIGNING_KEY"]
     }
   }]
   ```

### iOS - apple-app-site-association

Cuando el app este publicado en App Store:

1. Mientras la app este en la cuenta de Samuel, el Team ID es `K45698KZ4W`.
   Tras la transferencia, reemplazarlo por el Team ID del cliente
   (Apple Developer > Membership).

2. Crear `.well-known/apple-app-site-association` en el servidor:
   ```json
   {
     "applinks": {
       "apps": [],
       "details": [{
         "appID": "K45698KZ4W.app.trufi.trujillo",
         "paths": ["*"]
       }]
     }
   }
   ```
   > Ojo: el bundle ID de iOS es `app.trufi.trujillo` (no `dev.trufi.trujillo`,
   > que es solo el de Android).

3. El archivo debe servirse con `Content-Type: application/json` (nginx lo hace por defecto)

---

## Checklist de Release

- [ ] Incrementar version en `pubspec.yaml` (versionName + versionCode)
- [ ] Build APK y AAB con keystore de produccion
- [ ] Build iOS Archive desde Xcode del cliente
- [ ] Subir AAB a Google Play Console
- [ ] Subir iOS a App Store Connect
- [ ] Configurar `assetlinks.json` en servidor (con SHA256 de Google Play)
- [ ] Configurar `apple-app-site-association` en servidor (con Team ID del cliente)
- [ ] Actualizar URLs de las tiendas en la landing page (`trujillo.trufi.dev`)
