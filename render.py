"""Génère le jardin solarpunk (SVG isométrique animé) à partir de data/contributions.json."""
import json
import math
import os
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
# Géométrie, recalculée par layout() selon le nombre d'années
HW, HH = 14, 7          # demi-largeur / demi-hauteur d'une parcelle
SIDE = 3                  # épaisseur de terre visible
OX, OY = 138, 150         # origine de la grille à l'écran
W, H = 1000, 640
PLANT_K = 1.3             # échelle des plantes par rapport au dessin de base
COLS, ROWS_PER_YEAR = 54, 7
MARGIN, TOP = 50, 150

NORTH = {  # mois -> saison (hémisphère nord)
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}
HEMISPHERE = os.environ.get("GARDEN_HEMISPHERE", "north").strip().lower()
if HEMISPHERE not in ("north", "south"):
    raise SystemExit(f"GARDEN_HEMISPHERE doit valoir north ou south, pas {HEMISPHERE!r}")
# Au sud, les saisons sont celles du nord décalées de six mois.
SEASONS = NORTH if HEMISPHERE == "north" else {m: NORTH[(m + 5) % 12 + 1] for m in NORTH}
SEASON_LABEL = {"spring": "Printemps", "summer": "Été", "autumn": "Automne", "winter": "Hiver", "earth": "À venir"}

