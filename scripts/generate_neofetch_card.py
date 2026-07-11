#!/usr/bin/env python3
"""
Generate a neofetch-styled SVG info card.

Creates a terminal-window SVG mimicking the classic Linux `neofetch` output,
with an ASCII art logo on the left and system/stack info on the right.
Includes ANSI-style color palette blocks at the bottom.

Output: assets/neofetch_card.svg
"""

import os
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

GITHUB_USERNAME = "kunal-kaushal"

# SVG layout
FONT_SIZE = 16
CHAR_W = 9.6       # Approx monospace char width at 16px
CHAR_H = 24        # Line height
TITLE_BAR_H = 40   # Terminal title bar
PADDING_X = 36      # Horizontal content padding
PADDING_Y = 28      # Vertical content padding
LOGO_INFO_GAP = 30  # Pixel gap between logo and info columns

# Terminal colors
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TITLE_BAR_COLOR = "#161b22"
TITLE_TEXT_COLOR = "#7a7a7a"
HEADER_COLOR = "#58a6ff"
SEPARATOR_COLOR = "#484f58"
VALUE_COLOR = "#c9d1d9"

# Per-label accent colors (curated palette)
LABEL_COLORS = {
    "Role": "#58a6ff",
    "Focus": "#56d364",
    "Languages": "#f0883e",
    "Frameworks": "#a371f7",
    "Backend": "#f778ba",
    "Database": "#79c0ff",
    "Cloud": "#d29922",
    "Education": "#8b949e",
    "Status": "#ff7b72",
}

# ANSI terminal color palette (normal + bright)
ANSI_NORMAL = [
    "#2e3440", "#bf616a", "#a3be8c", "#ebcb8b",
    "#81a1c1", "#b48ead", "#88c0d0", "#e5e9f0",
]
ANSI_BRIGHT = [
    "#4c566a", "#d08770", "#8fbcbb", "#d8dee9",
    "#5e81ac", "#b48ead", "#8fbcbb", "#eceff4",
]

LOGO_LINES = []

# ── Info fields ───────────────────────────────────────────────────
# Format: (label, value)
INFO_LINES = [
    ("", f"{GITHUB_USERNAME}@genai-workstation"),
    ("", "─" * 40),
    ("Role", "AI Intern @ Droisys"),
    ("Focus", "GenAI · RAG · Agentic Workflows"),
    ("Languages", "Python · C/C++"),
    ("Frameworks", "LangChain · Google ADK"),
    ("Backend", "FastAPI · Flask"),
    ("Database", "SQL · NoSQL · Firestore"),
    ("Cloud", "GCP (Cloud Run) · AWS"),
    ("Education", "B.Tech AI &amp; ML @ GL Bajaj"),
    ("Status", "Building production-grade AI systems"),
]

