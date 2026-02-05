#!/usr/bin/env python3
"""
Generate platform icon PNGs for a Flutter app from a single master PNG.

- Android launcher icons (mipmap-*)
- iOS AppIcon.appiconset icons
- macOS AppIcon.appiconset icons

Usage:
    python generate_flutter_icons.py master_icon.png /path/to/flutter_project

The flutter_project path should be the root (with android/, ios/, macos/ folders).
"""

import argparse
import os
from pathlib import Path

from PIL import Image


# ------------ CONFIG: output sizes & paths -----------------

def get_android_icons(base: Path):
    """Return mapping of output path -> pixel size for Android launcher icons."""
    res_base = base / "android" / "app" / "src" / "main" / "res"
    return {
        # 48dp launcher at different densities
        res_base / "mipmap-mdpi" / "ic_launcher.png": 48,
        res_base / "mipmap-hdpi" / "ic_launcher.png": 72,
        res_base / "mipmap-xhdpi" / "ic_launcher.png": 96,
        res_base / "mipmap-xxhdpi" / "ic_launcher.png": 144,
        res_base / "mipmap-xxxhdpi" / "ic_launcher.png": 192,
    }


def get_ios_icons(base: Path):
    """
    Return mapping of output path -> pixel size for iOS AppIcon.appiconset.
    These filenames match the typical Xcode / Flutter Runner template.
    You may need to tweak ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json
    to reference these if it differs.
    """
    appicon_dir = base / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    return {
        # iPhone & iPad notification / settings / spotlight / app icons
        appicon_dir / "Icon-App-20x20@2x.png": 40,
        appicon_dir / "Icon-App-20x20@3x.png": 60,

        appicon_dir / "Icon-App-29x29@1x.png": 29,
        appicon_dir / "Icon-App-29x29@2x.png": 58,
        appicon_dir / "Icon-App-29x29@3x.png": 87,

        appicon_dir / "Icon-App-40x40@1x.png": 40,
        appicon_dir / "Icon-App-40x40@2x.png": 80,
        appicon_dir / "Icon-App-40x40@3x.png": 120,

        appicon_dir / "Icon-App-60x60@2x.png": 120,
        appicon_dir / "Icon-App-60x60@3x.png": 180,

        appicon_dir / "Icon-App-76x76@1x.png": 76,
        appicon_dir / "Icon-App-76x76@2x.png": 152,
        appicon_dir / "Icon-App-83.5x83.5@2x.png": 167,

        # App Store / marketing icon
        appicon_dir / "Icon-App-1024x1024@1x.png": 1024,
    }


def get_macos_icons(base: Path):
    """
    Return mapping of output path -> pixel size for macOS AppIcon.appiconset.
    Names are generic but work fine if you adjust Contents.json accordingly.
    """
    appicon_dir = base / "macos" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    return {
        appicon_dir / "app_icon_16.png": 16,
        appicon_dir / "app_icon_16@2x.png": 32,

        appicon_dir / "app_icon_32.png": 32,
        appicon_dir / "app_icon_32@2x.png": 64,

        appicon_dir / "app_icon_128.png": 128,
        appicon_dir / "app_icon_128@2x.png": 256,

        appicon_dir / "app_icon_256.png": 256,
        appicon_dir / "app_icon_256@2x.png": 512,

        appicon_dir / "app_icon_512.png": 512,
        appicon_dir / "app_icon_512@2x.png": 1024,
    }


# ------------ core logic -----------------


def generate_icons(master_path: Path, project_root: Path):
    if not master_path.is_file():
        raise FileNotFoundError(f"Master icon not found: {master_path}")

    img = Image.open(master_path).convert("RGBA")
    w, h = img.size

    if w != h:
        print(f"[WARN] Master icon is not square ({w}x{h}). It will be resized with aspect preserved and padded.")
        # Make it square by padding to max dimension
        max_dim = max(w, h)
        square = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        offset = ((max_dim - w) // 2, (max_dim - h) // 2)
        square.paste(img, offset)
        img = square
        w = h = max_dim

    # Determine maximum size requested
    all_targets = {}
    all_targets.update(get_android_icons(project_root))
    all_targets.update(get_ios_icons(project_root))
    all_targets.update(get_macos_icons(project_root))

    max_target = max(all_targets.values())
    if w < max_target:
        print(f"[WARN] Master icon is {w}px, but max target size is {max_target}px. "
              f"Upscaling may reduce quality.")

    for out_path, size in sorted(all_targets.items(), key=lambda kv: kv[1]):
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Resize with high-quality resampling
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(out_path, format="PNG")
        rel = os.path.relpath(out_path, project_root)
        print(f"[OK] {size}x{size} -> {rel}")


def main():
    parser = argparse.ArgumentParser(description="Generate Flutter platform icons from a master PNG.")
    parser.add_argument("master_icon", help="Path to master PNG (preferably 1024x1024 with transparency).")
    parser.add_argument("project_root", help="Path to the root of the Flutter project (contains android/, ios/, macos/).")
    args = parser.parse_args()

    master_path = Path(args.master_icon).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve()

    generate_icons(master_path, project_root)


if __name__ == "__main__":
    main()
