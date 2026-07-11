#!/usr/bin/env python3
"""
Generate an AI system boot sequence SVG with CSS animations.

Creates a sleek, monochromatic terminal SVG that simulates a server boot log.
Each line fades in sequentially, and two key repository modules are rendered
as clickable links. A blinking cursor caps the sequence.

Output: assets/boot_sequence.svg
"""

import os
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

# SVG layout constants
FONT_SIZE = 13
CHAR_W = 7.8       # Approx monospace character width at 13px
CHAR_H = 20        # Line height
TITLE_BAR_H = 40   # Terminal title bar height
PADDING_X = 24     # Horizontal padding inside terminal
PADDING_Y = 20     # Vertical padding inside terminal

# Animation timing
LINE_DELAY = 0.3   # Seconds between each line reveal

# Terminal colors
BG_COLOR = "#0a0a0a"
TITLE_BAR_COLOR = "#1a1a1a"
BORDER_COLOR = "#2a2a2a"
TEXT_COLOR = "#b0b0b0"

# Status badge colors
STATUS_COLORS = {
    "SYSTEM": "#ffb700",
    "  OK  ": "#00ff41",
    " LOAD ": "#00bfff",
    "READY ": "#00ff41",
}

# Repository links
ARCHON_URL = "https://github.com/Kunal-Kaushal/Archon"
DEVPILOT_URL = "https://github.com/Kunal-Kaushal/DevPilot"


def get_boot_lines(timestamp: str) -> list[dict]:
    """
    Define the boot sequence content.

    Each entry is a dict with:
        prefix: Status badge text (fixed-width, 6 chars)
        text:   Log message
        link:   Optional URL (makes the line clickable)
    """
    return [
        {
            "prefix": "SYSTEM",
            "text": f"Initializing AI Backend v3.2.1 ...           [{timestamp}]",
        },
        {
            "prefix": "  OK  ",
            "text": "Python runtime loaded ................................ 3.11.9",
        },
        {
            "prefix": "  OK  ",
            "text": "LangChain orchestrator connected ..................... active",
        },
        {
            "prefix": "  OK  ",
            "text": "FAISS vector index mounted ........................... 1.2M vectors",
        },
        {
            "prefix": "  OK  ",
            "text": "FastAPI server binding ............................... 0.0.0.0:8000",
        },
        {
            "prefix": "  OK  ",
            "text": "PostgreSQL connection pool ........................... 25 connections",
        },
        {
            "prefix": "  OK  ",
            "text": "Docker container health check ........................ passing",
        },
        {
            "prefix": "  OK  ",
            "text": "GCP Vertex AI endpoint .............................. online",
        },
        {
            "prefix": " LOAD ",
            "text": "Module 1: Archon .................................... Hybrid search initialized",
            "link": ARCHON_URL,
        },
        {
            "prefix": " LOAD ",
            "text": "Module 2: DevPilot .................................. Agentic repo analysis online",
            "link": DEVPILOT_URL,
        },
        {
            "prefix": "READY ",
            "text": "All systems operational. Awaiting queries.",
        },
    ]


