# Fluentmoji

Optimized, subsetted [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) webfonts for the web. Built as unicode-range-split woff2 chunks so browsers only download the glyphs actually used on a page. Some work and inspiration from [tetunori/fluent-emoji-webfont](https://github.com/tetunori/fluent-emoji-webfont).

## So... what's the deal?

I like emojis. They are an underrated art form. And subjective as well. I love the ones from Microsoft. And I want to use them in my work and personal projects.

But... how do you do it? Existant solutions that monkey-patch emojis in place client-side via javascript are finicky. They are, indeed, a hack. I want something clean. Something that does not involve network roundtrips for each emoji.

We, then, are left with using emoji fonts. They are a thing, and browsers can use them! With.. some observations:

- Emoji fonts are BIG in size. I mean, yes, for the people who ship +5MB javascript bundle to render a button there might not be a problem with it. But I do care. And every single person surfing the web.

- Emoji fonts are yet not properly standarized. The best we have is COLRv1, which is supported by Chrome and Firefox. And then we have OT-SVG, with Safari and Firefox. There is a gap there. We can't choose one or the other. It must be the two. Browser development... what do we do with them?

- Seems like we can merge both standards into the same font file. We are increasing the problem about size, though...

- There are other standards, like something related to bitmaps (I don't remember exactly. Yes, I'm not an LLM writing this), which should work universally. The problem is, these usually result in huge files and they are rasterized graphics at the end of the day. They don't scale with resolution.


## Hey, we have the technology! 🎉 

Enter `@font-face tech()` and `unicode-range`, both CSS technologies. And to think there are people who dislike CSS. With `tech()` we can fetch the emoji standard the browser supports automatically, and ``unicode-range` implies we can do font-subsetting. Basically, split each font into many different chunks. So if we have one emoji in the page, instead of fetching the whole font, it will only fetch the small chunk that includes it. This is also figured out by the browser at run time.

## Usage

Get the latest fonts from the [releases page](https://github.com/MARTYR-X-LTD/fluentmoji/releases).

### Quick start

Include the CSS for the style you want:

```html
<!-- Color style (with gradients, 3D style) -->
<link rel="stylesheet" href="path/to/dist/color/FluentEmojiColor.css">

<!-- Or Flat style (solid colors) -->
<link rel="stylesheet" href="path/to/dist/flat/FluentEmojiFlat.css">
```

Then use it in your CSS:

```css
p {
  font-family: sans-serif, 'Fluent Emoji Color';
  /* or: font-family: sans-serif, 'Fluent Emoji Flat'; */
}
```

Always place the text font first — the emoji font is a fallback. The browser uses it only for codepoints not found in the primary font.

### How it works

As mentioned, `@font-face` with `tech()` hints to automatically serve the right format, and with `unicode-range` it only fetches the chunk needed to render the specific glyph (emoji):

```css
@font-face {
  font-family: 'Fluent Emoji Color';
  src:
    url('colrv1/chunk-000.woff2') format('woff2') tech(color-COLRv1),
    url('otsvg/chunk-000.woff2') format('woff2') tech(color-SVG);
  unicode-range: U+1F600, U+1F601, U+1F602;
  font-display: swap;
}
```

- **Chrome & Firefox** → load COLRv1 (~1.2 MB total, ~26 KB per chunk)
- **Safari** → load OT-SVG (~2.5 MB total, ~52 KB per chunk)

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

Some Color SVGs have `<mask>` elements that picosvg can't normalize. These are automatically filtered out during the prepare step and fall back to the system emoji font.

## Source

SVGs from [microsoft/fluentui-emoji](https://github.com/microsoft/fluentui-emoji) (MIT License).

Built with [nanoemoji](https://github.com/googlefonts/nanoemoji), [picosvg](https://github.com/googlefonts/picosvg), and [fonttools](https://github.com/fonttools/fonttools).
