# CLAUDE.md

## Project Overview

Single-file Python CLI tool that generates multi-resolution icon assets for Flutter apps from a master image (PNG or SVG). Outputs correctly sized/formatted icons for Android, iOS, macOS, Linux, Web, Windows, and Store listings.

## Key File

- `generate_flutter_icons.py` — the entire tool (~420 lines)

## Dependencies

- **Pillow** (required) — image manipulation
- **pyvips** (optional) — SVG rasterization

## Usage

```bash
python generate_flutter_icons.py <master_icon.png|.svg> <flutter_project_path> [--platform android,ios,...]
```

Default platforms: android, ios, macos, linux, web, windows, store
Optional platforms: ios-legacy, watch

## Code Architecture

- **Platform generators** (functions returning `dict[Path, int]`): `get_android_icons()`, `get_ios_icons()`, etc.
- **Registry pattern**: `PLATFORM_GENERATORS` dict maps platform names to generator functions
- **Core function**: `generate_icons()` orchestrates the workflow
- **CLI entry point**: `argparse`-based at bottom of file

## Conventions

- Single-file design — no modules, no packages
- `pathlib.Path` for all file operations
- Private functions prefixed with `_`
- Console output uses `[INFO]`, `[WARN]`, `[OK]` prefixes
- No type hints, no tests, no linting config
- Commit messages: simple present-tense (no conventional commits)

## Running

```bash
python generate_flutter_icons.py icon.png /path/to/flutter/project
python generate_flutter_icons.py icon.svg /path/to/flutter/project --platform android,ios
```