def generate_boot_svg(output_path: str) -> None:
    """Generate the boot sequence SVG with staggered SMIL animations."""

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    boot_lines = get_boot_lines(timestamp)

    # ── Calculate SVG dimensions ──────────────────────────────────
    max_chars = max(len(f"[{l['prefix']}] {l['text']}") for l in boot_lines)
    svg_w = max(max_chars * CHAR_W + PADDING_X * 2, 780)
    num_content_lines = len(boot_lines) + 1  # +1 for cursor line
    svg_h = TITLE_BAR_H + PADDING_Y * 2 + num_content_lines * CHAR_H + 8

    total_anim_duration = len(boot_lines) * LINE_DELAY

    # ── Build SVG ─────────────────────────────────────────────────
    svg = []

    # Header
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">'
    )

    # Embedded styles
    svg.append(f"""  <defs>
    <style>
      .boot-line {{
        font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code',
                     'SF Mono', 'Courier New', monospace;
        font-size: {FONT_SIZE}px;
      }}
      .title-text {{
        font-family: 'SF Mono', 'Courier New', monospace;
        font-size: 12px;
      }}
      a {{ text-decoration: none; }}
      a:hover .link-text {{ text-decoration: underline; }}
    </style>
  </defs>""")

    # ── Terminal chrome ───────────────────────────────────────────

    # Background
    svg.append(
        f'  <rect width="{svg_w:.0f}" height="{svg_h:.0f}" '
        f'rx="10" ry="10" fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
    )

    # Title bar (rounded top, square bottom via overlay)
    svg.append(
        f'  <rect width="{svg_w:.0f}" height="{TITLE_BAR_H}" '
        f'rx="10" ry="10" fill="{TITLE_BAR_COLOR}"/>'
    )
    svg.append(
        f'  <rect y="{TITLE_BAR_H - 10}" width="{svg_w:.0f}" '
        f'height="10" fill="{TITLE_BAR_COLOR}"/>'
    )
    svg.append(
        f'  <line x1="0" y1="{TITLE_BAR_H}" x2="{svg_w:.0f}" '
        f'y2="{TITLE_BAR_H}" stroke="{BORDER_COLOR}" stroke-width="0.5"/>'
    )

    # Traffic light dots
    dot_cy = TITLE_BAR_H // 2
    svg.append(f'  <circle cx="20" cy="{dot_cy}" r="6" fill="#ff5f57"/>')
    svg.append(f'  <circle cx="40" cy="{dot_cy}" r="6" fill="#febc2e"/>')
    svg.append(f'  <circle cx="60" cy="{dot_cy}" r="6" fill="#28c840"/>')

    # Title
    svg.append(
        f'  <text class="title-text" x="{svg_w / 2:.0f}" y="{dot_cy + 4}" '
        f'text-anchor="middle" fill="#555">ai-backend — system boot</text>'
    )

    # ── Boot log lines ────────────────────────────────────────────

    for i, line in enumerate(boot_lines):
        y = TITLE_BAR_H + PADDING_Y + (i + 1) * CHAR_H
        delay = i * LINE_DELAY
        prefix = line["prefix"]
        text = line["text"]
        prefix_color = STATUS_COLORS.get(prefix, "#888")

        # Build the styled text content
        text_content = (
            f'<tspan fill="{prefix_color}">[{prefix}]</tspan>'
            f'<tspan fill="#333"> </tspan>'
            f'<tspan class="link-text" fill="{TEXT_COLOR}">{text}</tspan>'
        )

        svg.append(f'  <g opacity="0">')
        svg.append(
            f'    <animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.1f}s" dur="0.4s" fill="freeze"/>'
        )
        svg.append(
            f'    <animateTransform attributeName="transform" type="translate" '
            f'from="0 8" to="0 0" begin="{delay:.1f}s" dur="0.4s" fill="freeze"/>'
        )

        if line.get("link"):
            svg.append(f'    <a href="{line["link"]}" target="_blank">')
            svg.append(
                f'      <text class="boot-line" x="{PADDING_X}" y="{y:.0f}" '
                f'xml:space="preserve">{text_content}</text>'
            )
            svg.append("    </a>")
        else:
            svg.append(
                f'    <text class="boot-line" x="{PADDING_X}" y="{y:.0f}" '
                f'xml:space="preserve">{text_content}</text>'
            )
        svg.append(f'  </g>')

    # ── Blinking cursor ───────────────────────────────────────────

    cursor_y = TITLE_BAR_H + PADDING_Y + (len(boot_lines) + 1) * CHAR_H
    cursor_delay = total_anim_duration + 0.6
    svg.append(f'  <g opacity="0">')
    svg.append(
        f'    <animate attributeName="opacity" from="0" to="1" '
        f'begin="{cursor_delay:.1f}s" dur="0.1s" fill="freeze"/>'
    )
    svg.append(
        f'    <text x="{PADDING_X}" y="{cursor_y:.0f}" '
        f'font-family="\'Courier New\', monospace" font-size="{FONT_SIZE}">'
        f'<tspan fill="#00ff41">$ </tspan>'
        f'<tspan fill="#00ff41">█'
        f'<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" '
        f'calcMode="discrete" begin="{cursor_delay:.1f}s" dur="1s" repeatCount="indefinite"/>'
        f'</tspan>'
        f'</text>'
    )
    svg.append(f'  </g>')

    svg.append("</svg>")

    # ── Write output ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    print(f"✓ Boot sequence SVG generated: {output_path}")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    output = repo_root / "assets" / "boot_sequence.svg"
    generate_boot_svg(str(output))


if __name__ == "__main__":
    main()
