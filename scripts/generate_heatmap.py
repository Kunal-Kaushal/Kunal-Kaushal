#!/usr/bin/env python3
"""
Generate a custom animated contribution heatmap SVG.

Fetches 365-day contribution data from GitHub's GraphQL API and renders
a bespoke animated SVG heatmap with a teal/cyan color scheme and a
staggered cell fade-in wave animation.

Environment variables:
    GITHUB_TOKEN    — GitHub PAT or Actions token (required for real data)
    GITHUB_USERNAME — GitHub username to query (default: Kunal-Kaushal)

Output: assets/contribution_heatmap.svg
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# Custom color scale: teal/mint gradient (5 levels)
COLOR_LEVELS = [
    "#161b22",   # Level 0: no contributions
    "#003d33",   # Level 1: low (1–3)
    "#00695f",   # Level 2: medium-low (4–7)
    "#00a88a",   # Level 3: medium-high (8–12)
    "#00ffaa",   # Level 4: high (13+)
]

# Thresholds for mapping count → color level
THRESHOLDS = [0, 1, 4, 8, 13]

# SVG layout
CELL_SIZE = 11       # Cell width/height in pixels
CELL_GAP = 3         # Gap between cells
CELL_RADIUS = 2      # Border radius on cells
PADDING_X = 28       # Horizontal padding
PADDING_Y = 20       # Vertical padding
DAY_LABEL_W = 36     # Width reserved for day-of-week labels
MONTH_LABEL_H = 18   # Height reserved for month labels
TITLE_H = 36         # Height for title area

# Colors
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TEXT_COLOR = "#8b949e"
TITLE_COLOR = "#c9d1d9"

# Day labels (GitHub convention: 0=Sun, 1=Mon, ..., 6=Sat)
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


# ─────────────────────────────────────────────────────────────────────
# GitHub API
# ─────────────────────────────────────────────────────────────────────

CONTRIBUTION_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(username: str, token: str) -> dict:
    """
    Fetch contribution calendar data from GitHub's GraphQL API.

    Args:
        username: GitHub login username.
        token: GitHub bearer token (PAT or GITHUB_TOKEN).

    Returns:
        The contributionCalendar object with totalContributions and weeks.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": CONTRIBUTION_QUERY, "variables": {"username": username}},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    if "errors" in data:
        error_msgs = "; ".join(e.get("message", "?") for e in data["errors"])
        raise ValueError(f"GraphQL errors: {error_msgs}")

    calendar = (
        data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    )
    return calendar


def generate_sample_data() -> dict:
    """
    Generate realistic sample contribution data for local testing.

    Produces a full 53-week calendar with weighted random contribution counts
    that mimic real developer activity patterns (lower on weekends, higher on
    weekdays, occasional burst days).
    """
    import random

    random.seed(42)  # Deterministic for consistent previews

    today = datetime.now(timezone.utc).date()

    # Align to the most recent Sunday
    days_since_sunday = today.isoweekday() % 7  # Sun=0, Mon=1, ..., Sat=6
    last_sunday = today - timedelta(days=days_since_sunday)
    start_sunday = last_sunday - timedelta(weeks=52)

    weeks = []
    current_sunday = start_sunday

    while current_sunday <= last_sunday:
        week_days = []
        for d in range(7):
            day = current_sunday + timedelta(days=d)
            if day > today:
                break

            github_weekday = d  # 0=Sun since we iterate from Sunday

            # Realistic activity: less on weekends, bursts on weekdays
            is_weekend = github_weekday in (0, 6)
            if is_weekend:
                count = random.choices(
                    [0, 1, 2, 3],
                    weights=[0.45, 0.30, 0.15, 0.10],
                )[0]
            else:
                count = random.choices(
                    [0, 1, 2, 3, 5, 7, 10, 14, 18],
                    weights=[0.10, 0.12, 0.18, 0.18, 0.15, 0.12, 0.08, 0.05, 0.02],
                )[0]

            week_days.append({
                "contributionCount": count,
                "date": day.isoformat(),
                "weekday": github_weekday,
            })

        if week_days:
            weeks.append({"contributionDays": week_days})
        current_sunday += timedelta(days=7)

    total = sum(
        d["contributionCount"] for w in weeks for d in w["contributionDays"]
    )

    return {"totalContributions": total, "weeks": weeks}


# ─────────────────────────────────────────────────────────────────────
# SVG Generation
# ─────────────────────────────────────────────────────────────────────


def get_color(count: int) -> str:
    """Map a contribution count to its color level."""
    if count >= THRESHOLDS[4]:
        return COLOR_LEVELS[4]
    elif count >= THRESHOLDS[3]:
        return COLOR_LEVELS[3]
    elif count >= THRESHOLDS[2]:
        return COLOR_LEVELS[2]
    elif count >= THRESHOLDS[1]:
        return COLOR_LEVELS[1]
    else:
        return COLOR_LEVELS[0]


