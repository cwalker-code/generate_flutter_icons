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
| `--platform` | Optional comma-separated list: `android`, `ios`, `macos`, `linux`, `web`, `windows` |

**Examples:**

```bash
# Generate icons for all platforms
python generate_flutter_icons.py icon.png ./my_flutter_app

# Generate only for web and android
python generate_flutter_icons.py icon.png ./my_flutter_app --platform android,web

# Generate only the Windows ICO
python generate_flutter_icons.py icon.png ./my_flutter_app --platform windows
```

## What it generates

### Android (15 files)
`ic_launcher.png`, `ic_launcher_round.png`, and `ic_launcher_foreground.png` at each mipmap density (mdpi through xxxhdpi).

Output: `android/app/src/main/res/mipmap-*/`

### iOS (14 files)
All `AppIcon.appiconset` sizes from 20x20@1x through 1024x1024@1x, matching the standard Flutter/Xcode template filenames.

Output: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

### macOS (10 files)
All `AppIcon.appiconset` sizes from 16px through 1024px (including @2x variants).

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

## Notes

- Non-square master images are automatically padded to square with transparent pixels.
- A warning is shown if the master image is smaller than the largest target size.
- All PNG resizing uses LANCZOS resampling for best quality.
- Windows ICO frames are individually resized with LANCZOS before being packed.

## License

[MIT](LICENSE)
