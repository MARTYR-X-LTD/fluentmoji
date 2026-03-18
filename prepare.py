#!/usr/bin/env python3
"""
Prepare Fluent Emoji SVGs for nanoemoji compilation.

Walks the fluentui-emoji asset tree, reads metadata.json for unicode mappings,
and creates symlinked SVG files with nanoemoji-compatible names (emoji_uXXXX.svg).
Also generates glyphmap CSV files for each variant.
"""

import json
import os
import sys
from pathlib import Path

ASSETS_DIR = Path("fluentui-emoji/assets")
BUILD_DIR = Path("build")
STYLES = {
    "color": "Color",
    "flat": "Flat",
}

# Skin tone modifier directory names → modifier codepoints
SKIN_TONE_MAP = {
    "Light": "1f3fb",
    "Medium-Light": "1f3fc",
    "Medium": "1f3fd",
    "Medium-Dark": "1f3fe",
    "Dark": "1f3ff",
    "Default": None,  # uses base codepoint
}


def read_metadata(emoji_dir: Path) -> dict | None:
    meta_path = emoji_dir / "metadata.json"
    if not meta_path.exists():
        return None
    try:
        with open(meta_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  WARN: Failed to read {meta_path}: {e}", file=sys.stderr)
        return None


def codepoints_to_filename(codepoints: str) -> str:
    """Convert space-separated hex codepoints to nanoemoji filename.
    e.g. '1f600' -> 'emoji_u1f600.svg'
    e.g. '2764 fe0f' -> 'emoji_u2764.svg'  (trailing fe0f stripped)
    e.g. '26f9 fe0f 200d 2640 fe0f' -> 'emoji_u26f9_fe0f_200d_2640_fe0f.svg'
    """
    parts = codepoints.strip().split()
    # Strip trailing fe0f (variation selector 16) — sequences that end with
    # only fe0f get mapped directly by codepoint so Chrome finds them without
    # needing a GSUB ligature lookup.
    if len(parts) == 2 and parts[-1] == "fe0f":
        parts = parts[:1]
    return "emoji_u" + "_".join(parts) + ".svg"


def collect_emoji_entries(style_key: str, style_dir_name: str) -> list[dict]:
    """Collect all SVG -> unicode mappings for a style."""
    entries = []
    skipped = 0

    for emoji_dir in sorted(ASSETS_DIR.iterdir()):
        if not emoji_dir.is_dir():
            continue

        meta = read_metadata(emoji_dir)
        if meta is None:
            continue

        unicode_str = meta.get("unicode", "")
        if not unicode_str:
            continue

        skin_tones = meta.get("unicodeSkintones")
        has_skin_tones = skin_tones and len(skin_tones) > 1

        if has_skin_tones:
            # Process skin tone variants
            for tone_dir_name, tone_modifier in SKIN_TONE_MAP.items():
                if tone_dir_name == "Default":
                    # Default variant uses base unicode
                    variant_dir = emoji_dir / "Default" / style_dir_name
                    variant_unicode = unicode_str
                else:
                    variant_dir = emoji_dir / tone_dir_name / style_dir_name
                    # Find matching unicode from unicodeSkintones
                    variant_unicode = None
                    for st in skin_tones:
                        if tone_modifier in st and st != unicode_str:
                            variant_unicode = st
                            break
                    if variant_unicode is None:
                        continue

                # Find SVG file in variant dir
                if not variant_dir.exists():
                    continue
                svg_files = list(variant_dir.glob("*.svg"))
                if not svg_files:
                    continue

                entries.append({
                    "svg_path": svg_files[0],
                    "unicode": variant_unicode,
                    "name": meta.get("cldr", emoji_dir.name),
                })
        else:
            # No skin tones - look for SVG directly in style dir
            style_dir = emoji_dir / style_dir_name
            if not style_dir.exists():
                # Some emojis might not have all styles
                skipped += 1
                continue

            svg_files = list(style_dir.glob("*.svg"))
            if not svg_files:
                skipped += 1
                continue

            entries.append({
                "svg_path": svg_files[0],
                "unicode": unicode_str,
                "name": meta.get("cldr", emoji_dir.name),
            })

    if skipped:
        print(f"  Skipped {skipped} emojis without {style_dir_name} SVGs")

    return entries


def svg_is_compatible(svg_path: Path) -> bool:
    """Return False if the SVG contains elements picosvg cannot handle."""
    try:
        content = svg_path.read_text(errors="replace")
        if "<mask" in content:
            return False
    except OSError:
        return False
    return True


def create_symlinks_and_glyphmap(style_key: str, entries: list[dict]):
    """Create symlinked SVGs with nanoemoji-compatible names and a glyphmap CSV."""
    svg_dir = BUILD_DIR / style_key / "svgs"
    svg_dir.mkdir(parents=True, exist_ok=True)

    glyphmap_path = BUILD_DIR / style_key / "glyphmap.csv"
    seen_unicodes = set()
    written = 0

    with open(glyphmap_path, "w") as gm:
        for entry in entries:
            unicode_str = entry["unicode"]

            # Skip duplicates
            if unicode_str in seen_unicodes:
                continue
            seen_unicodes.add(unicode_str)

            if not svg_is_compatible(entry["svg_path"]):
                print(f"  SKIP (incompatible): {entry['svg_path'].name}")
                continue

            filename = codepoints_to_filename(unicode_str)
            link_path = svg_dir / filename
            src_path = entry["svg_path"].resolve()

            # Create symlink (overwrite if exists)
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink()
            link_path.symlink_to(src_path)

            # Glyphmap CSV: filename, codepoints (0xHEX space-separated), glyph_name
            cps = " ".join(f"0x{cp}" for cp in unicode_str.split())
            glyph_name = "emoji_u" + "_".join(unicode_str.split())
            gm.write(f"{link_path},{cps},{glyph_name}\n")
            written += 1

    print(f"  Created {written} symlinks in {svg_dir}")
    print(f"  Glyphmap: {glyphmap_path}")
    return written


def main():
    if not ASSETS_DIR.exists():
        print(f"ERROR: {ASSETS_DIR} not found. Clone fluentui-emoji first.", file=sys.stderr)
        sys.exit(1)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for style_key, style_dir_name in STYLES.items():
        print(f"\n=== Preparing {style_key} ({style_dir_name}) ===")
        entries = collect_emoji_entries(style_key, style_dir_name)
        print(f"  Found {len(entries)} emoji entries")
        count = create_symlinks_and_glyphmap(style_key, entries)
        print(f"  Total unique glyphs: {count}")


if __name__ == "__main__":
    main()
