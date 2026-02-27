#!/usr/bin/env python3
"""
Generate platform icon PNGs for a Flutter app from a single master image (PNG or SVG).

- Android launcher icons (mipmap-*: ic_launcher, ic_launcher_round, ic_launcher_foreground)
- iOS AppIcon.appiconset icons
- macOS AppIcon.appiconset icons
- Windows multi-size .ico for Flutter (windows/runner/resources/app_icon.ico)
- Linux desktop icon (linux/flutter/app_icon.png)
- Web favicon and PWA icons (web/favicon.png, web/icons/Icon-*.png)
- Store listing icons (appstore.png, playstore.png)

Optional (must be explicitly requested via --platform):
- ios-legacy: older iOS icon sizes (57x57, 50x50, 72x72)
- watch: Apple Watch icons for all case sizes (38mm–49mm)

Usage:
    python generate_flutter_icons.py master_icon.png /path/to/flutter_project
    python generate_flutter_icons.py master_icon.svg /path/to/flutter_project

PNG input is resized with Pillow (LANCZOS). SVG input requires pyvips
(pip install pyvips) and each icon is rasterized directly from the vector
at its exact target size for maximum sharpness.

The flutter_project path should be the root (with android/, ios/, linux/, macos/, web/, windows/ folders).
"""

import argparse
import io
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


IOS_PLATFORM = "ios"


