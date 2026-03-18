#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

BUILD="build"
DIST="dist"
CHUNK_SIZE=30  # glyphs per subset chunk
PROJECT_ROOT="$(pwd)"

# ─── Helpers ──────────────────────────────────────────────────────────────────

log()  { echo "==> $*"; }
warn() { echo "WARN: $*" >&2; }

ensure_deps() {
    if [ ! -d ".venv" ]; then
        log "Creating venv with uv (Python 3.12)..."
        uv venv --python 3.12
    fi
    log "Installing dependencies..."
    uv pip install nanoemoji fonttools brotli picosvg lxml 2>&1 | tail -3

    log "Patching nanoemoji to skip incompatible glyphs..."
    uv run python - <<'EOF'
import re, pathlib, sys

site = next(pathlib.Path(".venv/lib").glob("python3.*/site-packages/nanoemoji"))

# ninja.py: add -k 0 to keep going on individual SVG failures
ninja_py = site / "ninja.py"
src = ninja_py.read_text()
patched = src.replace(
    '["ninja", "-C",',
    '["ninja", "-k", "0", "-C",'
).replace(
    'subprocess.run(ninja_cmd, check=True)',
    'subprocess.run(ninja_cmd)'
)
if patched == src:
    print("ninja.py: already patched or unexpected content, skipping")
else:
    ninja_py.write_text(patched)
    print("ninja.py: patched")

# write_font.py: wrap color_glyphs.append in try/except to skip broken glyphs
wf_py = site / "write_font.py"
src = wf_py.read_text()
old = "        color_glyphs.append(\n            ColorGlyph.create("
new = "        try: color_glyphs.append(\n            ColorGlyph.create("
old_end = "            )\n        )\n    color_glyphs = tuple(color_glyphs)"
new_end = '            )\n        )\n        except Exception as e: print(f\'Skipping glyph due to error: {e}\')\n    color_glyphs = tuple(color_glyphs)'
patched = src.replace(old, new).replace(old_end, new_end)
if patched == src:
    print("write_font.py: already patched or unexpected content, skipping")
else:
    wf_py.write_text(patched)
    print("write_font.py: patched")
EOF
}

# ─── Step 1: Prepare ─────────────────────────────────────────────────────────

prepare() {
    if [ ! -d "fluentui-emoji" ]; then
        log "Cloning fluentui-emoji..."
        git clone --depth 1 https://github.com/microsoft/fluentui-emoji.git
    fi
    log "Running prepare.py..."
    uv run python prepare.py
}

# ─── Step 2: Compile fonts with nanoemoji ─────────────────────────────────────

compile_font() {
    local style=$1       # color, flat
    local format=$2      # glyf_colr_1, untouchedsvg
    local out_name=$3    # output filename (no extension)

    local svg_dir="$PROJECT_ROOT/$BUILD/$style/svgs"
    local build_dir="$PROJECT_ROOT/$BUILD/$style/$out_name"
    local output="$PROJECT_ROOT/$BUILD/$style/$out_name/${out_name}.ttf"

    mkdir -p "$build_dir"

    if [ -f "$output" ]; then
        log "  Font already exists: $output (skip)"
        return
    fi

    log "  Compiling $out_name ($format) from $svg_dir..."

    local svg_count
    svg_count=$(find "$svg_dir" -name '*.svg' | wc -l | tr -d ' ')
    log "  Found $svg_count SVGs"

    uv run nanoemoji \
        --color_format "$format" \
        --family "$out_name" \
        --output_file "$output" \
        --build_dir "$build_dir/ninja" \
        --ignore_reuse_error \
        --keep_glyph_names \
        "$svg_dir"/emoji_u*.svg \
        2>&1 | tee "$build_dir/nanoemoji.log" || {
            warn "nanoemoji failed for $out_name — check $build_dir/nanoemoji.log"
            return 1
        }

    # nanoemoji may nest the output inside the build dir — find it
    if [ ! -f "$output" ]; then
        local found
        found=$(find "$build_dir" -name "${out_name}.ttf" -type f | head -1)
        if [ -n "$found" ]; then
            mv "$found" "$output"
            log "  Moved output to $output"
        else
            warn "  Output not found for $out_name"
            return 1
        fi
    fi

    log "  Output: $output ($(du -h "$output" | cut -f1))"

    log "  Fixing font metrics..."
    uv run python "$PROJECT_ROOT/fix_metrics.py" "$output"
}