def generate_heatmap_svg(calendar_data: dict, output_path: str) -> None:
    """
    Generate the animated heatmap SVG from contribution calendar data.

    Features:
        - Custom teal/cyan 5-level color scale
        - Staggered fade-in wave animation (left → right)
        - Month labels along the top, day labels on the left
        - Hover tooltips showing date and count
        - Legend with color levels
    """
    weeks = calendar_data["weeks"]
    total = calendar_data["totalContributions"]
    num_weeks = len(weeks)

    # ── Dimensions ────────────────────────────────────────────────
    cell_step = CELL_SIZE + CELL_GAP
    grid_w = num_weeks * cell_step - CELL_GAP
    grid_h = 7 * cell_step - CELL_GAP

    content_w = DAY_LABEL_W + grid_w
    content_h = MONTH_LABEL_H + grid_h

    svg_w = content_w + PADDING_X * 2
    svg_h = TITLE_H + content_h + PADDING_Y * 2 + 44  # +44 for legend area

    grid_x0 = PADDING_X + DAY_LABEL_W
    grid_y0 = TITLE_H + PADDING_Y + MONTH_LABEL_H
    legend_y = TITLE_H + PADDING_Y + content_h + 24

    # ── Build SVG ─────────────────────────────────────────────────
    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">'
    )

    # Styles
    svg.append("""  <defs>
    <style>
      @keyframes cell {
        0%   { opacity: 0; transform: translateY(-6px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      .cell {
        opacity: 0;
        animation: cell 0.42s cubic-bezier(.2,.8,.2,1) both;
      }
      .cell:hover {
        stroke: #c9d1d9;
        stroke-width: 1.5;
      }
      .label {
        font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
        font-size: 11px;
        fill: #8b949e;
      }
      .title {
        font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
        font-size: 14px;
        font-weight: 600;
        fill: #c9d1d9;
      }
      .legend-text {
        font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
        font-size: 10px;
        fill: #8b949e;
      }
    </style>
  </defs>""")

    # Background
    svg.append(
        f'  <rect width="{svg_w:.0f}" height="{svg_h:.0f}" rx="12" ry="12" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
    )

    # Title
    svg.append(
        f'  <text class="title" x="{PADDING_X}" y="{TITLE_H - 8}">'
        f'{total:,} contributions in the last year</text>'
    )

    # Day-of-week labels (Mon, Wed, Fri)
    for day_idx, label in DAY_LABELS.items():
        y = grid_y0 + day_idx * cell_step + CELL_SIZE - 2
        svg.append(
            f'  <text class="label" x="{PADDING_X}" y="{y:.0f}">{label}</text>'
        )

    # ── Grid cells + month labels ─────────────────────────────────
    prev_month = -1

    for week_idx, week in enumerate(weeks):
        col_x = grid_x0 + week_idx * cell_step

        for day in week["contributionDays"]:
            day_idx = day["weekday"]
            count = day["contributionCount"]
            date_str = day["date"]
            color = get_color(count)

            cell_y = grid_y0 + day_idx * cell_step

            # Staggered wave delay: left → right, top → bottom
            delay = week_idx * 0.02 + day_idx * 0.005

            # Month label at first visible day of each new month
            month_num = int(date_str.split("-")[1])
            if month_num != prev_month and day_idx <= 2:
                prev_month = month_num
                month_name = MONTH_NAMES[month_num - 1]
                svg.append(
                    f'  <text class="label" x="{col_x:.0f}" '
                    f'y="{grid_y0 - 6:.0f}">{month_name}</text>'
                )

            # Contribution cell
            plural = "" if count == 1 else "s"
            tooltip = f"{date_str}: {count} contribution{plural}"
            svg.append(
                f'  <rect class="cell" x="{col_x:.0f}" y="{cell_y:.0f}" '
                f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" '
                f'fill="{color}" '
                f'style="animation-delay: {delay:.2f}s">'
                f'<title>{tooltip}</title>'
                f'</rect>'
            )

    # ── Legend ─────────────────────────────────────────────────────
    legend_right_edge = svg_w - PADDING_X
    num_swatches = len(COLOR_LEVELS)
    swatch_area_w = num_swatches * cell_step - CELL_GAP
    more_text_w = 30
    less_text_w = 30
    total_legend_w = less_text_w + swatch_area_w + more_text_w + 8
    legend_x0 = legend_right_edge - total_legend_w

    svg.append(
        f'  <text class="legend-text" x="{legend_x0:.0f}" '
        f'y="{legend_y + CELL_SIZE - 2:.0f}">Less</text>'
    )

    for i, color in enumerate(COLOR_LEVELS):
        sx = legend_x0 + less_text_w + 4 + i * cell_step
        svg.append(
            f'  <rect x="{sx:.0f}" y="{legend_y:.0f}" '
            f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" fill="{color}"/>'
        )

    more_x = legend_x0 + less_text_w + 4 + num_swatches * cell_step + 4
    svg.append(
        f'  <text class="legend-text" x="{more_x:.0f}" '
        f'y="{legend_y + CELL_SIZE - 2:.0f}">More</text>'
    )

    svg.append("</svg>")

    # ── Write output ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    print(
        f"✓ Heatmap generated: {output_path} "
        f"({total:,} contributions, {num_weeks} weeks)"
    )


def main():
    repo_root = Path(__file__).resolve().parent.parent
    output = repo_root / "assets" / "contribution_heatmap.svg"

    username = os.environ.get("GITHUB_USERNAME", "Kunal-Kaushal")
    token = os.environ.get("GITHUB_TOKEN", "")

    if token:
        print(f"Fetching contribution data for @{username}...")
        try:
            calendar_data = fetch_contributions(username, token)
        except Exception as e:
            print(f"ERROR fetching contributions: {e}")
            print("Falling back to sample data.")
            calendar_data = generate_sample_data()
    else:
        print(
            "⚠  No GITHUB_TOKEN set. Generating sample data for local preview.\n"
            "   Set GITHUB_TOKEN to fetch real contribution data."
        )
        calendar_data = generate_sample_data()

    generate_heatmap_svg(calendar_data, str(output))


if __name__ == "__main__":
    main()
