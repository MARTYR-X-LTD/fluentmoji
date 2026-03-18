#!/usr/bin/env python3
"""
Generate @font-face CSS with unicode-range subsetting and tech() hints.

Reads chunk_ranges.csv files produced by build.sh and generates CSS files
that use format(woff2) tech() for browser-compatible font selection.
"""

import csv
from pathlib import Path

DIST = Path("dist")
BUILD = Path("build")


def read_chunk_ranges(style: str, font_name: str) -> list[tuple[str, str]]:
    """Read chunk_ranges.csv -> list of (filename, unicode_range)."""
    csv_path = BUILD / style / font_name / "chunk_ranges.csv"
    if not csv_path.exists():
        print(f"  WARN: {csv_path} not found")
        return []

    entries = []
    with open(csv_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: chunk-000.woff2,U+1F600,U+1F601,...
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            filename = parts[0]
            unicode_range = parts[1]
            entries.append((filename, unicode_range))

    return entries


def generate_color_css():
    """Generate CSS for Color style with COLRv1 + OT-SVG fallback via tech()."""
    colrv1_chunks = read_chunk_ranges("color", "FluentEmojiColor-COLRv1")
    otsvg_chunks = read_chunk_ranges("color", "FluentEmojiColor-SVG")

    if not colrv1_chunks and not otsvg_chunks:
        print("  No color chunks found, skipping CSS")
        return

    css_path = DIST / "color" / "FluentEmojiColor.css"
    css_path.parent.mkdir(parents=True, exist_ok=True)

    # Build a mapping from unicode-range to chunk files
    # Both variants should have the same number of chunks with matching ranges
    # since they were subset from fonts with the same codepoints

    lines = []
    lines.append("/* Fluent Emoji Color — auto-generated, do not edit */\n")

    # If both variants have matching chunks, combine them into single @font-face rules
    if len(colrv1_chunks) == len(otsvg_chunks):
        for (colr_file, colr_range), (svg_file, _svg_range) in zip(colrv1_chunks, otsvg_chunks):
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Color';")
            lines.append("  src:")
            lines.append(f"    url('colrv1/{colr_file}') format(woff2) tech(color-COLRv1),")
            lines.append(f"    url('otsvg/{svg_file}')  format(woff2) tech(color-SVG);")
            lines.append(f"  unicode-range: {colr_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")
    else:
        # Fallback: separate @font-face blocks per format
        for colr_file, colr_range in colrv1_chunks:
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Color';")
            lines.append(f"  src: url('colrv1/{colr_file}') format(woff2) tech(color-COLRv1);")
            lines.append(f"  unicode-range: {colr_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")
        for svg_file, svg_range in otsvg_chunks:
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Color';")
            lines.append(f"  src: url('otsvg/{svg_file}') format(woff2) tech(color-SVG);")
            lines.append(f"  unicode-range: {svg_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")

    with open(css_path, "w") as f:
        f.write("\n".join(lines))

    print(f"  Written: {css_path} ({len(colrv1_chunks)} chunks)")


def generate_flat_css():
    """Generate CSS for Flat style with COLRv1 + OT-SVG fallback."""
    colrv1_chunks = read_chunk_ranges("flat", "FluentEmojiFlat-COLRv1")
    otsvg_chunks = read_chunk_ranges("flat", "FluentEmojiFlat-SVG")

    if not colrv1_chunks and not otsvg_chunks:
        print("  No flat chunks found, skipping CSS")
        return

    css_path = DIST / "flat" / "FluentEmojiFlat.css"
    css_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("/* Fluent Emoji Flat — auto-generated, do not edit */\n")

    if len(colrv1_chunks) == len(otsvg_chunks):
        for (colr_file, colr_range), (svg_file, _svg_range) in zip(colrv1_chunks, otsvg_chunks):
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Flat';")
            lines.append("  src:")
            lines.append(f"    url('colrv1/{colr_file}') format(woff2) tech(color-COLRv1),")
            lines.append(f"    url('otsvg/{svg_file}')  format(woff2) tech(color-SVG);")
            lines.append(f"  unicode-range: {colr_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")
    else:
        for colr_file, colr_range in colrv1_chunks:
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Flat';")
            lines.append(f"  src: url('colrv1/{colr_file}') format(woff2) tech(color-COLRv1);")
            lines.append(f"  unicode-range: {colr_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")
        for svg_file, svg_range in otsvg_chunks:
            lines.append("@font-face {")
            lines.append("  font-family: 'Fluent Emoji Flat';")
            lines.append(f"  src: url('otsvg/{svg_file}') format(woff2) tech(color-SVG);")
            lines.append(f"  unicode-range: {svg_range};")
            lines.append("  font-display: swap;")
            lines.append("}\n")

    with open(css_path, "w") as f:
        f.write("\n".join(lines))

    print(f"  Written: {css_path} ({len(colrv1_chunks)} chunks)")


def main():
    generate_color_css()
    generate_flat_css()


if __name__ == "__main__":
    main()