# ─── Step 3: Subset and compress ─────────────────────────────────────────────

subset_and_compress() {
    local style=$1       # color, flat
    local out_name=$2    # font name
    local sub_dir=$3     # colrv1, otsvg

    local font="$BUILD/$style/$out_name/${out_name}.ttf"
    local out_dir="$DIST/$style/$sub_dir"

    if [ ! -f "$font" ]; then
        warn "Font not found: $font — skipping subset"
        return 1
    fi

    mkdir -p "$out_dir"

    log "  Subsetting $font into $out_dir..."

    # Extract all unicode codepoints from the font
    local codepoints_file="$BUILD/$style/$out_name/codepoints.txt"
    uv run python -c "
from fontTools.ttLib import TTFont
font = TTFont('$font')
cmap = font.getBestCmap()
cps = sorted(cmap.keys())
for cp in cps:
    print(f'{cp:04X}')
" > "$codepoints_file"

    local total_cps
    total_cps=$(wc -l < "$codepoints_file" | tr -d ' ')
    log "  Total codepoints in font: $total_cps"

    # Split codepoints into chunks and subset
    local chunk_idx=0
    local chunk_cps=()
    local chunk_ranges_file="$BUILD/$style/$out_name/chunk_ranges.csv"
    > "$chunk_ranges_file"  # truncate

    while IFS= read -r cp; do
        chunk_cps+=("$cp")

        if [ "${#chunk_cps[@]}" -ge "$CHUNK_SIZE" ]; then
            _do_subset "$font" "$out_dir" "$chunk_idx" "${chunk_cps[*]}" "$chunk_ranges_file"
            chunk_idx=$((chunk_idx + 1))
            chunk_cps=()
        fi
    done < "$codepoints_file"

    # Remaining
    if [ "${#chunk_cps[@]}" -gt 0 ]; then
        _do_subset "$font" "$out_dir" "$chunk_idx" "${chunk_cps[*]}" "$chunk_ranges_file"
    fi

    log "  Created $((chunk_idx + 1)) chunks in $out_dir"
}

_do_subset() {
    local font=$1
    local out_dir=$2
    local idx=$3
    local cps_str=$4
    local ranges_file=$5

    local chunk_name
    chunk_name=$(printf "chunk-%03d" "$idx")
    local subset_woff2="$out_dir/${chunk_name}.woff2"

    # Build unicodes arg for pyftsubset
    local unicodes=""
    for cp in $cps_str; do
        if [ -n "$unicodes" ]; then
            unicodes="${unicodes},U+${cp}"
        else
            unicodes="U+${cp}"
        fi
    done

    uv run pyftsubset "$font" \
        --unicodes="$unicodes" \
        --output-file="$subset_woff2" \
        --flavor=woff2 \
        --layout-features='*' \
        --desubroutinize \
        2>/dev/null || {
            warn "  Subset failed for chunk $idx"
            return
        }

    # Record unicode range for CSS generation
    echo "${chunk_name}.woff2,${unicodes}" >> "$ranges_file"
}

# ─── Step 4: Generate CSS ────────────────────────────────────────────────────

generate_css() {
    log "Generating CSS..."
    uv run python generate_css.py
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
    ensure_deps

    # Step 1: Prepare SVGs
    prepare

    # Step 2: Compile fonts
    log ""
    log "=== Compiling Color fonts ==="
    compile_font color glyf_colr_1 FluentEmojiColor-COLRv1
    compile_font color untouchedsvg FluentEmojiColor-SVG

    log ""
    log "=== Compiling Flat fonts ==="
    compile_font flat glyf_colr_1 FluentEmojiFlat-COLRv1
    compile_font flat untouchedsvg FluentEmojiFlat-SVG

    # Step 3: Subset and compress
    log ""
    log "=== Subsetting and compressing ==="
    subset_and_compress color FluentEmojiColor-COLRv1 colrv1
    subset_and_compress color FluentEmojiColor-SVG otsvg
    subset_and_compress flat FluentEmojiFlat-COLRv1 colrv1
    subset_and_compress flat FluentEmojiFlat-SVG otsvg

    # Step 4: Generate CSS
    log ""
    generate_css

    log ""
    log "Done! Output in $DIST/"
    log ""
    du -sh "$DIST"/* 2>/dev/null || true
}

main "$@"
