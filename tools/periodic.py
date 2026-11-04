"""The periodic table of Nas, drawn with the Nas design system: every project is an element.

The table has the shape of the real one, and its four blocks are the four
families of work. The number is the order of release, the two letters are the
project's symbol, the block is the kind of work:

    s-block  Products        apps you can download
    d-block  Client work     sites for real clients
    p-block  Experiments     side projects for fun
    f-block  Design & study  systems, identity, notes

The design system allows six colors, so a family is told by its place in the
table, never by a hue of its own. Surfaces follow the system too: empty cells
are recessed like fields, elements are raised like buttons, the newest element
is rust (the primary action: the table links to it), and orange appears only in
pixel art (the loading bar and Orbi).

Lettering is Inter (SIL Open Font License, tools/fonts), turned into SVG paths
so GitHub shows it exactly: an SVG used as an image cannot load fonts.

    tile(element, size)    -> one element as a standalone SVG
    table(theme, elements) -> the whole table for the profile README

Needs fontTools.
"""
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

TOOLS = Path(__file__).resolve().parent
WEIGHTS = {400: "Regular", 500: "Medium", 600: "SemiBold"}

# the six colors of the Nas design system
INK, SLATE, CREAM, SAND, RUST, ORANGE = "#1B2632", "#2C3B4D", "#EEE9DF", "#C9C1B1", "#A35139", "#FFB162"
RUST_EDGE = "#6E3424"

# key: (name, singular, block, what it holds)
FAMILIES = {
    "product": ("Products", "Product", "s", "Apps you can download."),
    "client": ("Client work", "Client work", "d", "Sites for real clients."),
    "experiment": ("Experiments", "Experiment", "p", "Side projects for fun."),
    "design": ("Design & study", "Design", "f", "Systems, identity, notes."),
}
# semantic roles, as in tokens.json
THEMES = {
    "dark": {"background": INK, "raised": SLATE, "edge": "#111922", "text": CREAM, "soft": SAND,
             "drop": "#000000", "drop_alpha": 0.35, "inset": "#000000", "inset_alpha": 0.45,
             "light": CREAM, "light_alpha": 0.05, "rule": SLATE},
    "light": {"background": CREAM, "raised": SAND, "edge": "#A39B8B", "text": INK, "soft": SLATE,
              "drop": INK, "drop_alpha": 0.12, "inset": INK, "inset_alpha": 0.22,
              "light": "#FFFFFF", "light_alpha": 0.7, "rule": SAND},
}
RADIUS, RADIUS_CARD = 10, 16
STILL = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
_fonts = {}
_used = set()


# ------------------------------------------------------------------ lettering


def _font(weight):
    if weight not in _fonts:
        font = TTFont(TOOLS / "fonts" / f"Inter-{WEIGHTS[weight]}.ttf")
        _fonts[weight] = (font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm)
    return _fonts[weight]


def width(text, size, weight=400, tracking=0.0):
    glyphs, cmap, upem = _font(weight)
    return sum(glyphs[cmap[ord(c)]].width for c in text) * size / upem + tracking * size * (len(text) - 1)


def text(value, x, y, size, weight=400, anchor="start", tracking=0.0, **attrs):
    """value as glyph outlines; x, y is the baseline point, anchor start, middle or end;
    tracking is letter spacing in em, as in the design system (-0.025em for titles).
    Each glyph is drawn once in <defs> (see _defs) and placed with <use>."""
    glyphs, cmap, upem = _font(weight)
    if anchor == "middle":
        x -= width(value, size, weight, tracking) / 2
    elif anchor == "end":
        x -= width(value, size, weight, tracking)
    uses, cursor, step = [], 0, tracking * upem
    for c in value:
        name = cmap[ord(c)]
        if c != " ":
            _used.add((weight, name))
            uses.append(f'<use href="#{_glyph_id(weight, name)}" x="{cursor:.0f}"/>')
        cursor += glyphs[name].width + step
    scale = size / upem
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f} {-scale:.5f})"{extra}>'
            f'{"".join(uses)}</g>')