def get_ios_icons(base: Path):
    """
    Return mapping of output path -> pixel size for iOS AppIcon.appiconset.
    These filenames match the typical Xcode / Flutter Runner template.
    Apple requires iOS icons to have no alpha channel / transparency.
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
    Filenames match the Flutter template (named by pixel size, no @2x suffixes).
    Shared files (e.g. app_icon_32.png serves both 16@2x and 32@1x) are handled
    by Contents.json; we just need one file per unique pixel size.
    """
    appicon_dir = base / "macos" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    return {
        appicon_dir / "app_icon_16.png": 16,
        appicon_dir / "app_icon_32.png": 32,
        appicon_dir / "app_icon_64.png": 64,
        appicon_dir / "app_icon_128.png": 128,
        appicon_dir / "app_icon_256.png": 256,
        appicon_dir / "app_icon_512.png": 512,
        appicon_dir / "app_icon_1024.png": 1024,
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


def get_store_icons(base: Path):
    """Return mapping of output path -> pixel size for store listing icons.

    appstore.png  — 1024x1024 (Apple App Store marketing icon)
    playstore.png — 512x512   (Google Play Store listing icon)
    """
    return {
        base / "appstore.png": 1024,
        base / "playstore.png": 512,
    }


def get_ios_legacy_icons(base: Path):
    """Return mapping of output path -> pixel size for legacy iOS icon sizes.

    These are older sizes dropped from the current Flutter template but still
    referenced by some Xcode projects and older deployment targets:
      57x57 @1x/@2x (legacy iPhone app icon)
      50x50 @1x/@2x (legacy iPad Spotlight)
      72x72 @1x/@2x (legacy iPad app icon)
    """
    appicon_dir = base / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    return {
        appicon_dir / "Icon-App-57x57@1x.png": 57,
        appicon_dir / "Icon-App-57x57@2x.png": 114,

        appicon_dir / "Icon-App-50x50@1x.png": 50,
        appicon_dir / "Icon-App-50x50@2x.png": 100,

        appicon_dir / "Icon-App-72x72@1x.png": 72,
        appicon_dir / "Icon-App-72x72@2x.png": 144,
    }


def get_watch_icons(base: Path):
    """Return mapping of output path -> pixel size for Apple Watch icons.

    Covers all watch case sizes (38mm–49mm) for launcher, notification,
    and quick look roles. Companion settings icons (58px, 87px) are not
    included here as they are shared with the standard iOS icon set.
    """
    appicon_dir = base / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    return {
        # Notification center
        appicon_dir / "Icon-Watch-24x24@2x.png": 48,     # 38mm
        appicon_dir / "Icon-Watch-27.5x27.5@2x.png": 55, # 42mm
        appicon_dir / "Icon-Watch-33x33@2x.png": 66,     # 45mm

        # App launcher
        appicon_dir / "Icon-Watch-40x40@2x.png": 80,     # 38mm
        appicon_dir / "Icon-Watch-44x44@2x.png": 88,     # 40mm
        appicon_dir / "Icon-Watch-46x46@2x.png": 92,     # 41mm
        appicon_dir / "Icon-Watch-50x50@2x.png": 100,    # 44mm
        appicon_dir / "Icon-Watch-51x51@2x.png": 102,    # 45mm
        appicon_dir / "Icon-Watch-54x54@2x.png": 108,    # 49mm

        # Quick look
        appicon_dir / "Icon-Watch-86x86@2x.png": 172,    # 38mm
        appicon_dir / "Icon-Watch-98x98@2x.png": 196,    # 42mm
        appicon_dir / "Icon-Watch-108x108@2x.png": 216,  # 44mm
        appicon_dir / "Icon-Watch-117x117@2x.png": 234,  # 45mm
        appicon_dir / "Icon-Watch-129x129@2x.png": 258,  # 49mm
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

# PNG-based platform generators (all except windows which produces ICO)
PLATFORM_GENERATORS = {
    "android": get_android_icons,
    "ios": get_ios_icons,
    "macos": get_macos_icons,
    "linux": get_linux_icons,
    "web": get_web_icons,
    "store": get_store_icons,
    "ios-legacy": get_ios_legacy_icons,
    "watch": get_watch_icons,
}

# Default platforms included when no --platform is specified
DEFAULT_PLATFORMS = ["android", "ios", "macos", "linux", "web", "windows", "store"]

# Optional platforms that must be explicitly requested
OPTIONAL_PLATFORMS = ["ios-legacy", "watch"]

ALL_PLATFORMS = DEFAULT_PLATFORMS + OPTIONAL_PLATFORMS


# ------------ SVG rasterization -----------------


def _svg_to_pil(svg_path: Path, size: int) -> Image.Image:
    """Rasterize an SVG to a Pillow RGBA image at the given size using pyvips.

    The SVG is fitted within a size x size box (preserving aspect ratio),
    then centered on a transparent square canvas if the SVG is not square.
    """
    import pyvips
    image = pyvips.Image.thumbnail(str(svg_path), size, height=size)
    png_data = image.write_to_buffer(".png")
    rendered = Image.open(io.BytesIO(png_data)).convert("RGBA")

    # Pad to exact square if the SVG viewBox wasn't square
    if rendered.size != (size, size):
        square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - rendered.width) // 2, (size - rendered.height) // 2)
        square.paste(rendered, offset)
        return square
    return rendered


def _strip_alpha(img: Image.Image) -> Image.Image:
    """Composite an RGBA image onto a white background, returning an RGB image."""
    opaque = Image.new("RGB", img.size, (255, 255, 255))
    opaque.paste(img, mask=img.split()[3])
    return opaque


# ------------ core logic -----------------


def generate_icons(master_path: Path, project_root: Path, platforms=None):
    if not master_path.is_file():
        raise FileNotFoundError(f"Master icon not found: {master_path}")

    is_svg = master_path.suffix.lower() == ".svg"

    if is_svg:
        # Validate cairosvg is available before doing any work
        try:
            import pyvips  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "SVG input requires pyvips. Install it with:\n"
                "  pip install pyvips"
            )
        print("[INFO] SVG input — each icon will be rasterized at its exact target size.")
        svg_path = master_path
        img = None
    else:
        img = Image.open(master_path).convert("RGBA")
        svg_path = None
        w, h = img.size

        if w != h:
            print(f"[WARN] Master icon is not square ({w}x{h}). It will be padded to square with transparent pixels.")
            max_dim = max(w, h)
            square = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
            offset = ((max_dim - w) // 2, (max_dim - h) // 2)
            square.paste(img, offset)
            img = square
            w = h = max_dim

    if platforms is None:
        platforms = DEFAULT_PLATFORMS

    # Platforms whose icons must have no alpha channel (Apple rejects transparency)
    apple_icon_platforms = {IOS_PLATFORM, "ios-legacy", "watch"}

    # Collect PNG targets for selected platforms, tracking Apple paths separately
    all_targets = {}
    no_alpha_paths = set()
    for platform in platforms:
        if platform in PLATFORM_GENERATORS:
            targets = PLATFORM_GENERATORS[platform](project_root)
            if platform in apple_icon_platforms:
                no_alpha_paths.update(targets.keys())
            all_targets.update(targets)

    # Upscale warning (PNG only — SVG renders crisply at any size)
    if not is_svg:
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

            if is_svg:
                resized = _svg_to_pil(svg_path, size)
            else:
                resized = img.resize((size, size), Image.LANCZOS)

            # Apple icons must not contain an alpha channel (Apple rejects them)
            if out_path in no_alpha_paths:
                resized = _strip_alpha(resized)

            resized.save(out_path, format="PNG")
            rel = os.path.relpath(out_path, project_root)
            print(f"[OK] {size}x{size} -> {rel}")

    # Generate Windows multi-size ICO
    if "windows" in platforms:
        ico_path, windows_sizes = get_windows_ico_path_and_sizes(project_root)
        ico_path.parent.mkdir(parents=True, exist_ok=True)

        ico_frames = []
        for s in windows_sizes:
            if is_svg:
                ico_frames.append(_svg_to_pil(svg_path, s))
            else:
                ico_frames.append(img.resize((s, s), Image.LANCZOS))

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
        description="Generate Flutter platform icons from a master PNG or SVG."
    )
    parser.add_argument(
        "master_icon",
        help="Path to master image — PNG (preferably 1024x1024 with transparency) or SVG. "
             "SVG support requires pyvips (pip install pyvips).",
    )
    parser.add_argument(
        "project_root",
        help="Path to the root of the Flutter project (contains android/, ios/, linux/, macos/, web/, windows/).",
    )
    parser.add_argument(
        "--platform",
        help=f"Comma-separated list of platforms to generate. "
             f"Default: {', '.join(DEFAULT_PLATFORMS)}. "
             f"Optional extras: {', '.join(OPTIONAL_PLATFORMS)}.",
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