# ground, side, canopy, canopy2, accent
PALETTE = {
    "spring": dict(ground="#bfe28f", side="#93b86c", leaf="#8fd16a", leaf2="#6dbb5a", accent="#f6a6c1"),
    "summer": dict(ground="#86d174", side="#5fa551", leaf="#3fae4a", leaf2="#2f9440", accent="#ffd54a"),
    "autumn": dict(ground="#dcc57d", side="#b39c57", leaf="#e8923a", leaf2="#c4552b", accent="#d9482b"),
    "winter": dict(ground="#e9f1f5", side="#bccbd3", leaf="#2f6b4f", leaf2="#25573f", accent="#9ccbe8"),
    "earth": dict(ground="#c9a97a", side="#9c7e56", leaf="#a98a5d", leaf2="#a98a5d", accent="#a98a5d"),  # terre battue, jours à venir
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
    """Adapte la taille des parcelles pour que le parterre tienne dans W."""
    global HW, HH, OX, OY, H, PLANT_K
    rows = n_years * ROWS_PER_YEAR
    HW = min(14, (W - 2 * MARGIN) / (COLS + rows))
    HH = HW / 2
    PLANT_K = HW / 14 * 1.3
    OX, OY = MARGIN + rows * HW, TOP
    H = round(OY + (COLS + rows) * HH + 70)


def grid_pos(iso, years):
    """Colonne = semaine de l'année, ligne = jour de la semaine, un bloc de 7 lignes par année."""
    d = date.fromisoformat(iso)
    jan1 = date(d.year, 1, 1)
    col = ((d - jan1).days + (jan1.weekday() + 1) % 7) // 7
    return col, years.index(d.year) * ROWS_PER_YEAR + (d.weekday() + 1) % 7


def season_of(iso):
    return SEASONS[int(iso[5:7])]


def levels(days):
    """Niveau 0-4 par jour, par quartiles des jours actifs."""
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
    leaf = th.c(p["leaf"] if season != "winter" else "#4f8f6c")
    return (line(x, y, x, y - 5, leaf)
            + f'<ellipse cx="{f(x - 2)}" cy="{f(y - 5)}" rx="2.2" ry="1.2" fill="{leaf}" transform="rotate(-30 {f(x - 2)} {f(y - 5)})"/>'
            + f'<ellipse cx="{f(x + 2)}" cy="{f(y - 5.5)}" rx="2.2" ry="1.2" fill="{leaf}" transform="rotate(30 {f(x + 2)} {f(y - 5.5)})"/>')


def flower(x, y, season, th, rng):
    p = PALETTE[season]
    stem = th.c("#4f9a4a")
    if season == "winter":  # arbuste persistant sous la neige
        return (circle(x, y - 4, 4.2, th.c(p["leaf"]))
                + f'<ellipse cx="{f(x)}" cy="{f(y - 7)}" rx="3.6" ry="1.6" fill="{th.c("#ffffff")}"/>')
    head = {"spring": p["accent"], "summer": rng.choice(["#ffd54a", "#ff8fb1", "#ffffff"]),
            "autumn": rng.choice(["#e8923a", "#d9482b"])}[season]
    return (line(x, y, x, y - 8, stem)
            + circle(x, y - 9, 3.4, th.c(head))
            + circle(x, y - 9, 1.2, th.c("#ffe28a" if season != "summer" else "#c0702a")))


def tree(x, y, count_scale, season, th, rng):
    p = PALETTE[season]
    h = 9 + 5 * count_scale
    trunk = th.c(TRUNK)
    if season == "winter":  # sapin enneigé
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
    if season == "spring":
        for _ in range(4):
            body += circle(x + rng.uniform(-6, 6), cy + rng.uniform(-6, 3), 1.1, th.c(p["accent"]))
    elif season == "summer":
        for _ in range(3):
            body += circle(x + rng.uniform(-5, 5), cy + rng.uniform(-4, 3), 1.1, th.c("#ff6b5e"))
    return body


def turbine(x, y, count_scale, season, th, rng):
    """Éolienne + panneau solaire : le plus haut niveau d'activité."""
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
    # panneau solaire incliné au pied du mât
    px, py = x - 7, y + 1
    pts = f"{f(px - 5)},{f(py)} {f(px + 5)},{f(py - 3)} {f(px + 5)},{f(py + 2)} {f(px - 5)},{f(py + 5)}"
    panel = th.c("#ffffff") if season == "winter" else th.c(PANEL)
    out += f'<polygon points="{pts}" fill="{panel}" stroke="{th.c("#9fb7c9")}" stroke-width=".6"/>'
    out += circle(x + 6, y - 2, 3, th.c(PALETTE[season]["leaf"] if season != "winter" else "#4f8f6c"))
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
    if season == "winter":
        return circle(x + rng.uniform(-4, 4), y + rng.uniform(-1, 1), 0.9, th.c("#ffffff"))
    return line(x, y + 1, x, y - 2.5, th.c(PALETTE[season]["leaf2"]), 1)


def gardener(th):
    """Jardinier au repos, dessiné autour de (0, 0) : il arrose, la lueur du jour est conservée la nuit."""
    def c(color):
        return mix(color, NIGHT, 0.2) if th.dark else color
    skin, shirt, overall, boots = c("#f0c7a0"), c("#fff3d6"), c("#3f7fbf"), c("#5a3b24")
    hat, band, can = c("#e8c36a"), c("#c4552b"), c("#4aa6a0")
    drops = "".join(
        f'<circle cx="13.6" cy="-12" r=".7" fill="#8fd3ff">'
        f'<animate attributeName="cy" values="-12;-1" dur="1s" begin="{b}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;0" dur="1s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for b in (0, 0.33, 0.66))
    return (
        '<ellipse cx="0" cy="1" rx="6.5" ry="2.2" fill="#000" opacity=".2"/>'
        '<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -.7;0 0" dur="1.6s" repeatCount="indefinite"/>'
        f'<rect x="-2.8" y="-7" width="2.3" height="6" fill="{overall}"/><rect x=".5" y="-7" width="2.3" height="6" fill="{overall}"/>'
        f'<rect x="-3" y="-2" width="2.7" height="2" rx=".6" fill="{boots}"/><rect x=".3" y="-2" width="2.7" height="2" rx=".6" fill="{boots}"/>'
        f'<rect x="-3.4" y="-14.5" width="6.8" height="8" rx="1.2" fill="{overall}"/>'
        f'<rect x="-3.4" y="-14.5" width="6.8" height="3" rx="1" fill="{shirt}"/>'
        f'<line x1="-3.4" y1="-13" x2="-5.4" y2="-8" stroke="{shirt}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="-5.5" cy="-7.4" r="1.1" fill="{skin}"/>'
        f'<circle cx="0" cy="-17.8" r="2.8" fill="{skin}"/>'
        f'<ellipse cx="0" cy="-19.4" rx="5.8" ry="1.5" fill="{hat}"/><ellipse cx="0" cy="-20.8" rx="3.1" ry="2.2" fill="{hat}"/>'
        f'<rect x="-3.1" y="-20" width="6.2" height="1" fill="{band}"/>'
        '<g><animateTransform attributeName="transform" type="rotate" values="0 3 -12;9 3 -12;0 3 -12" dur="3s" repeatCount="indefinite"/>'
        f'<line x1="3" y1="-12.5" x2="7" y2="-10.5" stroke="{shirt}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<rect x="5.5" y="-12" width="4.6" height="3.6" rx=".8" fill="{can}"/>'
        f'<path d="M6.2 -12 q2.2 -3.2 4 0" fill="none" stroke="{can}" stroke-width=".9"/>'
        f'<line x1="10" y1="-10" x2="13.2" y2="-12.6" stroke="{can}" stroke-width="1"/>'
        f'<circle cx="13.4" cy="-12.8" r="1" fill="{can}"/>{drops}</g></g>')


MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def today_label(x, y, iso, th):
    text = f"{int(iso[8:])} {MOIS[int(iso[5:7]) - 1]}"
    fill, ink = ("#ffe9a8", "#1b2b3a") if th.dark else ("#ffffff", "#2c4a3a")
    return (f'<g><rect x="{f(x - 21)}" y="{f(y - 11)}" width="42" height="16" rx="8" fill="{fill}" opacity=".92"/>'
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
           f'font-family="ui-sans-serif,system-ui,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<title>Jardin de contributions de {data["login"]}</title><style>{STYLE}</style>', sky(th, rng_sky)]

    cells = []
    for d, level in zip(days, lv):
        col, row = grid_pos(d["date"], years)
        cells.append((col, row, d, level))
    # Les jours pas encore écoulés de l'année en cours : terre battue jusqu'au 31 décembre.
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
        if d["date"] == today:  # la parcelle du jour pulse doucement, le jardinier se tient à côté
            pts = f"{f(cx)},{f(cy - HH)} {f(cx + HW)},{f(cy)} {f(cx)},{f(cy + HH)} {f(cx - HW)},{f(cy)}"
            out.append(f'<polygon points="{pts}" fill="none" stroke="{"#ffe9a8" if dark else "#ffffff"}" stroke-width="1.8">'
                       '<animate attributeName="opacity" values=".2;1;.2" dur="2s" repeatCount="indefinite"/></polygon>')
        if level < 0:  # quelques cailloux sur la terre battue
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
        if d["date"] == today:  # par-dessus la plante : le jardinier est devant la parcelle du jour
            out.append(f'<g transform="translate({f(cx + HW * 0.3)} {f(cy + HH * 0.35)}) scale({PLANT_K * 1.9:.2f})">{gardener(th)}</g>')
            out.append(today_label(cx, cy - 58, d["date"], th))
    for x, y, delay in flies:
        out.append(f'<circle class="fly" cx="{f(x)}" cy="{f(y)}" r="1.3" fill="#fff3a0" style="animation-delay:{delay:.1f}s"/>')

    # en-tête et légende
    out.append(f'<text x="30" y="46" font-size="22" font-weight="700" fill="{th.text}">Le jardin de {data["login"]}</text>')
    out.append(f'<text x="30" y="68" font-size="13" fill="{th.text}" opacity=".8">'
               f'{data["total"]} contributions, de {years[0]} à {years[-1]}</text>')
    for i, y in enumerate(years):  # étiquette d'année le long du bord gauche
        mid = i * ROWS_PER_YEAR + 3
        out.append(f'<text x="{f(OX - mid * HW - 2 * HW)}" y="{f(OY + mid * HH + 4)}" font-size="14" font-weight="700" '
                   f'text-anchor="end" fill="{th.text}" opacity=".85">{y}</text>')
    lx, ly = 30, H - 96
    for i, s in enumerate(["spring", "summer", "autumn", "winter", "earth"]):
        y = ly + i * 18
        out.append(circle(lx + 5, y, 5, th.c(PALETTE[s]["ground"]), f' stroke="{th.c(PALETTE[s]["side"])}"'))
        out.append(f'<text x="{lx + 18}" y="{y + 4}" font-size="12" fill="{th.text}">{SEASON_LABEL[s]}</text>')
    out.append(f'<text x="{W - 30}" y="{H - 24}" font-size="11" text-anchor="end" fill="{th.text}" opacity=".7">'
               f'pousse, fleur, arbre, éolienne : plus on contribue, plus ça grandit</text>')
    out.append("</svg>")
    return "".join(out)


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "assets"
    out_dir.mkdir(exist_ok=True)
    for name, dark in (("garden-light.svg", False), ("garden-dark.svg", True)):
        (out_dir / name).write_text(render(data, dark), encoding="utf-8")
        print("écrit", out_dir / name)


if __name__ == "__main__":
    main()
