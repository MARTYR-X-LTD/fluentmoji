# Fluent Emoji Webfonts

Optimized, subsetted [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) webfonts for the web. Built as unicode-range-split woff2 chunks so browsers only download the glyphs actually used on a page.

## Styles

- **Fluent Emoji Color** — full gradients, compositing, the works
- **Fluent Emoji Flat** — flat solid colors

Each style ships two format variants that share the same `font-family` name:

| Format | Browsers | CSS hint |
|--------|----------|----------|
| COLRv1 | Chrome, Firefox | `tech(color-COLRv1)` |
| OT-SVG | Safari | `tech(color-SVG)` |

The browser picks the right one automatically via the `tech()` function in `@font-face`.

## Usage

Include the CSS for the style you want:

```html
<link rel="stylesheet" href="dist/color/FluentEmojiColor.css">
<!-- or -->
<link rel="stylesheet" href="dist/flat/FluentEmojiFlat.css">
```

Then use it:

```css
p {
  font-family: sans-serif, 'Fluent Emoji Color';
}
```

Always place the text font first — the emoji font is a fallback. The browser uses it only for codepoints not found in the primary font.

Only the woff2 chunks matching the emoji codepoints on your page will be downloaded.

## Output structure

```
dist/
  color/
    colrv1/          # COLRv1 woff2 chunks (Chrome, Firefox)
    otsvg/           # OT-SVG woff2 chunks (Safari)
    FluentEmojiColor.css
  flat/
    colrv1/          # COLRv1 woff2 chunks
    otsvg/           # OT-SVG woff2 chunks
    FluentEmojiFlat.css
```

## Building

### Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [ninja](https://ninja-build.org/) (build system, used by nanoemoji)

**macOS:**

```bash
brew install uv ninja
```

**Arch Linux:**

```bash
pacman -S python uv ninja
```

Or install `uv` via the official installer: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Build

```bash
./build.sh
```

The build script will:

1. Create a venv and install dependencies (`nanoemoji`, `picosvg`, `fonttools`, `brotli`)
2. Prepare SVGs — map unicode codepoints from metadata, symlink to nanoemoji-compatible filenames
3. Compile 4 fonts via nanoemoji (COLRv1 + OT-SVG for each style)
4. Fix font metrics on each TTF to match Apple Color Emoji baselines
5. Subset each font into ~30-glyph woff2 chunks via `pyftsubset`
6. Generate CSS with `@font-face` rules, `unicode-range`, and `tech()` hints

### Scripts

| Script | Purpose |
|--------|---------|
| `prepare.py` | Walks fluentui-emoji assets, reads `metadata.json` for unicode mappings, creates symlinked SVGs with nanoemoji-compatible names |
| `build.sh` | Orchestrates the full pipeline: deps, prepare, compile, fix metrics, subset, CSS |
| `fix_metrics.py` | Post-processes compiled TTFs to match Apple Color Emoji metrics (advance width, vertical metrics) |
| `generate_css.py` | Reads chunk ranges and emits `@font-face` rules with `tech()` hints |

## How it works

Fluent Emoji SVGs live in [fluentui-emoji](https://github.com/microsoft/fluentui-emoji) with descriptive filenames. Each emoji directory contains a `metadata.json` with unicode codepoint(s), including ZWJ sequences and skin tone variants.

`prepare.py` reads these and creates symlinks named `emoji_uXXXX.svg` (the format nanoemoji expects). nanoemoji then compiles them into OpenType color fonts, automatically running picosvg normalization on the SVGs.

The compiled fonts are split into unicode-range chunks and compressed to woff2. The generated CSS uses the `tech()` function so Chrome/Firefox get COLRv1 and Safari gets OT-SVG, all under the same font-family name.

## Known issues

Some Color SVGs have `<mask>` elements or degenerate gradient transforms that picosvg can't normalize. Affected glyphs are skipped silently and fall back to the system emoji font. Fix them manually in Inkscape if needed.

## Source

SVGs from [microsoft/fluentui-emoji](https://github.com/microsoft/fluentui-emoji) (MIT License).

Built with [nanoemoji](https://github.com/googlefonts/nanoemoji), [picosvg](https://github.com/googlefonts/picosvg), and [fonttools](https://github.com/fonttools/fonttools).
