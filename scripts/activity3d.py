#!/usr/bin/env python3
"""Isometric 3D contribution skyline, one SVG per README theme. No stats, just the city.

Runs inside GitHub Actions (see .github/workflows/activity.yml). Standard library only.

  GITHUB_TOKEN=... python scripts/activity3d.py --user Adel-Lis --out dist
  python scripts/activity3d.py --demo --out dist      # random data, for previewing locally

It also wraps Platane/snk's transparent snake SVGs in a themed background (--wrap-snakes).
"""
import argparse, json, math, os, random, re, urllib.request
from datetime import date, timedelta

THEMES = {
    "quant":  {"bg": "#04120D", "floor": "#0A2219", "lv": ["#0E2C20", "#0F5A3C", "#139A64", "#19C37D", "#5CF2B1"]},
    "lab":    {"bg": "#062019", "floor": "#0B2E24", "lv": ["#12382D", "#1F6B52", "#2FA078", "#3FD39A", "#D9B45B"]},
    "matrix": {"bg": "#010805", "floor": "#03130C", "lv": ["#062014", "#0A4F31", "#07915A", "#00E68A", "#9CFFD0"]},
    "poster": {"bg": "#063D2C", "floor": "#0A4A36", "lv": ["#0D5641", "#138A63", "#1FE5A0", "#9DF7D3", "#F2C14E"]},
}

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
weeks{contributionDays{date contributionCount weekday}}}}}}"""


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[(day["weekday"], day["contributionCount"]) for day in w["contributionDays"]] for w in weeks]


def demo():
    random.seed(4)
    weeks = []
    for w in range(53):
        base = 2 + 6 * (0.5 + 0.5 * math.sin(w / 6))
        weeks.append([(d, max(0, int(random.gauss(base, 3)) if random.random() > .25 else 0)) for d in range(7)])
    return weeks


def shade(hexc, f):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def level(c, mx):
    if c == 0:
        return 0
    q = c / mx
    return 1 if q < .25 else 2 if q < .5 else 3 if q < .75 else 4


def render(weeks, theme):
    t = THEMES[theme]
    # isometric basis: week axis runs right-down, day axis runs left-down
    wx, wy, dx, dy = 15.4, 3.1, -9.0, 7.6
    ox, oy = 128, 36
    maxc = max([c for w in weeks for _, c in w] + [1])
    W, H = 1000, 420
    cells = []
    for wi, w in enumerate(weeks):
        for d, c in w:
            cells.append((wi, d, c))
    cells.sort(key=lambda k: (k[0] + k[1], k[0]))
    out = []
    # floor slab
    corners = [(0, 0), (len(weeks), 0), (len(weeks), 7), (0, 7)]
    pts = " ".join(f"{ox + a*wx + b*dx:.1f},{oy + 150 + a*wy + b*dy:.1f}" for a, b in corners)
    out.append(f'<polygon points="{pts}" fill="{t["floor"]}"/>')
    for wi, d, c in cells:
        lv = level(c, maxc)
        h = 3 if c == 0 else 8 + 96 * math.sqrt(c / maxc)
        col = t["lv"][lv]
        bx = ox + wi * wx + d * dx
        by = oy + 150 + wi * wy + d * dy
        s = 0.86  # gap between bars
        p0 = (bx, by)
        p1 = (bx + wx * s, by + wy * s)
        p2 = (bx + wx * s + dx * s, by + wy * s + dy * s)
        p3 = (bx + dx * s, by + dy * s)
        top = [(x, y - h) for x, y in (p0, p1, p2, p3)]
        f = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)
        left = [p3, p2, top[2], top[3]]
        right = [p2, p1, top[1], top[2]]
        delay = wi * 0.035 + d * 0.01
        out.append(
            f'<g class="b" style="animation-delay:{delay:.2f}s">'
            f'<polygon points="{f(left)}" fill="{shade(col, .62)}"/>'
            f'<polygon points="{f(right)}" fill="{shade(col, .8)}"/>'
            f'<polygon points="{f(top)}" fill="{col}"/></g>')
    style = (".b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);"
             "animation:up 1.1s cubic-bezier(.2,.9,.3,1.2) forwards}@keyframes up{to{transform:scaleY(1)}}"
             "@media (prefers-reduced-motion:reduce){.b{animation:none;transform:none}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="3D contribution skyline"><style>{style}</style>'
            f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>{"".join(out)}</svg>')


def wrap_snake(path, theme):
    svg = open(path).read()
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', svg)
    if not m or "data-wrapped" in svg:
        return
    x, y, w, h = (float(v) for v in m.groups())
    pad = 14
    svg = svg.replace(m.group(0), f'viewBox="{x-pad} {y-pad} {w+2*pad} {h+2*pad}" data-wrapped="1"', 1)
    svg = re.sub(r'(<svg[^>]*>)', r'\1' + f'<rect x="{x-pad}" y="{y-pad}" width="{w+2*pad}" height="{h+2*pad}" rx="12" fill="{THEMES[theme]["bg"]}"/>', svg, 1)
    svg = re.sub(r'\swidth="[\d.]+"\s', ' ', svg, 1)
    svg = re.sub(r'\sheight="[\d.]+"\s', ' ', svg, 1)
    open(path, "w").write(svg)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "Adel-Lis"))
    ap.add_argument("--out", default="dist")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--wrap-snakes", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.wrap_snakes:
        for th in THEMES:
            p = os.path.join(a.out, f"snake-{th}.svg")
            if os.path.exists(p):
                wrap_snake(p, th)
                print("wrapped", p)
    else:
        weeks = demo() if a.demo else fetch(a.user, os.environ["GITHUB_TOKEN"])
        for th in THEMES:
            p = os.path.join(a.out, f"skyline-{th}.svg")
            open(p, "w").write(render(weeks, th))
            print("wrote", p)
