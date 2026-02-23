# generate_flutter_icons

Generate all platform icon assets for a Flutter app from a single master PNG.

One command replaces your icons across Android, iOS, macOS, Windows, Linux, and Web — matching the exact paths and filenames Flutter expects.

## Requirements

- Python 3.7+
- [Pillow](https://pypi.org/project/Pillow/)

```bash
pip install Pillow
```

## Usage

```bash
python generate_flutter_icons.py <master_icon> <project_root> [--platform <platforms>]
```

**Arguments:**

| Argument | Description |
|---|---|
| `master_icon` | Path to your master PNG (ideally 1024x1024 with transparency) |
| `project_root` | Root of your Flutter project (contains `android/`, `ios/`, etc.) |
| `--platform` | Comma-separated list of platforms (see below) |

**Default platforms** (included when `--platform` is omitted):
`android`, `ios`, `macos`, `linux`, `web`, `windows`, `store`

**Optional platforms** (must be explicitly requested):
`ios-legacy`, `watch`

**Examples:**

```bash
# Generate all default platform icons
python generate_flutter_icons.py icon.png ./my_flutter_app

# Generate only for web and android
python generate_flutter_icons.py icon.png ./my_flutter_app --platform android,web

# Generate defaults plus Apple Watch icons
python generate_flutter_icons.py icon.png ./my_flutter_app --platform android,ios,macos,linux,web,windows,store,watch

# Generate only legacy iOS icons
python generate_flutter_icons.py icon.png ./my_flutter_app --platform ios-legacy
```

## What it generates

### Android (15 files)
`ic_launcher.png`, `ic_launcher_round.png`, and `ic_launcher_foreground.png` at each mipmap density (mdpi through xxxhdpi).

Output: `android/app/src/main/res/mipmap-*/`

### iOS (14 files)
All `AppIcon.appiconset` sizes from 20x20@1x through 1024x1024@1x, matching the standard Flutter/Xcode template filenames. Alpha channel is stripped (Apple requirement).

Output: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

### macOS (7 files)
All `AppIcon.appiconset` sizes from 16px through 1024px, named by pixel size to match the Flutter template.

Output: `macos/Runner/Assets.xcassets/AppIcon.appiconset/`

### Windows (1 file)
A single multi-size `.ico` containing 14 sizes (16px through 256px) covering all Windows 11 scale factors.

Output: `windows/runner/resources/app_icon.ico`

### Linux (1 file)
A 256x256 PNG for the desktop icon.

Output: `linux/flutter/app_icon.png`

### Web (5 files)
Favicon (32x32) and PWA icons (192px, 512px, plus maskable variants).

Output: `web/favicon.png` and `web/icons/`

### Store (2 files)
Standalone store listing icons for convenience:
- `appstore.png` — 1024x1024 (Apple App Store)
- `playstore.png` — 512x512 (Google Play Store)

Output: project root

### iOS Legacy (6 files) — optional
Older icon sizes dropped from the current Flutter template: 57x57, 50x50, and 72x72 at @1x/@2x. Useful if targeting older iOS versions.

Output: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

### Apple Watch (14 files) — optional
Icons for all watch case sizes (38mm–49mm) covering launcher, notification, and quick look roles.

Output: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

## Notes

- Non-square master images are automatically padded to square with transparent pixels.
- iOS, legacy iOS, and Apple Watch icons are flattened to RGB (no alpha) as required by Apple.
- A warning is shown if the master image is smaller than the largest target size.
- All PNG resizing uses LANCZOS resampling for best quality.
- Windows ICO frames are individually resized with LANCZOS before being packed.

## License

[MIT](LICENSE)
