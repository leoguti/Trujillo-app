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

### El cliente firma por su cuenta

El build con `--no-codesign` genera un `.app` sin firma. El cliente necesita:

1. **Cuenta de Apple Developer** ($99/anio)
2. Recibir el proyecto completo (repositorio o zip)
3. Abrir `ios/Runner.xcworkspace` en Xcode
4. Configurar:
   - **Signing & Capabilities > Team**: seleccionar su equipo
   - **Bundle Identifier**: `dev.trufi.trujillo` (ya configurado)
5. **Product > Archive**
6. En el **Organizer**, seleccionar el archive y **Distribute App**
7. Elegir **App Store Connect** para subir a la tienda

### Subir a App Store

1. Desde Xcode Organizer: **Distribute App > App Store Connect**
2. O usar **Transporter** (app de Apple) para subir el `.ipa`
3. En [App Store Connect](https://appstoreconnect.apple.com), crear la ficha del app y enviar a revision

### Observaciones iOS

- **Bundle ID**: `dev.trufi.trujillo`
- **Deep Linking**: `FlutterDeepLinkingEnabled` esta activo. Cuando el app se publique, se debe configurar el archivo `apple-app-site-association` en el servidor (ver seccion Deep Links)
- **El cliente NO necesita compartir su cuenta**: solo necesita el codigo fuente y hacer el Archive desde su Xcode con su Team configurado

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

1. Obtener el **Team ID** de la cuenta del cliente (en Apple Developer > Membership)

2. Crear `.well-known/apple-app-site-association` en el servidor:
   ```json
   {
     "applinks": {
       "apps": [],
       "details": [{
         "appID": "TEAM_ID.dev.trufi.trujillo",
         "paths": ["*"]
       }]
     }
   }
   ```

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
