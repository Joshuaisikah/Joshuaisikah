#!/usr/bin/env python3
"""
Growing snake SVG generator for GitHub profile README.
Fetches contribution data via GitHub GraphQL API and generates
an animated SVG where the snake grows longer as it eats contributions.
"""

import os
import sys
import requests

USERNAME    = os.environ.get('GITHUB_USERNAME', 'Joshuaisikah')
TOKEN       = os.environ.get('GITHUB_TOKEN', '')
OUTPUT_FILE = os.environ.get('OUTPUT_FILE', 'dist/snake-growing.svg')

# ── Grid ──────────────────────────────────────────────────────────────────────
CELL   = 12
GAP    = 3
STEP   = CELL + GAP
MX     = 16   # margin x
MY     = 20   # margin y

# ── Animation ─────────────────────────────────────────────────────────────────
SPD          = 0.07   # seconds per grid step
INIT_LEN     = 5      # starting snake length
GROWTH_SCALE = 0.6    # segments added per contribution point

# ── Cyberpunk palette ─────────────────────────────────────────────────────────
BG      = '#0D0D0D'
LEVELS  = ['#0D1A0D', '#0D3B0D', '#1A6B1A', '#00A550', '#00FF41']
HEAD    = '#FFE600'
BODY    = ['#00FF41', '#00D936', '#00B82C', '#009622', '#007518']
EATEN   = '#060D06'


# ── GitHub API ────────────────────────────────────────────────────────────────

def fetch_contributions():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays { contributionCount }
            }
          }
        }
      }
    }
    """
    r = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': {'login': USERNAME}},
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
        timeout=15,
    )
    if r.status_code != 200:
        print(f"API error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    data = r.json()
    if 'errors' in data:
        print(f"GraphQL error: {data['errors']}", file=sys.stderr)
        sys.exit(1)
    return data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']


# ── Grid / path ───────────────────────────────────────────────────────────────

def build_grid(weeks):
    grid = []
    for week in weeks:
        col = [d['contributionCount'] for d in week['contributionDays']]
        while len(col) < 7:
            col.append(0)
        grid.append(col)
    return grid


def build_path(grid):
    """Boustrophedon (serpentine) path through the contribution grid."""
    path = []
    for ci, col in enumerate(grid):
        rows = range(7) if ci % 2 == 0 else range(6, -1, -1)
        for row in rows:
            path.append((ci, row))
    return path


# ── Snake state ───────────────────────────────────────────────────────────────

def compute_states(grid, path):
    """Return list of snake body lists (head first) at every step."""
    states, snake, target = [], [], INIT_LEN
    for col, row in path:
        count = grid[col][row]
        snake = [(col, row)] + snake
        if count > 0:
            target += max(1, int(count * GROWTH_SCALE))
        while len(snake) > target:
            snake.pop()
        states.append(list(snake))
    return states


# ── SVG generation ────────────────────────────────────────────────────────────

def level_color(count):
    if count == 0: return LEVELS[0]
    if count <= 1: return LEVELS[1]
    if count <= 3: return LEVELS[2]
    if count <= 8: return LEVELS[3]
    return LEVELS[4]


def body_color(depth):
    return BODY[min(depth, len(BODY) - 1)]


def kt(t, total):
    """Normalised keyTime, clamped to [0, 1], 5 decimal places."""
    return f"{max(0.0, min(t / total, 1.0)):.5f}"


def generate_svg(grid, path, states):
    N       = len(grid)
    steps   = len(path)
    T       = steps * SPD
    W       = MX + N * STEP + MX
    H       = MY + 7 * STEP + MY

    # Fast lookup: is pos in snake at step i?
    snake_sets = [set(map(tuple, s)) for s in states]

    # Per cell: when does the head arrive, when does the tail leave?
    arrive  = {pos: k for k, pos in enumerate(path)}
    depart  = {}
    for k, pos in enumerate(path):
        dep = steps   # stays till end by default
        for j in range(k + 1, steps):
            if pos not in snake_sets[j]:
                dep = j
                break
        depart[pos] = dep

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    )
    out.append(f'  <rect width="{W}" height="{H}" fill="{BG}" rx="8"/>')

    for ci, col in enumerate(grid):
        for row in range(7):
            count = col[row] if row < len(col) else 0
            x     = MX + ci * STEP
            y     = MY + row * STEP
            pos   = (ci, row)
            base  = level_color(count)

            if pos not in arrive:
                # Not visited by snake — static cell
                out.append(
                    f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="2" fill="{base}"/>'
                )
                continue

            k   = arrive[pos]
            dep = depart[pos]

            t0   = k * SPD           # head arrives
            t1   = (k + 1) * SPD     # head moves on → becomes body
            t2   = dep * SPD         # tail leaves
            t2e  = t2 + SPD * 0.4    # brief eaten flash

            # Determine depth of this cell when first seen as body (always 1 initially)
            bc = body_color(1)

            if dep >= steps:
                # Snake still here at animation end
                values = f"{base};{base};{HEAD};{bc}"
                times  = f"0;{kt(t0,T)};{kt(t0,T)};1"
            else:
                values = f"{base};{base};{HEAD};{bc};{bc};{EATEN};{EATEN}"
                times  = (
                    f"0;{kt(t0,T)};{kt(t0,T)};"
                    f"{kt(t1,T)};{kt(t2,T)};{kt(t2e,T)};1"
                )

            out.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base}">\n'
                f'    <animate attributeName="fill" dur="{T:.2f}s" repeatCount="indefinite"\n'
                f'      calcMode="discrete" values="{values}" keyTimes="{times}"/>\n'
                f'  </rect>'
            )

    out.append('</svg>')
    return '\n'.join(out)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        print("GITHUB_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching contributions for {USERNAME}...")
    weeks  = fetch_contributions()
    grid   = build_grid(weeks)
    path   = build_path(grid)
    states = compute_states(grid, path)

    print(f"Grid   : {len(grid)} weeks × 7 days = {len(path)} cells")
    print(f"Snake  : starts at {INIT_LEN}, grows to {len(states[-1])} segments")

    svg = generate_svg(grid, path, states)

    out_dir = os.path.dirname(OUTPUT_FILE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(svg)

    print(f"Written : {OUTPUT_FILE}  ({len(svg)/1024:.1f} KB)")


if __name__ == '__main__':
    main()
