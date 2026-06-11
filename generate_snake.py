"""Generate an animated snake SVG following GitHub contribution cells."""

import json
import sys
import math
import os
from datetime import datetime, timezone

CELL_SIZE = 12
CELL_GAP = 3
GRID_LEFT = 20
GRID_TOP = 20
USERNAME = "PerryWhitePeak"

LIGHT_COLORS = {0: "#ebedf0", 1: "#9be9a8", 2: "#40c463", 3: "#30a14e", 4: "#216e39"}
DARK_COLORS = {0: "#161b22", 1: "#0e4429", 2: "#006d32", 3: "#26a641", 4: "#39d353"}


def count_to_level(count: int) -> int:
    if count == 0: return 0
    if count <= 3: return 1
    if count <= 6: return 2
    if count <= 10: return 3
    return 4


def build_snake_path(grid: list[list[int]]) -> str:
    ncols = len(grid[0])
    coords = [(col, row) for col in range(ncols) for row in range(len(grid)) if grid[row][col] > 0]
    if not coords:
        return ""
    step_x = CELL_SIZE + CELL_GAP
    step_y = CELL_SIZE + CELL_GAP
    radius = CELL_SIZE / 2
    parts = []
    for i, (cx, cy) in enumerate(coords):
        x = GRID_LEFT + cx * step_x + radius
        y = GRID_TOP + cy * step_y + radius
        parts.append(f"M {x:.1f} {y:.1f}" if i == 0 else f"L {x:.1f} {y:.1f}")
    return " ".join(parts)


def make_dots(grid: list[list[int]], dark: bool) -> str:
    colors = DARK_COLORS if dark else LIGHT_COLORS
    ncols, nrows = len(grid[0]), len(grid)
    s = CELL_SIZE + CELL_GAP
    r = CELL_SIZE / 2
    parts = []
    for row in range(nrows):
        for col in range(ncols):
            level = count_to_level(grid[row][col])
            x = GRID_LEFT + col * s + r
            y = GRID_TOP + row * s + r
            parts.append(f'<rect x="{x - r:.1f}" y="{y - r:.1f}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="{colors[level]}"/>')
    return "\n    ".join(parts)


def make_svg(path_str: str, grid: list[list[int]], dark: bool) -> str:
    ncols, nrows = len(grid[0]), len(grid)
    s = CELL_SIZE + CELL_GAP
    total_w = GRID_LEFT + ncols * s + 20
    total_h = GRID_TOP + nrows * s + 50
    bg = "#0d1117" if dark else "#ffffff"
    fg = "#c9d1d9" if dark else "#24292f"
    snake_color = "#3B82F6"
    head_color = "#60a5fa"

    # Path length for animation
    parts = path_str.split()
    nums = [float(p) for p in parts if p not in ("M", "L")]
    path_len = 0.0
    for i in range(2, len(nums) - 1, 2):
        path_len += math.sqrt((nums[i] - nums[i-2])**2 + (nums[i+1] - nums[i-1])**2)
    if path_len < 1:
        path_len = 1.0

    dots = make_dots(grid, dark)
    head_r = 3.5

    css = f'''
  @keyframes snakeDash {{
    0% {{ stroke-dashoffset: {path_len:.0f}; }}
    100% {{ stroke-dashoffset: 0; }}
  }}
  @keyframes headPulse {{
    0%,100% {{ opacity:1; }}
    50% {{ opacity:0.4; }}
  }}
  .snake-path {{ stroke-dasharray: {path_len:.0f}; animation: snakeDash 4s ease-in-out infinite; }}
  .snake-head {{ animation: headPulse 1.5s ease-in-out infinite; }}
'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" fill="none">
<style>{css}</style>
<rect width="100%" height="100%" fill="{bg}" rx="4"/>
<g id="dots">{dots}</g>
<path d="{path_str}" stroke="{snake_color}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" class="snake-path" fill="none"/>
<circle r="{head_r}" fill="{head_color}" class="snake-head">
  <animateMotion dur="4s" repeatCount="indefinite" rotate="auto"><mpath href="#mp"/></animateMotion>
</circle>
<path id="mp" d="{path_str}" fill="none" stroke="none"/>
<text x="{total_w/2:.0f}" y="{total_h-10:.0f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="{fg}">@{USERNAME} · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</text>
</svg>'''


def main():
    data = json.load(sys.stdin)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = []
    for week in weeks:
        for row_idx, day in enumerate(week["contributionDays"]):
            if len(grid) <= row_idx:
                grid.append([])
            grid[row_idx].append(day["contributionCount"])
    # Pad shorter rows (partial weeks) to match max length
    max_len = max(len(row) for row in grid)
    for row in grid:
        while len(row) < max_len:
            row.append(0)

    path = build_snake_path(grid)
    if not path:
        print("No contributions found", file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out_dir, exist_ok=True)

    for dark, suffix in [(False, ""), (True, "-dark")]:
        svg = make_svg(path, grid, dark)
        fname = os.path.join(out_dir, f"github-contribution-grid-snake{suffix}.svg")
        with open(fname, "w") as f:
            f.write(svg)

    print(f"Generated SVGs in {out_dir}")


if __name__ == "__main__":
    main()
