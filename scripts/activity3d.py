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


def fetch_graphql(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "activity3d"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    if d.get("errors") or not (d.get("data") or {}).get("user"):
        raise RuntimeError(f"GraphQL returned: {d.get('errors') or d}")
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[(day["weekday"], day["contributionCount"], day["date"]) for day in w["contributionDays"]] for w in weeks]


def fetch_public(user):
    """Public contribution calendar HTML: no token needed."""
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0 activity3d"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    days = {}
    for m in re.finditer(r'data-date="(\d{4}-\d\d-\d\d)"\s+id="([^"]+)"[^>]*data-level="(\d)"', page):
        days[m.group(2)] = [m.group(1), int(m.group(3))]
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        if m.group(1) in days:
            n = re.match(r"\s*(\d+)", m.group(2))
            days[m.group(1)].append(int(n.group(1)) if n else 0)
    if not days:
        raise RuntimeError("could not parse the public contribution calendar")
    weeks, cur, last = [], [], None
    for dt, lvl, *cnt in sorted(days.values()):
        dd = date.fromisoformat(dt)
        wd = (dd.weekday() + 1) % 7  # Sunday = 0, like GitHub
        if cur and wd == 0:
            weeks.append(cur); cur = []
        cur.append((wd, cnt[0] if cnt else lvl * 3, dt))
    if cur:
        weeks.append(cur)
    return weeks


def fetch(user, token):
    if token:
        try:
            return fetch_graphql(user, token)
        except Exception as e:
            print(f"::warning::GraphQL fetch failed ({e}); using the public calendar instead")
    return fetch_public(user)


def demo():
    random.seed(4)
    weeks, start = [], date.today() - timedelta(days=date.today().weekday() + 1 + 52 * 7)
    for w in range(53):
        base = 2 + 6 * (0.5 + 0.5 * math.sin(w / 6))
        weeks.append([(d, max(0, int(random.gauss(base, 3)) if random.random() > .25 else 0),
                       (start + timedelta(days=7 * w + d)).isoformat()) for d in range(7)])
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
    maxc = max([day[1] for w in weeks for day in w] + [1])
    W, H = 1000, 420
    cells = []
    for wi, w in enumerate(weeks):
        for d, c, *_ in w:
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


HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def _fonts(files):
    import base64
    out = ""
    for alias, fn in files:
        p = os.path.join(HERE, "..", "assets", "fonts", fn + ".woff2")
        if os.path.exists(p):
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            out += f"@font-face{{font-family:'{alias}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
    return out


CITY = {
    "poster": dict(bg="#063D2C", floor="#0A4A36", empty="#0B5139", lv=["#138A63", "#1FE5A0", "#9DF7D3", "#9DF7D3"],
                   peak="#F2C14E", hot="#9DF7D3", dim="#7FB9A2", cap_font="SI", mono="M",
                   fonts=[("M", "spacemono-r"), ("MB", "spacemono-b"), ("SI", "instserif-i")],
                   cap="one tower per day, taller means more activity", peak_word="PEAK DAY", fmt=str.upper,
                   total="{n} contributions in the last 12 months", legend="gold tower = busiest day of the year"),
    "quant": dict(bg="#04120D", floor="#0A2219", empty="#0C2A1D", lv=["#0F5A3C", "#139A64", "#19C37D", "#5CF2B1"],
                  peak="#F0B429", hot="#5CF2B1", dim="#3E7A5E", cap_font="M", mono="M",
                  fonts=[("M", "plexmono-r"), ("MB", "plexmono-sb")],
                  cap="INTRADAY VOLUME  ·  one tower per session, height = contributions", peak_word="PEAK SESSION", fmt=str.upper,
                  total="VOL 12M  {n}", legend="amber = highest-volume session"),
    "lab": dict(bg="#062019", floor="#0B2E24", empty="#0E3429", lv=["#1F6B52", "#2FA078", "#3FD39A", "#8EF0C6"],
                peak="#D9B45B", hot="#8EF0C6", dim="#6F9E8B", cap_font="SI", mono="M",
                fonts=[("M", "plexmono-r"), ("SI", "instserif-i")],
                cap="one tower per day; height grows with the square root of contributions", peak_word="maximum", fmt=lambda x: x,
                total="n = {n} contributions over 12 months", legend="gold: the maximum, shared across all figures"),
    "matrix": dict(bg="#010805", floor="#03130C", empty="#05190F", lv=["#0A4F31", "#07915A", "#00E68A", "#9CFFD0"],
                   peak="#D6FFEC", hot="#00E68A", dim="#1F7A50", cap_font="M", mono="M",
                   fonts=[("M", "sharetech")],
                   cap="# one tower per day, height = commits", peak_word="max()", fmt=str.lower,
                   total="$ git rev-list --count  ->  {n}", legend="# white tower = argmax(day)"),
}


