"""Render the solarpunk garden (animated isometric SVG) from data/contributions.json."""
import html
import json
import math
import os
import random
from datetime import date
from pathlib import Path

import i18n

ROOT = Path(__file__).parent
# Geometry, recomputed by layout() from the number of years
HW, HH = 14, 7          # half width / half height of a tile
SIDE = 3                  # visible soil thickness
OX, OY = 138, 150         # screen origin of the grid
W, H = 1000, 640
PLANT_K = 1.3             # plant scale relative to the base drawing
COLS, ROWS_PER_YEAR = 54, 7
MARGIN, TOP = 50, 150

NORTH = {  # month -> season (temperate climate, northern hemisphere)
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}


def _months(**seasons):
    """_months(wet="11 12 1 2 3 4", dry="5 6 7 8 9 10") -> {month: season}."""
    return {int(m): name for name, ms in seasons.items() for m in ms.split()}


# climate name -> (season of each month, seasons in legend order)
CLIMATES = {
    "temperate-north": (NORTH, ("spring", "summer", "autumn", "winter")),
    # In the south, seasons are the northern ones shifted by six months.
    "temperate-south": ({m: NORTH[(m + 5) % 12 + 1] for m in NORTH}, ("spring", "summer", "autumn", "winter")),
    # South Asia (India, Bangladesh...): the four seasons used by the Indian meteorological department.
    "monsoon": (_months(cool="12 1 2", hot="3 4 5", monsoon="6 7 8 9", postmonsoon="10 11"),
                ("cool", "hot", "monsoon", "postmonsoon")),
    # Two-season tropics: central Brazil, Indonesia, southern Africa...
    "tropical-south": (_months(wet="11 12 1 2 3 4", dry="5 6 7 8 9 10"), ("wet", "dry")),
    # ... and the Sahel, Central America, mainland Southeast Asia.
    "tropical-north": (_months(wet="5 6 7 8 9 10", dry="11 12 1 2 3 4"), ("wet", "dry")),
    # East Asian monsoon, southeast China (Guangdong, Fujian, Hong Kong): mild winter, spring rains,
    # humid summer and typhoons, clear autumn.
    "china-southeast": (_months(mild="12 1 2", plum="3 4 5", humid="6 7 8 9", clear="10 11"),
                        ("mild", "plum", "humid", "clear")),
    # Japan (Honshu): sakura, rainy season (tsuyu, June to mid-July), summer, autumn, winter.
    # A month can be split in two: (season up to the 15th, season after the 15th).
    "japan": ({12: "winter", 1: "winter", 2: "winter", 3: "sakura", 4: "sakura", 5: "spring", 6: "tsuyu",
               7: ("tsuyu", "summer"), 8: "summer", 9: ("summer", "autumn"), 10: "autumn", 11: "autumn"},
              ("sakura", "spring", "tsuyu", "summer", "autumn", "winter")),
}
CLIMATE = os.environ.get("GARDEN_CLIMATE", "").strip().lower()
if not CLIMATE:  # GARDEN_HEMISPHERE is still accepted: it is the old name of the temperate setting
    CLIMATE = "temperate-" + os.environ.get("GARDEN_HEMISPHERE", "north").strip().lower()
if CLIMATE not in CLIMATES:
    raise SystemExit(f"GARDEN_CLIMATE must be one of {', '.join(CLIMATES)}, not {CLIMATE!r}")
SEASONS, LEGEND = CLIMATES[CLIMATE]
LANG = os.environ.get("GARDEN_LANG", "fr").strip().lower()
if LANG not in i18n.STRINGS:
    raise SystemExit(f"GARDEN_LANG must be one of {', '.join(i18n.STRINGS)}, not {LANG!r}")
T = i18n.STRINGS[LANG]
FONT_STACK = T["fonts"] + 'ui-sans-serif,system-ui,"Segoe UI",Helvetica,Arial,sans-serif'


def say(key, **values):
    """Translated sentence with its placeholders filled in, escaped for SVG."""
    return html.escape(T[key].format(**values), quote=False)


