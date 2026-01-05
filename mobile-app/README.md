# Kigali Mobility

Public transport navigation app for Kigali, Rwanda. Built with [Trufi Core](https://github.com/trufi-association/trufi-core) v5.0.0.

## Features

- Route planning with OpenTripPlanner
- Location search with Photon geocoding
- MapLibre vector maps
- Saved places
- Transport line list
- Fare information
- Light and dark mode support

## Configuration

### Backends

| Service | URL |
|---------|-----|
| OTP (Routing) | https://otp.kigali.trufi.dev |
| Photon (Search) | https://photon.kigali.trufi.dev |
| Maps (Tiles) | https://maps.kigali.trufi.dev |

### Map Center

- Latitude: -1.929701
- Longitude: 30.129698

## Getting Started

### Prerequisites

- Flutter SDK ^3.10.0
- Android Studio / Xcode
- Connected device or emulator

### Installation

```bash
# Get dependencies
flutter pub get

# Run on connected device
flutter run
```

### Build

```bash
# Android APK
flutter build apk

# Android App Bundle
flutter build appbundle

# iOS
flutter build ios

# Web
flutter build web
```

## Platforms

- Android (minSdk 24)
- iOS
- Web

## Project Structure

```
lib/
  main.dart          # App configuration and entry point
assets/
  images/            # App images
  pois/              # POI GeoJSON files (optional)
android/             # Android platform files
ios/                 # iOS platform files
web/                 # Web platform files
```

## License

This project uses Trufi Core which is licensed under the GPL-3.0 license.

## Links

- [Trufi Association](https://www.trufi-association.org)
- [Trufi Core](https://github.com/trufi-association/trufi-core)