def render_city(weeks, theme):
    """Themed 3D contribution city with month labels and the peak day highlighted."""
    c = CITY[theme]
    W, H = 1000, 440
    wx, wy, dx, dy = 15.4, 3.1, -9.0, 7.6
    ox, oy = 128, 130
    days = [(wi, d[0], d[1], d[2]) for wi, w in enumerate(weeks) for d in w]
    maxc = max([k[2] for k in days] + [1])
    peak = max(days, key=lambda k: k[2])
    total = sum(k[2] for k in days)
    f = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)
    out = []
    corners = [(0, 0), (len(weeks), 0), (len(weeks), 7), (0, 7)]
    out.append(f'<polygon points="{f([(ox + a*wx + b*dx, oy + a*wy + b*dy) for a, b in corners])}" fill="{c["floor"]}"/>')
    px_ = py_ = None
    for wi, d, cnt, dt in sorted(days, key=lambda k: (k[0] + k[1], k[0])):
        is_peak = (wi, d) == (peak[0], peak[1]) and cnt > 0
        col = c["peak"] if is_peak else (c["lv"][level(cnt, maxc) - 1] if cnt else c["empty"])
        h = 3 if cnt == 0 else 8 + 96 * math.sqrt(cnt / maxc)
        bx, by, s_ = ox + wi * wx + d * dx, oy + wi * wy + d * dy, 0.86
        p0, p1 = (bx, by), (bx + wx * s_, by + wy * s_)
        p2, p3 = (bx + wx * s_ + dx * s_, by + wy * s_ + dy * s_), (bx + dx * s_, by + dy * s_)
        top = [(x, y - h) for x, y in (p0, p1, p2, p3)]
        out.append(f'<g class="b" style="animation-delay:{wi*0.035 + d*0.01:.2f}s">'
                   f'<polygon points="{f([p3, p2, top[2], top[3]])}" fill="{shade(col, .62)}"/>'
                   f'<polygon points="{f([p2, p1, top[1], top[2]])}" fill="{shade(col, .8)}"/>'
                   f'<polygon points="{f(top)}" fill="{col}"/></g>')
        if is_peak:
            px_, py_ = top[0][0] + 4, top[0][1] - 10
    prev, labels = None, []
    for wi, w in enumerate(weeks):
        dd = date.fromisoformat(w[0][2])
        if dd.month != prev:
            labels.append((wi, c["fmt"](f"{MONTHS[dd.month-1]} {dd.year % 100:02d}")))
            prev = dd.month
    if len(labels) > 1 and labels[1][0] - labels[0][0] < 3:
        labels = labels[1:]
    for wi, lab in labels:
        x, y = ox + wi * wx + 7 * dx, oy + wi * wy + 7 * dy
        out.append(f'<line x1="{x:.1f}" y1="{y+2:.1f}" x2="{x-6:.1f}" y2="{y+10:.1f}" stroke="{c["dim"]}"/>'
                   f'<text x="{x-8:.1f}" y="{y+22:.1f}" text-anchor="middle" class="m" font-size="10.5" fill="{c["dim"]}">{lab}</text>')
    if px_ is not None:
        pd = date.fromisoformat(peak[3])
        plabel = c["fmt"](f"{c['peak_word']}  {MONTHS[pd.month-1]} {pd.day}, {pd.year}  ·  {peak[2]}")
        out.append(f'<line x1="{px_:.1f}" y1="{py_:.1f}" x2="{px_+40:.1f}" y2="{py_-34:.1f}" stroke="{c["peak"]}"/>'
                   f'<text x="{px_+44:.1f}" y="{py_-38:.1f}" class="m" font-size="12" fill="{c["peak"]}">{plabel}</text>')
    style = (_fonts(c["fonts"]) + ".m{font-family:'M',monospace}.si{font-family:'SI',serif}"
             ".b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:up 1.1s cubic-bezier(.2,.9,.3,1.2) forwards}"
             "@keyframes up{to{transform:scaleY(1)}}@media (prefers-reduced-motion:reduce){.b{animation:none;transform:none}}")
    capcls = "si" if c["cap_font"] == "SI" else "m"
    cap = (f'<text x="34" y="30" class="{capcls}" font-size="{19 if capcls == "si" else 13}" fill="{c["hot"]}">{c["cap"]}</text>'
           f'<text x="{W-34}" y="{H-22}" text-anchor="end" class="m" font-size="11" fill="{c["peak"]}">{c["legend"]}</text>'
           f'<text x="34" y="{H-22}" class="m" font-size="11" fill="{c["dim"]}">{c["total"].format(n=total)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="3D contribution city"><style>text{{white-space:pre}}{style}</style>'
            f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>{cap}{"".join(out)}</svg>')


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
        weeks = demo() if a.demo else fetch(a.user, os.environ.get("GITHUB_TOKEN"))
        print(f"{len(weeks)} weeks, {sum(day[1] for w in weeks for day in w)} contributions")
        for th in CITY:
            p = os.path.join(a.out, f"activity-{th}.svg")
            open(p, "w").write(render_city(weeks, th))
            print("wrote", p)