def _glyph_id(weight, name):
    return f"g{weight}-{''.join(c if c.isalnum() else '_' for c in name)}"


def _glyphs():
    """the outlines of every glyph used since the last call, in font units"""
    out = []
    for weight, name in sorted(_used):
        glyphs = _font(weight)[0]
        pen = SVGPathPen(glyphs, ntos=lambda v: str(round(v)))
        glyphs[name].draw(pen)
        out.append(f'<path id="{_glyph_id(weight, name)}" d="{pen.getCommands()}"/>')
    _used.clear()
    return "".join(out)


# ------------------------------------------------------------------ surfaces


def _filters(t):
    """recessed (shadow-inset) and raised (the soft half of shadow-button / shadow-card)"""
    def inner(dx, dy, color, alpha, out):
        return (f'<feComponentTransfer in="SourceAlpha"><feFuncA type="table" tableValues="1 0"/></feComponentTransfer>'
                f'<feGaussianBlur stdDeviation="2.5"/><feOffset dx="{dx}" dy="{dy}" result="{out}-blur"/>'
                f'<feFlood flood-color="{color}" flood-opacity="{alpha}"/><feComposite operator="in" in2="{out}-blur"/>'
                f'<feComposite operator="in" in2="SourceAlpha" result="{out}"/>')
    inset = (f'<filter id="inset" x="0" y="0" width="100%" height="100%">'
             + inner(2, 2, t["inset"], t["inset_alpha"], "dark")
             + inner(-2, -2, t["light"], t["light_alpha"], "lit")
             + '<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="dark"/><feMergeNode in="lit"/></feMerge></filter>')
    lift = (f'<filter id="lift" x="-30%" y="-30%" width="160%" height="180%">'
            f'<feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="{t["drop"]}" flood-opacity="{t["drop_alpha"]}"/></filter>')
    return inset + lift


def _raised(x, y, w, h, r, face, edge, lift=True):
    """a raised surface: the hard 3px edge under the face, as in shadow-button"""
    group = ' filter="url(#lift)"' if lift else ""
    return (f'<g{group}><rect x="{x:.2f}" y="{y + 3:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{edge}"/>'
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{face}"/></g>')


def _pill(label, x, y, t, anchor="start"):
    """the recessed n-label, small; x, y is its top corner"""
    w = width(label, 10.5, 500) + 16
    if anchor == "end":
        x -= w
    return (f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="20" rx="10" fill="{t["background"]}" filter="url(#inset)"/>'
            + text(label, x + 8, y + 14, 10.5, 500, fill=t["soft"]))


def _orbi(x, y, scale, theme):
    """mini Orbi, 16 px artwork at a whole-number scale, colored for the theme"""
    svg = (TOOLS / "orbi-16.svg").read_text(encoding="utf-8")
    fills = dict(re.findall(r"\.(c\w)\{fill:(#\w+)\}", svg.split("@media")[0]))
    if theme == "light":
        fills.update(re.findall(r"\.(c\w)\{fill:(#\w+)\}", svg.split("@media")[1]))
    paths = "".join(f'<path fill="{fills[c]}" d="{d}"/>' for c, d in re.findall(r'<path class="(c\w)" d="([^"]+)"', svg))
    return f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges">{paths}</g>'


# ------------------------------------------------------------------ one element


def _element(e, x, y, size, t, latest):
    """a small element: the number in the corner, the symbol in the middle"""
    face, edge, ink = (RUST, RUST_EDGE, CREAM) if latest else (t["raised"], t["edge"], t["text"])
    return (_raised(x, y, size[0], size[1], RADIUS, face, edge)
            + text(f'{e["number"]:02d}', x + 6, y + 12, 8, 600, fill=ink, opacity=".85")
            + text(e["symbol"], x + size[0] / 2, y + size[1] * 0.72, size[1] * 0.42, 600, "middle", -0.025, fill=ink))


def tile(e, size=96):
    """a standalone SVG of one element, the same in both themes: the rust raised square"""
    label = f'{e["number"]:02d} {e["symbol"]}: {e["name"]}'
    body = (f'<rect x="4" y="7" width="88" height="85" rx="{RADIUS_CARD}" fill="{RUST_EDGE}"/>'
            f'<rect x="4" y="4" width="88" height="85" rx="{RADIUS_CARD}" fill="{RUST}"/>'
            + text(f'{e["number"]:02d}', 14, 22, 13, 600, fill=CREAM, opacity=".85")
            + text(e["symbol"], 48, 70, 40, 600, "middle", -0.025, fill=CREAM))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="{size}" height="{size}" '
            f'role="img" aria-label="{label}"><title>{label}</title><defs>{_glyphs()}</defs>{body}</svg>\n')