# Per season: colors (ground, side, foliage, foliage 2, accent) and how plants are drawn.
# heads: possible flower colors; blossom/fruit: dots on trees; tree: leafy or pine; shrub: shrub
# instead of the flower; snow: snow on the panels; puddle: puddles on empty tiles.
PALETTE = {
    "spring": dict(ground="#bfe28f", side="#93b86c", leaf="#8fd16a", leaf2="#6dbb5a", accent="#f6a6c1",
                   heads=("#f6a6c1",), blossom="#f6a6c1"),
    "summer": dict(ground="#86d174", side="#5fa551", leaf="#3fae4a", leaf2="#2f9440", accent="#ffd54a",
                   heads=("#ffd54a", "#ff8fb1", "#ffffff"), core="#c0702a", fruit="#ff6b5e"),
    "autumn": dict(ground="#dcc57d", side="#b39c57", leaf="#e8923a", leaf2="#c4552b", accent="#d9482b",
                   heads=("#e8923a", "#d9482b")),
    "winter": dict(ground="#e9f1f5", side="#bccbd3", leaf="#2f6b4f", leaf2="#25573f", accent="#9ccbe8",
                   tree="pine", shrub=True, snow=True, sprout_leaf="#4f8f6c"),
    # South Asia
    "cool": dict(ground="#d9d58f", side="#aaa365", leaf="#7fa24f", leaf2="#678a3f", accent="#f2c230",
                 heads=("#f2c230", "#ffffff")),  # mustard fields
    "hot": dict(ground="#e2c48a", side="#b89a5e", leaf="#9aa84a", leaf2="#7f8c3d", accent="#e8532b",
                heads=("#e8532b", "#ff9a1f"), blossom="#e8532b"),  # dust and flame trees
    "monsoon": dict(ground="#5fb86a", side="#3f8f4f", leaf="#2f9e4f", leaf2="#1f7f3f", accent="#7ad0e8",
                    heads=("#ff8fb1", "#ffffff"), puddle=True),  # lotus and puddles
    "postmonsoon": dict(ground="#a8d86e", side="#7fae4e", leaf="#58b84a", leaf2="#3f9a3c", accent="#ffb300",
                        heads=("#ffb300", "#ff7a00"), fruit="#ffb300"),  # marigolds
    # Two-season tropics
    "wet": dict(ground="#5fb86a", side="#3f8f4f", leaf="#2f9e4f", leaf2="#1f7f3f", accent="#7ad0e8",
                heads=("#ff8fb1", "#ffd54a", "#ffffff"), puddle=True),
    "dry": dict(ground="#dfc384", side="#b39a5a", leaf="#a8a24a", leaf2="#8a8a3d", accent="#e8923a",
                heads=("#f2c230", "#e8923a")),
    # Southeast China: kumquats, bauhinias, lychees, osmanthus
    "mild": dict(ground="#a6d48e", side="#7fab69", leaf="#4fa65a", leaf2="#3a8a49", accent="#ff8fb1",
                 heads=("#ff8fb1", "#ffffff", "#e05aa0"), blossom="#ff8fb1", fruit="#ff9a1f"),
    "plum": dict(ground="#8fd0a0", side="#64a678", leaf="#3fae6a", leaf2="#2f8f58", accent="#e05aa0",
                 heads=("#e05aa0", "#ff8fb1"), blossom="#e05aa0", puddle=True),
    "humid": dict(ground="#55b56a", side="#3a8f4e", leaf="#2f9e4f", leaf2="#1f7f3f", accent="#7ad0e8",
                  heads=("#ff8fb1", "#ffffff"), fruit="#e0334a", puddle=True),
    "clear": dict(ground="#bcd97c", side="#92ad56", leaf="#5dba4a", leaf2="#43a23a", accent="#ffd54a",
                  heads=("#ffd54a", "#ffb300"), fruit="#ff9a1f"),
    # Japan: cherry blossoms, rainy-season hydrangeas (summer, autumn and winter are the temperate ones)
    "sakura": dict(ground="#e0e6b0", side="#98b872", leaf="#f7c1d6", leaf2="#eea3c1", accent="#f6a6c1",
                   heads=("#f6a6c1", "#ffffff"), blossom="#ffffff", sprout_leaf="#7fc46a", tuft="#6dbb5a"),
    "tsuyu": dict(ground="#6fb59a", side="#4a8f78", leaf="#4aa88a", leaf2="#2f8a6f", accent="#8a9be8",
                  heads=("#8a9be8", "#b58be8", "#e88bc8"), puddle=True),
    "earth": dict(ground="#c9a97a", side="#9c7e56", leaf="#a98a5d", leaf2="#a98a5d", accent="#a98a5d"),  # packed earth, upcoming days
}
TRUNK = "#7a5636"
PANEL = "#2f6fb5"
NIGHT = "#0b1d2e"


