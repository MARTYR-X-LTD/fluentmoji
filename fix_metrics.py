#!/usr/bin/env python3
"""
Fix font metrics on compiled Fluent Emoji TTFs.
Sets vertical metrics to match actual glyph bounds, consistent across all
hhea/OS2 typo/OS2 win tables. Based on tetunori/fluent-emoji-webfont reference.
"""

import sys
from fontTools.ttLib import TTFont


def fix_metrics(path: str) -> None:
    print(f"  Fixing metrics: {path}")
    font = TTFont(path)

    head = font["head"]
    y_max = head.yMax  # actual glyph top (e.g. 950)
    y_min = head.yMin  # actual glyph bottom (e.g. -250)

    hhea = font["hhea"]
    hhea.ascent  = y_max
    hhea.descent = y_min
    hhea.lineGap = 0

    os2 = font["OS/2"]
    os2.sTypoAscender  = y_max
    os2.sTypoDescender = y_min
    os2.sTypoLineGap   = 0
    os2.usWinAscent    = y_max
    os2.usWinDescent   = abs(y_min)

    font.save(path)
    print(f"  ascent={y_max} descent={y_min} — done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fix_metrics.py <font.ttf> [font2.ttf ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        fix_metrics(path)
