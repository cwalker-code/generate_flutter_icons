#!/usr/bin/env python3
"""
Generate platform icon PNGs for a Flutter app from a single master PNG.

- Android launcher icons (mipmap-*: ic_launcher, ic_launcher_round, ic_launcher_foreground)
- iOS AppIcon.appiconset icons
- macOS AppIcon.appiconset icons
- Windows multi-size .ico for Flutter (windows/runner/resources/app_icon.ico)
- Linux desktop icon (linux/flutter/app_icon.png)
- Web favicon and PWA icons (web/favicon.png, web/icons/Icon-*.png)

Usage:
    python generate_flutter_icons.py master_icon.png /path/to/flutter_project

The flutter_project path should be the root (with android/, ios/, linux/, macos/, web/, windows/ folders).
"""

import argparse
import os
from pathlib import Path

from PIL import Image


# ------------ CONFIG: output sizes & paths -----------------


def get_android_icons(base: Path):
    """Return mapping of output path -> pixel size for Android launcher icons.

    Generates ic_launcher, ic_launcher_round, and ic_launcher_foreground
    at each mipmap density. The foreground is used by the adaptive icon system
    (Android 8.0+); it should be 108dp (1.5x the 72dp visible area) to allow
    the launcher to mask and animate correctly.
    """
    res_base = base / "android" / "app" / "src" / "main" / "res"
    densities = {
        "mipmap-mdpi": 1,
        "mipmap-hdpi": 1.5,
        "mipmap-xhdpi": 2,
        "mipmap-xxhdpi": 3,
        "mipmap-xxxhdpi": 4,
    }
    targets = {}
    for folder, scale in densities.items():
        # Standard launcher icon: 48dp
        targets[res_base / folder / "ic_launcher.png"] = int(48 * scale)
        # Round launcher icon: 48dp (same size, used by launchers that show round icons)
        targets[res_base / folder / "ic_launcher_round.png"] = int(48 * scale)
        # Adaptive foreground layer: 108dp (provides bleed area for masking)
        targets[res_base / folder / "ic_launcher_foreground.png"] = int(108 * scale)
    return targets


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
        appicon_dir / "Icon-App-20x20@1x.png": 20,
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


def get_linux_icons(base: Path):
    """Return mapping of output path -> pixel size for Linux desktop icon."""
    return {
        base / "linux" / "flutter" / "app_icon.png": 256,
    }


def get_web_icons(base: Path):
    """Return mapping of output path -> pixel size for web favicon and PWA icons."""
    web_dir = base / "web"
    icons_dir = web_dir / "icons"
    return {
        web_dir / "favicon.png": 32,
        icons_dir / "Icon-192.png": 192,
        icons_dir / "Icon-512.png": 512,
        icons_dir / "Icon-maskable-192.png": 192,
        icons_dir / "Icon-maskable-512.png": 512,
    }


def get_windows_ico_path_and_sizes(base: Path):
    """
    Return the path for the Windows .ico file and the list of icon sizes (px).

    This follows the Flutter Windows template icon path:
        windows/runner/resources/app_icon.ico

    Sizes are chosen based on Windows 11 scale-factor usage:
      Context/menu/tray, taskbar, Start pins → combined unique list:
      16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 256
    """
    ico_path = base / "windows" / "runner" / "resources" / "app_icon.ico"
    windows_sizes = [16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 256]
    return ico_path, windows_sizes


# ------------ platform registry -----------------

PLATFORM_GENERATORS = {
    "android": get_android_icons,
    "ios": get_ios_icons,
    "macos": get_macos_icons,
    "linux": get_linux_icons,
    "web": get_web_icons,
}

ALL_PLATFORMS = list(PLATFORM_GENERATORS.keys()) + ["windows"]


# ------------ core logic -----------------


def generate_icons(master_path: Path, project_root: Path, platforms=None):
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

    if platforms is None:
        platforms = ALL_PLATFORMS

    # Collect PNG targets for selected platforms
    all_targets = {}
    for platform in platforms:
        if platform in PLATFORM_GENERATORS:
            all_targets.update(PLATFORM_GENERATORS[platform](project_root))

    # Check if master icon is smaller than the largest target across all selected platforms
    all_sizes = list(all_targets.values())
    if "windows" in platforms:
        _, windows_sizes = get_windows_ico_path_and_sizes(project_root)
        all_sizes.extend(windows_sizes)
    if all_sizes:
        max_target = max(all_sizes)
        if w < max_target:
            print(
                f"[WARN] Master icon is {w}px, but max target size is {max_target}px. "
                f"Upscaling may reduce quality."
            )

    if all_targets:
        # Generate platform PNGs
        for out_path, size in sorted(all_targets.items(), key=lambda kv: kv[1]):
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Resize with high-quality resampling
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(out_path, format="PNG")
            rel = os.path.relpath(out_path, project_root)
            print(f"[OK] {size}x{size} -> {rel}")

    # Generate Windows multi-size ICO with explicit LANCZOS resizing per frame
    if "windows" in platforms:
        ico_path, windows_sizes = get_windows_ico_path_and_sizes(project_root)
        ico_path.parent.mkdir(parents=True, exist_ok=True)

        ico_frames = []
        for s in windows_sizes:
            ico_frames.append(img.resize((s, s), Image.LANCZOS))
        # Save the smallest frame and append the rest; Pillow writes all as ICO entries
        ico_frames[0].save(
            ico_path, format="ICO", append_images=ico_frames[1:], sizes=[(s, s) for s in windows_sizes]
        )
        rel_ico = os.path.relpath(ico_path, project_root)
        sizes_str = ", ".join(f"{s}x{s}" for s in windows_sizes)
        print(f"[OK] ICO ({sizes_str}) -> {rel_ico}")

    # Summary
    file_count = len(all_targets) + (1 if "windows" in platforms else 0)
    print(f"\nGenerated {file_count} icon(s) for: {', '.join(platforms)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Flutter platform icons from a master PNG."
    )
    parser.add_argument(
        "master_icon",
        help="Path to master PNG (preferably 1024x1024 with transparency).",
    )
    parser.add_argument(
        "project_root",
        help="Path to the root of the Flutter project (contains android/, ios/, linux/, macos/, web/, windows/).",
    )
    parser.add_argument(
        "--platform",
        help=f"Comma-separated list of platforms to generate (default: all). "
             f"Choices: {', '.join(ALL_PLATFORMS)}.",
    )
    args = parser.parse_args()

    master_path = Path(args.master_icon).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve()

    platforms = None
    if args.platform:
        platforms = [p.strip().lower() for p in args.platform.split(",")]
        invalid = [p for p in platforms if p not in ALL_PLATFORMS]
        if invalid:
            parser.error(f"Unknown platform(s): {', '.join(invalid)}. Choose from: {', '.join(ALL_PLATFORMS)}")

    generate_icons(master_path, project_root, platforms=platforms)


if __name__ == "__main__":
    main()
