#!/usr/bin/env python3
"""
Growing snake SVG generator — CSS @keyframes based.
Each cell gets its own animation that flashes white (head), then green (body),
then near-black (eaten) as the snake passes through.
"""

import os, sys, random, requests

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
SPD          = 0.08   # seconds per step
INIT_LEN     = 5
MAX_LEN      = 30
GROWTH_SCALE = 0.6
SEED         = 42

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = '#0D0D0D'
LEVELS = ['#0D1A0D', '#0D3B0D', '#1A6B1A', '#00A550', '#00FF41']
HEAD   = '#FFFFFF'   # white head pops against green
BODY   = '#00FF41'   # neon green body
EATEN  = '#060D06'   # near-black after eaten
EPS    = 0.02        # % gap for "instant" CSS jump (≈ 0.005s)


# ── GitHub API ────────────────────────────────────────────────────────────────

def fetch_contributions():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks { contributionDays { contributionCount } }
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
        print(f"API error {r.status_code}", file=sys.stderr); sys.exit(1)
    d = r.json()
    if 'errors' in d:
        print(f"GraphQL: {d['errors']}", file=sys.stderr); sys.exit(1)
    return d['data']['user']['contributionsCollection']['contributionCalendar']['weeks']


# ── Grid ──────────────────────────────────────────────────────────────────────

def build_grid(weeks):
    grid = []
    for week in weeks:
        col = [d['contributionCount'] for d in week['contributionDays']]
        while len(col) < ROWS: col.append(0)
        grid.append(col)
    while len(grid) < COLS: grid.append([0] * ROWS)
    return grid[:COLS]


# ── Random walk ───────────────────────────────────────────────────────────────

def random_walk():
    """Space-filling random walk visiting every cell exactly once."""
    rng = random.Random(SEED)
    visited = [[False] * ROWS for _ in range(COLS)]
    path, stack = [(0, 0)], [(0, 0)]
    visited[0][0] = True

    def nbrs(c, r):
        ds = [(0,1),(0,-1),(1,0),(-1,0)]
        rng.shuffle(ds)
        return [(c+dc, r+dr) for dc,dr in ds
                if 0 <= c+dc < COLS and 0 <= r+dr < ROWS]

    while len(path) < COLS * ROWS:
        c, r = stack[-1]
        opts = [(nc,nr) for nc,nr in nbrs(c,r) if not visited[nc][nr]]
        if opts:
            nc, nr = rng.choice(opts)
            visited[nc][nr] = True
            path.append((nc, nr))
            stack.append((nc, nr))
        else:
            stack.pop()
            if not stack:
                for ci in range(COLS):
                    for ri in range(ROWS):
                        if not visited[ci][ri]:
                            visited[ci][ri] = True
                            path.append((ci, ri))
                            stack.append((ci, ri))
                            break
                    if stack: break
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def level_color(count):
    if count == 0: return LEVELS[0]
    if count <= 1: return LEVELS[1]
    if count <= 3: return LEVELS[2]
    if count <= 8: return LEVELS[3]
    return LEVELS[4]

def pct(t, total):
    """Convert time to CSS percentage string, clamped 0–100."""
    return round(max(0.0, min(t / total * 100, 100.0)), 4)


# ── SVG ───────────────────────────────────────────────────────────────────────

def generate_svg(grid, path, states):
    steps  = len(path)
    T      = steps * SPD
    W      = MX + COLS * STEP + MX
    H      = MY + ROWS * STEP + MY

    # Precompute: when does each cell arrive/depart
    snake_sets = [set(map(tuple, s)) for s in states]
    arrive = {pos: k for k, pos in enumerate(path)}
    depart = {}
    for k, pos in enumerate(path):
        dep = steps
        for j in range(k + 1, steps):
            if pos not in snake_sets[j]:
                dep = j
                break
        depart[pos] = dep

    css_rules = []
    rects     = []

    for ci in range(COLS):
        col = grid[ci] if ci < len(grid) else [0] * ROWS
        for row in range(ROWS):
            count = col[row] if row < len(col) else 0
            x     = MX + ci * STEP
            y     = MY + row * STEP
            pos   = (ci, row)
            base  = level_color(count)
            cname = f"c{ci}x{row}"

            if pos not in arrive:
                rects.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base}"/>')
                continue

            k   = arrive[pos]
            dep = depart[pos]

            # percentage keyframe positions
            pa  = pct(k * SPD, T)           # head arrives
            pb  = min(pa + EPS, pct((k+1)*SPD, T) - EPS)  # head leaves → body
            pb  = max(pa + EPS, pb)
            pd  = pct(dep * SPD, T)         # tail leaves → eaten
            pde = min(pd + EPS, 99.99)

            # Build @keyframes rule
            if pa <= 0:
                # cell is first — starts as head
                if dep >= steps:
                    kf = f"@keyframes {cname}{{0%{{fill:{HEAD}}}{pb}%,100%{{fill:{BODY}}}}}"
                else:
                    kf = (f"@keyframes {cname}{{0%{{fill:{HEAD}}}{pb}%,{pd}%{{fill:{BODY}}}"
                          f"{pde}%,100%{{fill:{EATEN}}}}}")
            else:
                pa0 = max(0, pa - EPS)
                if dep >= steps:
                    kf = (f"@keyframes {cname}{{0%,{pa0}%{{fill:{base}}}"
                          f"{pa}%{{fill:{HEAD}}}{pb}%,100%{{fill:{BODY}}}}}")
                else:
                    kf = (f"@keyframes {cname}{{0%,{pa0}%{{fill:{base}}}"
                          f"{pa}%{{fill:{HEAD}}}{pb}%,{pd}%{{fill:{BODY}}}"
                          f"{pde}%,100%{{fill:{EATEN}}}}}")

            css_rules.append(kf)
            css_rules.append(
                f".{cname}{{animation:{cname} {T:.2f}s linear infinite}}")
            rects.append(
                f'<rect class="{cname}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base}"/>')

    style_block = "<style>" + "".join(css_rules) + "</style>"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'  <rect width="{W}" height="{H}" fill="{BG}" rx="8"/>',
        style_block,
    ] + rects + ['</svg>']

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        print("GITHUB_TOKEN not set", file=sys.stderr); sys.exit(1)

    print(f"Fetching contributions for {USERNAME}...")
    weeks  = fetch_contributions()
    grid   = build_grid(weeks)
    path   = random_walk()
    states = compute_states(grid, path)

    print(f"Grid : {COLS}×{ROWS} = {len(path)} cells")
    print(f"Snake: starts {INIT_LEN}, max {MAX_LEN}, ends {len(states[-1])}")

    svg = generate_svg(grid, path, states)

    out_dir = os.path.dirname(OUTPUT_FILE)
    if out_dir: os.makedirs(out_dir, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(svg)
    print(f"Done : {OUTPUT_FILE} ({len(svg)/1024:.1f} KB)")


if __name__ == '__main__':
    main()
