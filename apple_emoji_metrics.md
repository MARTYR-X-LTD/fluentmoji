# Apple Color Emoji — Font Metrics Reference

Extracted from `/System/Library/Fonts/Apple Color Emoji.ttc` on macOS using fonttools.
Used as the target baseline for Fluent Emoji webfont metrics.

## Core Values

| Table | Metric | Value | Normalized (per UPM) |
|-------|--------|-------|----------------------|
| head  | unitsPerEm | 800 | 1.0 |
| hhea  | ascent | 800 | 1.0 |
| hhea  | descent | -250 | -0.3125 |
| hhea  | lineGap | 0 | 0 |
| OS/2  | sTypoAscender | 750 | 0.9375 |
| OS/2  | sTypoDescender | -250 | -0.3125 |
| OS/2  | sTypoLineGap | 0 | 0 |
| OS/2  | usWinAscent | 0 | — |
| OS/2  | usWinDescent | 0 | — |
| OS/2  | sxHeight | 500 | 0.625 |
| OS/2  | sCapHeight | 800 | 1.0 (= UPM) |
| hmtx  | advanceWidth (all emoji) | 800 | 1.0 (= UPM, perfectly square) |
| hmtx  | LSB (all emoji) | 0 | — |

## Key Takeaways

- **Advance width = UPM** — every emoji occupies exactly 1em, perfectly square, no extra space
- **LSB = 0** — no side bearings
- **usWinAscent/Descent = 0** — Apple relies on hhea/typo metrics, not Win metrics
- **sCapHeight = UPM** — emoji fill the full cap height

## Scaled to 1024 UPM (our fonts)

| Metric | Target value |
|--------|-------------|
| advanceWidth | 1024 |
| LSB | 0 |
| hhea ascent | 1024 |
| hhea descent | -320 |
| hhea lineGap | 0 |
| sTypoAscender | 960 |
| sTypoDescender | -320 |
| sTypoLineGap | 0 |
| sxHeight | 640 |
| sCapHeight | 1024 |