def _feature(e, x, y, size, t):
    """the newest element up close, as a raised card"""
    family = FAMILIES[e["family"]]
    pad = 14
    parts = [_raised(x, y, size, size, RADIUS_CARD, t["raised"], t["edge"]),
             text(f'{e["number"]:02d}', x + pad, y + pad + 12, 12, 600, fill=t["soft"]),
             _pill(family[1], x + size - pad + 4, y + pad - 2, {**t, "background": t["raised"]}, "end"),
             text(e["symbol"], x + size / 2, y + size * 0.62, size * 0.40, 600, "middle", -0.045, fill=t["text"]),
             text(e["name"], x + size / 2, y + size * 0.80, 12.5, 600, "middle", -0.01, fill=t["text"])]
    if e.get("platforms"):
        parts.append(text(e["platforms"], x + size / 2, y + size * 0.91, 10, 400, "middle", fill=t["soft"]))
    return "".join(parts)


# ------------------------------------------------------------------ the table

W, H = 960, 656
PAD, GAP, CELL, TOP = 40, 5, 44, 128
COL = (W - 2 * PAD - 17 * GAP) / 18


def _x(col):
    return PAD + (col - 1) * (COL + GAP)


def _y(row):
    if row <= 7:
        return TOP + (row - 1) * (CELL + GAP)
    return TOP + 7 * (CELL + GAP) + 14 + (row - 9) * (CELL + GAP)


def _cells():
    """every cell of the real table as (col, row, block); rows 9 and 10 are the f-block"""
    cells = [(18, 1, "p")]
    for row in (2, 3):
        cells += [(col, row, "s") for col in (1, 2)] + [(col, row, "p") for col in range(13, 19)]
    for row in range(4, 8):
        for col in range(1, 19):
            block = "s" if col <= 2 else "p" if col >= 13 else "f" if (col == 3 and row >= 6) else "d"
            cells.append((col, row, block))
    for row in (9, 10):
        cells += [(col, row, "f") for col in range(4, 19)]
    return [(1, 1, "s")] + cells


def _places(elements):
    """each element takes the next free cell of its block, in reading order"""
    free = {}
    for col, row, block in sorted(_cells(), key=lambda c: (c[1], c[0])):
        if not (col == 3 and row >= 6):            # the lanthanide marker holds nothing
            free.setdefault(block, []).append((col, row))
    places = {}
    for e in sorted(elements, key=lambda e: e["number"]):
        places[(free[FAMILIES[e["family"]][2]].pop(0))] = e
    return places


def _map(block, x, y, t):
    """the table in miniature, with one block drawn in text color: the family's key"""
    out = []
    for col, row, b in _cells():
        cy = y + (row - 1) * 3 + (2 if row >= 9 else 0)
        out.append(f'<rect x="{x + (col - 1) * 3}" y="{cy}" width="3" height="3" '
                   f'fill="{t["soft"] if b == block else t["raised"]}"/>')
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def _loading(x, y):
    """the n-loading bar in pixels: the lab is working"""
    css = ".px{fill:" + ORANGE + ";opacity:0;animation:3.6s steps(1,end) infinite}"
    cells = "".join(f'<rect class="px" x="{x + 4 + i * 7}" y="{y + 4}" width="6" height="6" '
                    f'style="animation-name:lab{i}"/>' for i in range(4))
    frames = "".join(f"@keyframes lab{i}{{0%,{i * 20 + 1}%{{opacity:0}}{i * 20 + 2}%,90%{{opacity:1}}91%,100%{{opacity:0}}}}"
                     for i in range(4))
    still = "@media (prefers-reduced-motion: reduce){.px{opacity:1}.px:last-child{opacity:0}}"
    return css + frames + still, cells


