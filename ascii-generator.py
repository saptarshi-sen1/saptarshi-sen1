#!/usr/bin/env python3
"""
ascii-generator.py
-------------------
Converts a front-facing portrait into terminal-style ASCII art and emits
two ready-to-embed SVG assets (light mode + dark mode) sized for a GitHub
README, plus a plain .txt copy for quick inspection.

Usage
-----
    pip install pillow
    python ascii-generator.py --input portrait.jpg

Optional flags
---------------
    --width        Output width in characters        (default: 85)
    --out-dir      Where to write generated assets    (default: assets/)
    --invert       Invert the brightness ramp (use for light-background photos)
    --font-size    Font size (px) used inside the generated SVG (default: 6.4)

Regenerating after you replace the photo
-----------------------------------------
1. Drop the new portrait in the repo root (or anywhere) as e.g. portrait.jpg.
2. Run:  python ascii-generator.py --input portrait.jpg
3. This overwrites:
       assets/avatar-placeholder-dark.svg
       assets/avatar-placeholder-light.svg
       assets/avatar-placeholder.txt
4. Commit the regenerated files. README.md already points at the SVG paths,
   so no other edits are needed.
"""

import argparse
import html
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("This script needs Pillow. Install it with: pip install pillow")
    sys.exit(1)

# Darkest -> lightest. Tuned for a terminal look rather than photographic
# accuracy: fewer, chunkier ramp steps read better at README scale.
RAMP = " .,:;+*#%@$&X█"


def image_to_ascii(path: str, out_width: int, invert: bool) -> list[str]:
    img = Image.open(path).convert("L")

    # Characters are taller than they are wide, so compress vertically
    # to keep the final art from looking stretched.
    aspect_correction = 0.55
    w, h = img.size
    out_height = max(1, int((h / w) * out_width * aspect_correction))
    img = img.resize((out_width, out_height))

    pixels = list(img.getdata())
    ramp = RAMP[::-1] if invert else RAMP
    scale = (len(ramp) - 1) / 255

    lines = []
    for row in range(out_height):
        line = "".join(
            ramp[int(pixels[row * out_width + col] * scale)]
            for col in range(out_width)
        )
        lines.append(line.rstrip())
    return lines


def build_svg(lines: list[str], theme: str, font_size: float) -> str:
    line_height = font_size * 1.19
    char_w = font_size * 0.60
    max_len = max((len(l) for l in lines), default=1)

    pad_x, pad_top, pad_bottom = 30, 60, 26
    width = int(max_len * char_w + pad_x * 2)
    height = int(len(lines) * line_height + pad_top + pad_bottom)

    if theme == "dark":
        bg, panel, border, titlebar = "#0A0E14", "#0F141C", "#1E2733", "#131A24"
        glyph, path_c = "#56D8C9", "#6B7685"
        dot_r, dot_y, dot_g = "#E5645B", "#E3A857", "#6FBF8B"
    else:
        bg, panel, border, titlebar = "#FAFBFC", "#FFFFFF", "#D7DCE1", "#F1F3F5"
        glyph, path_c = "#0E7C74", "#57606A"
        dot_r, dot_y, dot_g = "#E5645B", "#D9A441", "#4C9A6A"

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="ASCII portrait, {theme} mode">',
        "<style>",
        f".bg{{fill:{bg};}} .panel{{fill:{panel};stroke:{border};stroke-width:1;}} "
        f".titlebar{{fill:{titlebar};}}",
        f".path{{fill:{path_c};font-family:'JetBrains Mono','Fira Code',monospace;font-size:12px;}}",
        f".art{{fill:{glyph};font-family:'JetBrains Mono','Fira Code',monospace;"
        f"font-size:{font_size}px;}}",
        "</style>",
        f'<rect class="bg" width="{width}" height="{height}" rx="10"/>',
        f'<rect class="panel" x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10"/>',
        f'<path class="titlebar" d="M10 0 H{width-10} A10 10 0 0 1 {width} 10 '
        f'V38 H0 V10 A10 10 0 0 1 10 0 Z"/>',
        f'<circle cx="26" cy="19" r="6" fill="{dot_r}"/>',
        f'<circle cx="46" cy="19" r="6" fill="{dot_y}"/>',
        f'<circle cx="66" cy="19" r="6" fill="{dot_g}"/>',
        f'<text class="path" x="{width/2}" y="24" text-anchor="middle">'
        f"avatar.ascii &#8212; render preview</text>",
    ]

    y0 = pad_top
    for i, line in enumerate(lines):
        esc = html.escape(line).replace(" ", "&#160;")
        y = y0 + i * line_height
        parts.append(f'<text class="art" x="{pad_x}" y="{y:.1f}" xml:space="preserve">{esc}</text>')

    parts.append(
        f'<text class="path" x="{pad_x}" y="{height-10}">'
        f"$ python ascii-generator.py --input portrait.jpg --mode {theme}</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Convert a portrait into terminal ASCII art SVGs.")
    ap.add_argument("--input", required=True, help="Path to the source portrait image.")
    ap.add_argument("--width", type=int, default=85, help="Output width in characters.")
    ap.add_argument("--out-dir", default="assets", help="Directory to write generated assets.")
    ap.add_argument("--invert", action="store_true", help="Invert the brightness ramp.")
    ap.add_argument("--font-size", type=float, default=6.4, help="SVG glyph font size in px.")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    lines = image_to_ascii(args.input, args.width, args.invert)

    txt_path = os.path.join(args.out_dir, "avatar-placeholder.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    for theme in ("dark", "light"):
        svg = build_svg(lines, theme, args.font_size)
        svg_path = os.path.join(args.out_dir, f"avatar-placeholder-{theme}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {svg_path}")

    print(f"wrote {txt_path}")
    print("Done. Commit the files in", args.out_dir)


if __name__ == "__main__":
    main()
