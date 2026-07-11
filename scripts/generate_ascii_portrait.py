#!/usr/bin/env python3
"""
Generate an ASCII art SVG portrait from a headshot image.

Uses Pillow to convert a photo into ASCII art, then renders it as a
terminal-styled SVG with a SMIL-based line-by-line wipe animation
(a cursor sweeps each line left-to-right, revealing the text).

This uses SMIL <animate> elements instead of CSS @keyframes because
GitHub's SVG sanitizer strips CSS transforms but preserves SMIL.

Usage:
    python generate_ascii_portrait.py [width]

Requires:
    - Pillow (pip install Pillow)
    - A headshot image at assets/headshot.{jpg,jpeg,png,webp}
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

# ASCII character density ramp — lightest (space) to darkest (@)
ASCII_RAMP = " .,:;i1tfLCG08@#"
ASCII_RAMP_LEN = len(ASCII_RAMP)

DEFAULT_WIDTH = 80
CHAR_ASPECT_RATIO = 0.55  # compensate for tall monospace chars

# SVG rendering
FONT_SIZE = 12.9
CHAR_W = 8.0        # monospace char width at ~13px
LINE_H = 15         # line height
TITLE_BAR_H = 30    # terminal title bar
PAD_X = 20          # horizontal content padding
PAD_Y = 7           # vertical content padding (above first line)

# Animation timing
LINE_DUR = 0.11     # seconds to wipe each line
CURSOR_W = 8        # cursor block width
CURSOR_H = 13       # cursor block height


def load_and_process_image(image_path: str, width: int) -> list[str]:
    """Load an image and convert it to ASCII art lines."""
    img = Image.open(image_path)
    aspect = img.height / img.width
    height = int(width * aspect * CHAR_ASPECT_RATIO)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # If image has an alpha channel, use it to mask the background
    has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
    if has_alpha:
        img = img.convert("RGBA")
        pixels = list(img.getdata())
    else:
        img = img.convert("L")
        pixels = list(img.getdata())

    lines = []
    for row in range(height):
        chars = []
        for col in range(width):
            pixel = pixels[row * width + col]
            
            # Check transparency first
            if has_alpha:
                alpha = pixel[3]
                if alpha < 128:  # Transparent enough to be background
                    chars.append(" ")
                    continue
                # Calculate brightness from RGB
                r, g, b = pixel[:3]
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
            else:
                brightness = pixel
                
            idx = int((255 - brightness) / 256 * ASCII_RAMP_LEN)
            idx = min(idx, ASCII_RAMP_LEN - 1)
            chars.append(ASCII_RAMP[idx])
        lines.append("".join(chars))
    return lines


def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_svg(ascii_lines: list[str], output_path: str) -> None:
    """
    Render ASCII art as an animated terminal-style SVG.

    Animation technique (from reference repo):
    - Each line is wrapped in a <clipPath> whose inner rect animates
      from width=0 to width=full, creating a left-to-right wipe.
    - A cursor <rect> sweeps across each line in sync.
    - Uses SMIL <animate> for GitHub compatibility.
    """
    cols = max(len(line) for line in ascii_lines)
    rows = len(ascii_lines)

    text_w = cols * CHAR_W
    svg_w = text_w + PAD_X * 2
    svg_h = TITLE_BAR_H + PAD_Y + (rows + 2) * LINE_H + PAD_Y

    svg = []

    # ── Header ────────────────────────────────────────────────────
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )

    # ── Background ────────────────────────────────────────────────
    svg.append("  <defs>")
    svg.append('    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">')
    svg.append('      <stop offset="0" stop-color="#111722"/>')
    svg.append('      <stop offset="1" stop-color="#0d1117"/>')
    svg.append("    </linearGradient>")
    svg.append("  </defs>")
    svg.append(
        f'  <rect width="{svg_w:.0f}" height="{svg_h:.0f}" rx="12" fill="url(#bg)"/>'
    )
    svg.append(
        f'  <rect x="0.5" y="0.5" width="{svg_w - 1:.0f}" height="{svg_h - 1:.0f}" '
        f'rx="12" fill="none" stroke="#30363d" stroke-width="1"/>'
    )

    # ── Title bar ─────────────────────────────────────────────────
    svg.append(
        f'  <line x1="0" y1="{TITLE_BAR_H}" x2="{svg_w:.0f}" '
        f'y2="{TITLE_BAR_H}" stroke="#30363d"/>'
    )
    dot_cy = TITLE_BAR_H / 2
    svg.append(f'  <circle cx="20" cy="{dot_cy}" r="5" fill="#ff5f56"/>')
    svg.append(f'  <circle cx="36" cy="{dot_cy}" r="5" fill="#ffbd2e"/>')
    svg.append(f'  <circle cx="52" cy="{dot_cy}" r="5" fill="#27c93f"/>')
    svg.append(
        f'  <text x="{svg_w / 2:.0f}" y="{dot_cy + 4:.0f}" fill="#7d8590" '
        f'font-size="12" text-anchor="middle">kunal@github: ~$ ./portrait.sh</text>'
    )

    # ── Animated ASCII lines ──────────────────────────────────────
    for i, line in enumerate(ascii_lines):
        line_y = TITLE_BAR_H + PAD_Y + i * LINE_H
        text_y = line_y + LINE_H - 3.9  # baseline offset
        begin = f"{i * LINE_DUR:.3f}s"
        end = f"{(i + 1) * LINE_DUR:.3f}s"

        escaped = escape_xml(line)

        # ClipPath: rect that wipes from width=0 → text_w
        svg.append(f'  <clipPath id="r{i}">')
        svg.append(
            f'    <rect x="{PAD_X}" y="{line_y}" height="{LINE_H}" width="0">'
        )
        svg.append(
            f'      <animate attributeName="width" from="0" to="{text_w:.0f}" '
            f'begin="{begin}" dur="{LINE_DUR}s" fill="freeze"/>'
        )
        svg.append("    </rect>")
        svg.append("  </clipPath>")

        # Text element clipped by the wipe
        svg.append(f'  <g clip-path="url(#r{i})">')
        svg.append(
            f'    <text xml:space="preserve" x="{PAD_X}" y="{text_y:.1f}" '
            f'fill="#c9d1d9" font-size="{FONT_SIZE}" '
            f'textLength="{text_w:.0f}" lengthAdjust="spacing">{escaped}</text>'
        )
        svg.append("  </g>")

        # Cursor block that sweeps across the line
        svg.append(
            f'  <rect y="{line_y + 1:.0f}" width="{CURSOR_W}" '
            f'height="{CURSOR_H}" fill="#c9d1d9" opacity="0">'
        )
        svg.append(
            f'    <animate attributeName="x" from="{PAD_X}" '
            f'to="{PAD_X + text_w:.0f}" begin="{begin}" '
            f'dur="{LINE_DUR}s" fill="freeze"/>'
        )
        svg.append(f'    <set attributeName="opacity" to="0.85" begin="{begin}"/>')
        svg.append(f'    <set attributeName="opacity" to="0" begin="{end}"/>')
        svg.append("  </rect>")

    # ── Bottom Prompt ──────────────────────────────────────────────
    bottom_y = TITLE_BAR_H + PAD_Y + (rows + 1) * LINE_H
    prompt_delay = rows * LINE_DUR + 0.3
    
    svg.append(f'  <g opacity="0">')
    svg.append(
        f'    <animate attributeName="opacity" from="0" to="1" '
        f'begin="{prompt_delay:.1f}s" dur="0.4s" fill="freeze"/>'
    )
    svg.append(
        f'    <text x="{PAD_X}" y="{bottom_y:.0f}" '
        f'font-family="\'Courier New\', monospace" font-size="{FONT_SIZE}">'
        f'<tspan fill="#7d8590">kunal@github:~$ </tspan>'
        f'<tspan fill="#c9d1d9">whoami </tspan>'
        f'<tspan fill="#58a6ff" font-weight="bold">Kunal Kaushal</tspan>'
        f'</text>'
    )
    svg.append(f'  </g>')

    svg.append("</svg>")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    print(f"✓ ASCII portrait generated: {output_path} ({cols}×{rows} chars)")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    assets_dir = repo_root / "assets"

    headshot = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = assets_dir / f"headshot.{ext}"
        if candidate.exists():
            headshot = candidate
            break

    if not headshot:
        print("ERROR: No headshot found in assets/ directory.")
        print("  Place your photo as: assets/headshot.jpg (or .jpeg, .png, .webp)")
        sys.exit(1)

    width = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WIDTH
    output = assets_dir / "ascii_portrait.svg"

    print(f"Processing {headshot.name} at {width} columns...")
    ascii_lines = load_and_process_image(str(headshot), width)
    generate_svg(ascii_lines, str(output))


if __name__ == "__main__":
    main()