def table(theme, elements):
    t = THEMES[theme]
    places = _places(elements)
    latest = max(elements, key=lambda e: e["number"])

    out = [text("The periodic table of Nas.", PAD, 74, 34, 600, tracking=-0.025, fill=t["text"]),
           text("Every project is an element. The number is the order it shipped, the block is the kind of work.",
                PAD, 102, 14, 400, fill=t["soft"])]
    right = W - PAD
    for value, label in ((min(e.get("year", 9999) for e in elements), "since"), (len(FAMILIES), "families"),
                         (len(elements), "shipped")):
        out.append(text(str(value), right, 72, 22, 600, "end", -0.025, fill=t["text"]))
        out.append(text(label, right, 90, 11, 400, "end", fill=t["soft"]))
        right -= max(width(str(value), 22, 600, -0.025), width(label, 11)) + 28

    # empty cells are recessed, like a field waiting for input; one filter for all of them
    empty, filled = [], []
    for col, row, block in _cells():
        x, y = _x(col), _y(row)
        e = places.get((col, row))
        if e is None:
            empty.append(f'<rect x="{x:.2f}" y="{y}" width="{COL:.2f}" height="{CELL}" rx="{RADIUS}"/>')
        else:
            filled.append(_element(e, x, y, (COL, CELL), t, e is latest))
    out.append(f'<g fill="{t["background"]}" filter="url(#inset)">{"".join(empty)}</g>')
    out += filled

    # the empty space at the top of the real table: the newest element up close, and the families
    size = 3 * CELL + 2 * GAP
    ix, iy = _x(3) + 12, _y(1)
    out.append(_feature(latest, ix, iy, size, t))
    x0, x1 = ix + size + 26, _x(13) - 18
    for i, (name, _, block, about) in enumerate(FAMILIES.values()):
        y = iy + 2 + i * 37
        out.append(_map(block, x0, y + 3, t))
        out.append(text(name, x0 + 68, y + 13, 13, 600, tracking=-0.01, fill=t["text"]))
        out.append(text(f"{block}-block", x1, y + 13, 10.5, 500, "end", fill=t["soft"]))
        out.append(text(about, x0 + 68, y + 30, 11.5, 400, fill=t["soft"]))

    loading_css, loading = _loading(PAD, 612)
    out.append(f'<line x1="{PAD}" y1="598.5" x2="{W - PAD}" y2="598.5" stroke="{t["rule"]}"/>')
    out.append(f'<rect x="{PAD}" y="612" width="36" height="14" rx="5" fill="{t["background"]}" filter="url(#inset)"/>')
    out.append(f'<g shape-rendering="crispEdges">{loading}</g>')
    out.append(text("Empty cells are projects still in the lab.", PAD + 48, 623, 12.5, 400, fill=t["soft"]))
    out.append(text("Planets run out. Elements don't.", W - PAD - 42, 623, 12.5, 400, "end", fill=t["soft"]))
    out.append(_orbi(W - PAD - 32, 603, 2, theme))

    shipped = ", ".join(f'{e["number"]:02d} {e["name"]}' for e in sorted(elements, key=lambda e: e["number"]))
    label = (f"The periodic table of Nas. Its four blocks are the families of work: products, client work, "
             f"experiments, design and study. Shipped: {shipped}.")
    body = "".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{label}"><title>The periodic table of Nas</title><style>{loading_css}{STILL}</style>'
            f'<defs>{_filters(t)}{_glyphs()}</defs><rect width="{W}" height="{H}" rx="18" fill="{t["background"]}"/>'
            f'{body}</svg>\n')