def mix(hex_color, other, t):
    a = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


class Theme:
    def __init__(self, dark):
        self.dark = dark
        self.text = "#cfe3f0" if dark else "#2c4a3a"
        self.sky = ("#0a1626", "#16304a") if dark else ("#dff3ff", "#fff7e0")

    def c(self, color):
        return mix(color, NIGHT, 0.55) if self.dark else color


def layout(n_years):
    """Scale the tiles so the whole bed fits in W."""
    global HW, HH, OX, OY, H, PLANT_K
    rows = n_years * ROWS_PER_YEAR
    HW = min(14, (W - 2 * MARGIN) / (COLS + rows))
    HH = HW / 2
    PLANT_K = HW / 14 * 1.3
    OX, OY = MARGIN + rows * HW, TOP
    H = round(OY + (COLS + rows) * HH + 70)


def grid_pos(iso, years):
    """Column = week of the year, row = day of the week, one block of 7 rows per year."""
    d = date.fromisoformat(iso)
    jan1 = date(d.year, 1, 1)
    col = ((d - jan1).days + (jan1.weekday() + 1) % 7) // 7
    return col, years.index(d.year) * ROWS_PER_YEAR + (d.weekday() + 1) % 7


def season_of(iso):
    season = SEASONS[int(iso[5:7])]
    if isinstance(season, tuple):  # month split in two
        return season[0] if int(iso[8:]) <= 15 else season[1]
    return season


def levels(days):
    """Level 0-4 per day, by quartiles of the active days."""
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    if not counts:
        return [0] * len(days)
    q = [counts[min(len(counts) - 1, int(len(counts) * p))] for p in (0.25, 0.5, 0.75)]
    out = []
    for d in days:
        n = d["count"]
        out.append(0 if n == 0 else 1 if n <= q[0] else 2 if n <= q[1] else 3 if n <= q[2] else 4)
    return out


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def tile(cx, cy, season, th):
    p = PALETTE[season]
    g, s = th.c(p["ground"]), th.c(p["side"])
    top = f"{f(cx)},{f(cy - HH)} {f(cx + HW)},{f(cy)} {f(cx)},{f(cy + HH)} {f(cx - HW)},{f(cy)}"
    left = f"{f(cx - HW)},{f(cy)} {f(cx)},{f(cy + HH)} {f(cx)},{f(cy + HH + SIDE)} {f(cx - HW)},{f(cy + SIDE)}"
    right = f"{f(cx + HW)},{f(cy)} {f(cx)},{f(cy + HH)} {f(cx)},{f(cy + HH + SIDE)} {f(cx + HW)},{f(cy + SIDE)}"
    return (f'<polygon points="{left}" fill="{mix(s, "#000000", 0.12)}"/>'
            f'<polygon points="{right}" fill="{s}"/>'
            f'<polygon points="{top}" fill="{g}"/>')


def circle(x, y, r, fill, extra=""):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{fill}"{extra}/>'


