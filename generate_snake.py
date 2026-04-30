#!/usr/bin/env python3
"""
Growing snake SVG generator for GitHub profile README.
Snake takes a random walk through the contribution grid,
growing longer each time it eats a contribution square.
"""

import os
import sys
import random
import requests

USERNAME    = os.environ.get('GITHUB_USERNAME', 'Joshuaisikah')
TOKEN       = os.environ.get('GITHUB_TOKEN', '')
OUTPUT_FILE = os.environ.get('OUTPUT_FILE', 'assets/snake-growing.svg')

# ── Grid ──────────────────────────────────────────────────────────────────────
CELL  = 12
GAP   = 3
STEP  = CELL + GAP
MX    = 16
MY    = 20
COLS  = 53
ROWS  = 7

# ── Animation ─────────────────────────────────────────────────────────────────
SPD          = 0.07   # seconds per step
INIT_LEN     = 5
MAX_LEN      = 30    # snake never grows beyond this
GROWTH_SCALE = 0.6
RANDOM_SEED  = 42     # reproducible random walk

# ── Cyberpunk palette ─────────────────────────────────────────────────────────
BG     = '#0D0D0D'
LEVELS = ['#0D1A0D', '#0D3B0D', '#1A6B1A', '#00A550', '#00FF41']
HEAD   = '#FFE600'
BODY   = ['#00FF41', '#00D936', '#00B82C', '#009622', '#007518']
EATEN  = '#060D06'


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


def build_grid(weeks):
    grid = []
    for week in weeks:
        col = [d['contributionCount'] for d in week['contributionDays']]
        while len(col) < ROWS:
            col.append(0)
        grid.append(col)
    # Pad to COLS wide
    while len(grid) < COLS:
        grid.append([0] * ROWS)
    return grid[:COLS]


# ── Random walk path ──────────────────────────────────────────────────────────

def random_walk(grid):
    """
    Walk every cell exactly once using a space-filling random walk.
    Falls back to scanning unvisited neighbours; backtracks if stuck.
    Visits all COLS×ROWS cells.
    """
    rng = random.Random(RANDOM_SEED)
    total = COLS * ROWS
    visited = [[False] * ROWS for _ in range(COLS)]

    def neighbours(c, r):
        dirs = [(0,1),(0,-1),(1,0),(-1,0)]
        rng.shuffle(dirs)
        return [
            (c+dc, r+dr)
            for dc, dr in dirs
            if 0 <= c+dc < COLS and 0 <= r+dr < ROWS
        ]

    # Start at top-left
    path = [(0, 0)]
    visited[0][0] = True
    stack = [(0, 0)]

    while len(path) < total:
        c, r = stack[-1]
        unvisited = [(nc, nr) for nc, nr in neighbours(c, r) if not visited[nc][nr]]
        if unvisited:
            nc, nr = rng.choice(unvisited)
            visited[nc][nr] = True
            path.append((nc, nr))
            stack.append((nc, nr))
        else:
            # Backtrack
            stack.pop()
            if not stack:
                # Find any unvisited cell and teleport (shouldn't happen often)
                for ci in range(COLS):
                    for ri in range(ROWS):
                        if not visited[ci][ri]:
                            visited[ci][ri] = True
                            path.append((ci, ri))
                            stack.append((ci, ri))
                            break
                    if stack:
                        break

    return path


# ── Snake state ───────────────────────────────────────────────────────────────

def compute_states(grid, path):
    states, snake, target = [], [], INIT_LEN
    for col, row in path:
        count = grid[col][row] if col < len(grid) and row < len(grid[col]) else 0
        snake = [(col, row)] + snake
        if count > 0:
            target = min(MAX_LEN, target + max(1, int(count * GROWTH_SCALE)))
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


def kt(t, total):
    return f"{max(0.0, min(t / total, 1.0)):.5f}"


def generate_svg(grid, path, states):
    steps = len(path)
    T     = steps * SPD
    W     = MX + COLS * STEP + MX
    H     = MY + ROWS * STEP + MY

    snake_sets = [set(map(tuple, s)) for s in states]

    arrive  = {pos: k for k, pos in enumerate(path)}
    depart  = {}
    for k, pos in enumerate(path):
        dep = steps
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

    for ci in range(COLS):
        col = grid[ci] if ci < len(grid) else [0] * ROWS
        for row in range(ROWS):
            count = col[row] if row < len(col) else 0
            x     = MX + ci * STEP
            y     = MY + row * STEP
            pos   = (ci, row)
            base  = level_color(count)

            if pos not in arrive:
                out.append(
                    f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="2" fill="{base}"/>'
                )
                continue

            k   = arrive[pos]
            dep = depart[pos]
            t0  = k * SPD
            t1  = (k + 1) * SPD
            t2  = dep * SPD
            t2e = t2 + SPD * 0.4

            bc = BODY[1]  # body color

            # Ensure strictly increasing keyTimes by nudging duplicates
            def safe_kt(t):
                return max(0.0, min(t / T, 1.0))

            kf0 = 0.0
            kfa = safe_kt(t0)
            kfb = safe_kt(t0) + 1e-5   # head flash start (tiny nudge after arrive)
            kfc = safe_kt(t1)
            kfd = safe_kt(t2)
            kfe = safe_kt(t2e)
            kff = 1.0

            # Clamp and ensure monotone
            kfb = min(kfb, kfc - 1e-5)
            kfd = max(kfd, kfc + 1e-5)
            kfe = max(kfe, kfd + 1e-5)
            kfe = min(kfe, kff - 1e-5)

            def fk(v):
                return f"{v:.5f}"

            if dep >= steps:
                values = f"{base};{base};{HEAD};{bc}"
                times  = f"{fk(kf0)};{fk(kfa)};{fk(kfb)};1"
            else:
                values = f"{base};{base};{HEAD};{bc};{bc};{EATEN};{EATEN}"
                times  = (
                    f"{fk(kf0)};{fk(kfa)};{fk(kfb)};"
                    f"{fk(kfc)};{fk(kfd)};{fk(kfe)};{fk(kff)}"
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
    path   = random_walk(grid)
    states = compute_states(grid, path)

    print(f"Grid   : {COLS} weeks × {ROWS} days = {len(path)} cells")
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