def generate_neofetch_svg(output_path: str) -> None:
    """Generate the neofetch-style terminal card SVG."""

    # ── Layout calculations ───────────────────────────────────────
    logo_max_chars = max([0] + [len(line) for line in LOGO_LINES])
    logo_w_px = logo_max_chars * CHAR_W

    max_info_chars = max(
        len(f"{lbl}: {val}") if lbl else len(val)
        for lbl, val in INFO_LINES
    )
    info_w_px = max_info_chars * CHAR_W

    info_x = PADDING_X + logo_w_px + (LOGO_INFO_GAP if logo_w_px > 0 else 0)

    num_lines = max(len(LOGO_LINES), len(INFO_LINES))
    content_h = (num_lines + 1) * CHAR_H + 8

    pad_x = PADDING_X
    content_y0 = TITLE_BAR_H + PADDING_Y
    
    info_x = pad_x + logo_w_px + (LOGO_INFO_GAP if logo_w_px > 0 else 0)
    svg_w = info_x + info_w_px + pad_x
    svg_h = TITLE_BAR_H + PADDING_Y * 2 + content_h

    # ── SVG assembly ──────────────────────────────────────────────
    parts = []

    # Root element
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">'
    )

    # Styles
    parts.append(f"""  <style>
    .mono {{
      font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code',
                   'SF Mono', 'Courier New', monospace;
      font-size: {FONT_SIZE}px;
    }}
    .title-text {{
      font-family: 'SF Mono', 'Courier New', monospace;
      font-size: 13px;
    }}
  </style>""")

    # ── Clip Paths for Animation ──────────────────────────────────
    parts.append("  <defs>")
    for i in range(num_lines):
        y_clip = content_y0 + i * CHAR_H
        delay = i * 0.15  # Stagger rows by 0.15s
        dur = 0.5         # 0.5s left-to-right wipe per row
        parts.append(
            f'    <clipPath id="wipe-row-{i}">'
            f'<rect x="0" y="{y_clip}" width="0" height="{CHAR_H + 4}">'
            f'<animate attributeName="width" from="0" to="{svg_w:.0f}" '
            f'begin="{delay:.2f}s" dur="{dur}s" fill="freeze" />'
            f'</rect></clipPath>'
        )
    parts.append("  </defs>")

    # ── Terminal chrome ───────────────────────────────────────────

    # Outer background (rounded rect)
    parts.append(
        f'  <rect width="{svg_w:.0f}" height="{svg_h:.0f}" rx="12" ry="12" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
    )

    # Title bar
    parts.append(
        f'  <rect width="{svg_w:.0f}" height="{TITLE_BAR_H}" '
        f'rx="12" ry="12" fill="{TITLE_BAR_COLOR}"/>'
    )
    # Square off the bottom of the title bar
    parts.append(
        f'  <rect y="{TITLE_BAR_H - 12}" width="{svg_w:.0f}" '
        f'height="12" fill="{TITLE_BAR_COLOR}"/>'
    )
    # Separator line
    parts.append(
        f'  <line x1="0" y1="{TITLE_BAR_H}" x2="{svg_w:.0f}" '
        f'y2="{TITLE_BAR_H}" stroke="{BORDER_COLOR}" stroke-width="0.5"/>'
    )

    # Traffic light dots
    dot_cy = TITLE_BAR_H // 2
    parts.append(f'  <circle cx="20" cy="{dot_cy}" r="6" fill="#ff5f57"/>')
    parts.append(f'  <circle cx="40" cy="{dot_cy}" r="6" fill="#febc2e"/>')
    parts.append(f'  <circle cx="60" cy="{dot_cy}" r="6" fill="#28c840"/>')

    # Title text
    parts.append(
        f'  <text class="title-text" x="{svg_w / 2:.0f}" y="{dot_cy + 4}" '
        f'text-anchor="middle" fill="{TITLE_TEXT_COLOR}">'
        f'{GITHUB_USERNAME} — neofetch</text>'
    )

    # ── Animated Content Rows ─────────────────────────────────────
    for i in range(num_lines):
        parts.append(f'  <g clip-path="url(#wipe-row-{i})">')
        
        # Left column (Logo)
        if i < len(LOGO_LINES) and LOGO_LINES[i]:
            y = content_y0 + (i + 1) * CHAR_H
            parts.append(
                f'    <text class="mono" x="{pad_x:.0f}" y="{y:.0f}" '
                f'fill="{HEADER_COLOR}" xml:space="preserve">{LOGO_LINES[i]}</text>'
            )

        # Right column (Info)
        if i < len(INFO_LINES):
            label, value = INFO_LINES[i]
            y = content_y0 + (i + 1) * CHAR_H
            
            if not label:
                # Header line or separator
                if i == 0:
                    parts.append(
                        f'    <text class="mono" x="{info_x:.0f}" y="{y:.0f}" '
                        f'fill="{HEADER_COLOR}" font-weight="bold" '
                        f'xml:space="preserve">{value}</text>'
                    )
                elif value:
                    parts.append(
                        f'    <text class="mono" x="{info_x:.0f}" y="{y:.0f}" '
                        f'fill="{SEPARATOR_COLOR}" xml:space="preserve">{value}</text>'
                    )
            else:
                # Key-value info line
                lbl_color = LABEL_COLORS.get(label, VALUE_COLOR)
                parts.append(
                    f'    <text class="mono" x="{info_x:.0f}" y="{y:.0f}">'
                    f'<tspan fill="{lbl_color}" font-weight="bold">{label}</tspan>'
                    f'<tspan fill="{VALUE_COLOR}">: {value}</tspan>'
                    f'</text>'
                )

        parts.append('  </g>')

    parts.append("</svg>")

    # ── Write output ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"✓ Neofetch card generated: {output_path}")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    output = repo_root / "assets" / "neofetch_card.svg"
    generate_neofetch_svg(str(output))


if __name__ == "__main__":
    main()