def line(x1, y1, x2, y2, stroke, w=1.2):
    return (f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"/>')


def sprout(x, y, season, th, rng):
    p = PALETTE[season]
    leaf = th.c(p.get("sprout_leaf", p["leaf"]))
    return (line(x, y, x, y - 5, leaf)
            + f'<ellipse cx="{f(x - 2)}" cy="{f(y - 5)}" rx="2.2" ry="1.2" fill="{leaf}" transform="rotate(-30 {f(x - 2)} {f(y - 5)})"/>'
            + f'<ellipse cx="{f(x + 2)}" cy="{f(y - 5.5)}" rx="2.2" ry="1.2" fill="{leaf}" transform="rotate(30 {f(x + 2)} {f(y - 5.5)})"/>')


def flower(x, y, season, th, rng):
    p = PALETTE[season]
    if p.get("shrub"):  # evergreen shrub under the snow
        return (circle(x, y - 4, 4.2, th.c(p["leaf"]))
                + f'<ellipse cx="{f(x)}" cy="{f(y - 7)}" rx="3.6" ry="1.6" fill="{th.c("#ffffff")}"/>')
    return (line(x, y, x, y - 8, th.c("#4f9a4a"))
            + circle(x, y - 9, 3.4, th.c(rng.choice(p["heads"])))
            + circle(x, y - 9, 1.2, th.c(p.get("core", "#ffe28a"))))


def tree(x, y, count_scale, season, th, rng):
    p = PALETTE[season]
    h = 9 + 5 * count_scale
    trunk = th.c(TRUNK)
    if p.get("tree") == "pine":  # snowy fir
        body = f'<rect x="{f(x - 1)}" y="{f(y - 4)}" width="2" height="4" fill="{trunk}"/>'
        for i, (w, off) in enumerate([(8, 4), (6, 4 + h * 0.35), (4, 4 + h * 0.7)]):
            ty = y - off
            body += (f'<polygon points="{f(x)},{f(ty - h * 0.5)} {f(x + w)},{f(ty)} {f(x - w)},{f(ty)}" fill="{th.c(p["leaf"])}"/>'
                     f'<polygon points="{f(x)},{f(ty - h * 0.5)} {f(x + w * 0.45)},{f(ty - h * 0.5 + w * 0.5)} {f(x - w * 0.45)},{f(ty - h * 0.5 + w * 0.5)}" fill="{th.c("#ffffff")}"/>')
        return body
    body = f'<rect x="{f(x - 1.2)}" y="{f(y - h)}" width="2.4" height="{f(h)}" fill="{trunk}"/>'
    cy = y - h - 3
    body += circle(x - 3, cy + 1.5, 5.2, th.c(p["leaf2"])) + circle(x + 3, cy + 1, 5.2, th.c(p["leaf2"]))
    body += circle(x, cy - 1.5, 6.4, th.c(p["leaf"]))
    if p.get("blossom"):
        for _ in range(4):
            body += circle(x + rng.uniform(-6, 6), cy + rng.uniform(-6, 3), 1.1, th.c(p["blossom"]))
    if p.get("fruit"):
        for _ in range(3):
            body += circle(x + rng.uniform(-5, 5), cy + rng.uniform(-4, 3), 1.1, th.c(p["fruit"]))
    return body


def turbine(x, y, count_scale, season, th, rng):
    """Wind turbine + solar panel: the highest activity level."""
    mast = 24 + 8 * count_scale
    top = y - mast
    white = th.c("#f4f7f5")
    dur = rng.uniform(3.5, 6)
    blades = "".join(line(x, top, x + 7.5 * math.cos(math.radians(a)), top + 7.5 * math.sin(math.radians(a)), white, 1.6)
                     for a in (-90, 30, 150))
    out = line(x, y, x, top, th.c("#d7dfdb"), 1.8)
    out += (f'<g>{blades}<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {f(x)} {f(top)}" to="360 {f(x)} {f(top)}" dur="{dur:.1f}s" repeatCount="indefinite"/></g>')
    out += circle(x, top, 1.6, th.c("#8fa39a"))
    # tilted solar panel at the foot of the mast
    px, py = x - 7, y + 1
    pts = f"{f(px - 5)},{f(py)} {f(px + 5)},{f(py - 3)} {f(px + 5)},{f(py + 2)} {f(px - 5)},{f(py + 5)}"
    panel = th.c("#ffffff") if PALETTE[season].get("snow") else th.c(PANEL)
    out += f'<polygon points="{pts}" fill="{panel}" stroke="{th.c("#9fb7c9")}" stroke-width=".6"/>'
    out += circle(x + 6, y - 2, 3, th.c(PALETTE[season].get("sprout_leaf", PALETTE[season]["leaf"])))
    if th.dark:
        out += circle(x, top, 2.6, "#ffe9a8", ' opacity=".35"')
    return out


def plant(level, x, y, season, th, rng, scale):
    if level == 1:
        return sprout(x, y, season, th, rng)
    if level == 2:
        return flower(x, y, season, th, rng)
    if level == 3:
        return f'<g class="sway" style="animation-delay:-{rng.uniform(0, 4):.1f}s">{tree(x, y, scale, season, th, rng)}</g>'
    return turbine(x, y, scale, season, th, rng)


def decor_tuft(x, y, season, th, rng):
    p = PALETTE[season]
    if p.get("snow"):
        return circle(x + rng.uniform(-4, 4), y + rng.uniform(-1, 1), 0.9, th.c("#ffffff"))
    if p.get("puddle"):  # monsoon puddle
        return (f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="4.2" ry="1.8" fill="{th.c("#7ab8d8")}" opacity=".75"/>')
    return line(x, y + 1, x, y - 2.5, th.c(p.get("tuft", p["leaf2"])), 1)


def gardener(th, start, end, dur):
    """Gardener walking back and forth around today's tile, drawn around (0, 0).
    start, end: (x, y) endpoints of the walk in pixels, dur: duration of the round trip.
    Colors are darkened less at night so he stays readable."""
    def c(color):
        return mix(color, NIGHT, 0.2) if th.dark else color
    skin, shirt, overall, boots = c("#f0c7a0"), c("#fff3d6"), c("#3f7fbf"), c("#5a3b24")
    hat, band, can = c("#e8c36a"), c("#c4552b"), c("#4aa6a0")

    def leg(x, values):
        return (f'<g><animateTransform attributeName="transform" type="rotate" values="{values}" dur="1.1s" repeatCount="indefinite"/>'
                f'<rect x="{x}" y="-7" width="2.3" height="5.2" fill="{overall}"/>'
                f'<rect x="{x - .2}" y="-2" width="2.7" height="2" rx=".6" fill="{boots}"/></g>')

    walk = (f'<animateTransform attributeName="transform" type="translate" calcMode="linear" dur="{dur:.0f}s" repeatCount="indefinite" '
            f'values="{start[0]:.1f} {start[1]:.1f};{end[0]:.1f} {end[1]:.1f};{start[0]:.1f} {start[1]:.1f}"/>')
    # turn around: discrete, mirrored during the second half of the walk
    turn = (f'<animateTransform attributeName="transform" type="scale" calcMode="discrete" dur="{dur:.0f}s" repeatCount="indefinite" '
            'values="1 1;-1 1" keyTimes="0;.5"/>')
    return (
        f'<g>{walk}'
        '<ellipse cx="0" cy="1" rx="6" ry="2" fill="#000" opacity=".18"/>'
        f'<g>{turn}'
        '<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -.6;0 0" dur=".55s" repeatCount="indefinite"/>'
        + leg(-2.8, "-18 -1.7 -7;18 -1.7 -7;-18 -1.7 -7") + leg(.5, "18 1.7 -7;-18 1.7 -7;18 1.7 -7") +
        f'<rect x="-3.4" y="-14.5" width="6.8" height="8" rx="1.2" fill="{overall}"/>'
        f'<rect x="-3.4" y="-14.5" width="6.8" height="3" rx="1" fill="{shirt}"/>'
        f'<line x1="-3.4" y1="-13" x2="-5" y2="-8.5" stroke="{shirt}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="0" cy="-17.8" r="2.8" fill="{skin}"/>'
        f'<ellipse cx="0" cy="-19.4" rx="5.8" ry="1.5" fill="{hat}"/><ellipse cx="0" cy="-20.8" rx="3.1" ry="2.2" fill="{hat}"/>'
        f'<rect x="-3.1" y="-20" width="6.2" height="1" fill="{band}"/>'
        f'<line x1="3" y1="-12.5" x2="6" y2="-9.5" stroke="{shirt}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<rect x="4.6" y="-10.5" width="4.4" height="3.4" rx=".8" fill="{can}"/>'
        f'<path d="M5.2 -10.5 q2 -3 3.4 0" fill="none" stroke="{can}" stroke-width=".9"/>'
        f'<line x1="9" y1="-8.8" x2="11.6" y2="-11" stroke="{can}" stroke-width="1"/>'
        '</g></g></g>')


def today_label(x, y, iso, th):
    text = say("date", day=int(iso[8:]), month=T["months"][int(iso[5:7]) - 1])
    w = i18n.text_width(text, 10.5) + 16
    fill, ink = ("#ffe9a8", "#1b2b3a") if th.dark else ("#ffffff", "#2c4a3a")
    return (f'<g><rect x="{f(x - w / 2)}" y="{f(y - 11)}" width="{f(w)}" height="16" rx="8" fill="{fill}" opacity=".75"/>'
            f'<text x="{f(x)}" y="{f(y)}" font-size="10.5" font-weight="700" text-anchor="middle" fill="{ink}">{text}</text></g>')


def sky(th, rng):
    out = (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{th.sky[0]}"/><stop offset="1" stop-color="{th.sky[1]}"/></linearGradient></defs>'
           f'<rect width="{W}" height="{H}" rx="18" fill="url(#sky)"/>')
    if th.dark:
        for _ in range(45):
            out += (f'<circle cx="{rng.uniform(20, W - 20):.0f}" cy="{rng.uniform(15, 260):.0f}" r="{rng.choice([.6, .9, 1.2])}" fill="#fff" '
                    f'class="twinkle" style="animation-delay:-{rng.uniform(0, 5):.1f}s"/>')
        out += ('<mask id="moon"><rect width="100%" height="100%" fill="#fff"/>'
                f'<circle cx="{W - 78}" cy="70" r="20" fill="#000"/></mask>'
                f'<circle cx="{W - 90}" cy="78" r="22" fill="#f3eed2" mask="url(#moon)"/>')
    else:
        out += circle(W - 90, 78, 44, "#ffe9a8", ' opacity=".35"') + circle(W - 90, 78, 26, "#ffd35c")
    for cx, cy, s, dur in [(520, 70, 1.0, 70), (300, 110, .7, 95), (700, 180, .8, 80)]:
        col = "#2a4560" if th.dark else "#ffffff"
        out += (f'<g class="cloud" style="animation-duration:{dur}s;animation-delay:-{rng.uniform(0, dur):.0f}s" opacity=".85">'
                f'<ellipse cx="{cx}" cy="{cy}" rx="{34 * s:.0f}" ry="{10 * s:.0f}" fill="{col}"/>'
                f'<ellipse cx="{cx - 14 * s:.0f}" cy="{cy - 6 * s:.0f}" rx="{16 * s:.0f}" ry="{10 * s:.0f}" fill="{col}"/>'
                f'<ellipse cx="{cx + 10 * s:.0f}" cy="{cy - 8 * s:.0f}" rx="{18 * s:.0f}" ry="{12 * s:.0f}" fill="{col}"/></g>')
    return out


STYLE = """
.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 5s ease-in-out infinite}
@keyframes sway{0%,100%{transform:rotate(-1.6deg)}50%{transform:rotate(1.6deg)}}
.cloud{animation:drift linear infinite}
@keyframes drift{from{transform:translateX(-120px)}to{transform:translateX(220px)}}
.twinkle{animation:tw 4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}
.fly{animation:fly 3.5s ease-in-out infinite}
@keyframes fly{0%,100%{opacity:0}50%{opacity:1}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def render(data, dark):
    th = Theme(dark)
    days = data["days"]
    years = sorted({int(d["date"][:4]) for d in days})
    layout(len(years))
    lv = levels(days)
    maxc = max((d["count"] for d in days), default=1) or 1
    rng_sky = random.Random(7)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f"font-family='{FONT_STACK}'>",
           f'<title>{say("svg_title", login=data["login"])}</title><style>{STYLE}</style>', sky(th, rng_sky)]

    cells = []
    for d, level in zip(days, lv):
        col, row = grid_pos(d["date"], years)
        cells.append((col, row, d, level))
    # Days of the current year that have not happened yet: packed earth up to December 31.
    known = {d["date"] for d in days}
    for y in years:
        day = date(y, 1, 1)
        while day.year == y:
            if day.isoformat() not in known:
                col, row = grid_pos(day.isoformat(), years)
                cells.append((col, row, {"date": day.isoformat(), "count": 0}, -1))
            day = day.fromordinal(day.toordinal() + 1)
    cells.sort(key=lambda c: (c[0] + c[1], c[1]))

    today = max(d["date"] for d in days)
    flies = []
    for c, r, d, level in cells:
        rng = random.Random(d["date"])
        cx, cy = OX + (c - r) * HW, OY + (c + r) * HH
        season = "earth" if level < 0 else season_of(d["date"])
        out.append(tile(cx, cy, season, th))
        if d["date"] == today:  # today's tile pulses gently
            today_pos, today_cr = (cx, cy), (c, r)
            pts = f"{f(cx)},{f(cy - HH)} {f(cx + HW)},{f(cy)} {f(cx)},{f(cy + HH)} {f(cx - HW)},{f(cy)}"
            out.append(f'<polygon points="{pts}" fill="none" stroke="{"#ffe9a8" if dark else "#ffffff"}" stroke-width="1.8">'
                       '<animate attributeName="opacity" values=".3;.85;.3" dur="3s" repeatCount="indefinite"/></polygon>')
        if level < 0:  # a few pebbles on the packed earth
            if rng.random() < 0.25:
                out.append(circle(cx + rng.uniform(-5, 5), cy + rng.uniform(-1.5, 1.5), 0.9, th.c("#8f7650")))
        elif level == 0:
            if rng.random() < 0.3:
                out.append(decor_tuft(cx + rng.uniform(-4, 4), cy, season, th, rng))
        else:
            scale = math.sqrt(d["count"] / maxc)
            out.append(f'<g transform="translate({f(cx)} {f(cy)}) scale({PLANT_K})">'
                       f'{plant(level, 0, 0, season, th, rng, scale)}</g>')
            if dark and level >= 2 and rng.random() < 0.6:
                flies.append((cx + rng.uniform(-10, 10), cy - rng.uniform(10, 34), rng.uniform(-5, 0)))
    for x, y, delay in flies:
        out.append(f'<circle class="fly" cx="{f(x)}" cy="{f(y)}" r="1.3" fill="#fff3a0" style="animation-delay:{delay:.1f}s"/>')
    # gardener last: he strolls over about three tiles around today, in front of the plants
    cx, cy = today_pos
    # The walk follows the week axis but stops at the last existing tile: at the start and end of the
    # year he never leaves the field (the first and last weeks can be partial).
    have = {(c, r) for c, r, _, _ in cells}
    tc, tr = today_cr
    reach = [0, 0]  # possible steps backward then forward, 1.6 at most
    for i, step in enumerate((-1, 1)):
        while reach[i] + 1 <= 1.6 and (tc + step * (reach[i] + 1), tr) in have:
            reach[i] += 1
        if (tc + step * (reach[i] + 1), tr) in have:
            reach[i] = 1.6
    k = PLANT_K * 1.1
    start, end = (-reach[0] * HW / k, -reach[0] * HH / k), (reach[1] * HW / k, reach[1] * HH / k)
    dur = max(4, 5 * (reach[0] + reach[1]))
    out.append(f'<g transform="translate({f(cx)} {f(cy + HH * 0.2)}) scale({k:.2f})">{gardener(th, start, end, dur)}</g>')
    out.append(today_label(cx, cy - 44, today, th))

    # header and legend
    out.append(f'<text x="30" y="46" font-size="22" font-weight="700" fill="{th.text}">{say("title", login=data["login"])}</text>')
    out.append(f'<text x="30" y="68" font-size="13" fill="{th.text}" opacity=".8">'
               f'{say("subtitle", total=i18n.number(data["total"], LANG), first=years[0], last=years[-1])}</text>')
    for i, y in enumerate(years):  # year label along the left edge
        mid = i * ROWS_PER_YEAR + 3
        out.append(f'<text x="{f(OX - mid * HW - 2 * HW)}" y="{f(OY + mid * HH + 4)}" font-size="14" font-weight="700" '
                   f'text-anchor="end" fill="{th.text}" opacity=".85">{y}</text>')
    lx, ly = 30, H - 24 - 18 * len(LEGEND)
    for i, s in enumerate([*LEGEND, "earth"]):
        y = ly + i * 18
        out.append(circle(lx + 5, y, 5, th.c(PALETTE[s]["ground"]), f' stroke="{th.c(PALETTE[s]["side"])}"'))
        out.append(f'<text x="{lx + 18}" y="{y + 4}" font-size="12" fill="{th.text}">{html.escape(T['seasons'][s])}</text>')
    out.append(f'<text x="{W - 30}" y="{H - 24}" font-size="11" text-anchor="end" fill="{th.text}" opacity=".7">'
               f'{say("footer")}</text>')
    out.append("</svg>")
    return "".join(out)


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "assets"
    out_dir.mkdir(exist_ok=True)
    for name, dark in (("garden-light.svg", False), ("garden-dark.svg", True)):
        (out_dir / name).write_text(render(data, dark), encoding="utf-8")
        print("wrote", out_dir / name)


if __name__ == "__main__":
    main()
