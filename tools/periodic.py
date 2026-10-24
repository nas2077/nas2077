"""The periodic table of Nas, drawn smooth: every project is an element.

The table has the shape of the real one, and its four blocks are the four
families of work. The number is the order of release, the two letters are the
project's symbol, the block (and its color) is the kind of work:

    s-block  Products        apps you can download
    d-block  Client work     sites for real clients
    p-block  Experiments     side projects for fun
    f-block  Design & study  systems, identity, notes

Lettering is Barlow (SIL Open Font License, tools/fonts), turned into SVG paths
so GitHub shows it exactly: an SVG used as an image cannot load fonts.

    tile(element, size)    -> one element as a standalone SVG
    table(theme, elements) -> the whole table, animated, for the profile README

Needs fontTools.
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent / "fonts"
WEIGHTS = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
INK = "#1B2632"

# key: (name, singular, block, color, what it holds)
FAMILIES = {
    "product": ("Products", "Product", "s", "FFB162", "Apps you can download."),
    "client": ("Client work", "Client work", "d", "8FB8E8", "Sites for real clients."),
    "experiment": ("Experiments", "Experiment", "p", "7FC8A9", "Side projects for fun."),
    "design": ("Design & study", "Design", "f", "C59BE0", "Systems, identity, notes."),
}
THEMES = {
    "dark": {"bg": "#1B2632", "text": "#EEE9DF", "soft": "#C9C1B1", "rule": "rgba(238,233,223,0.12)",
             "empty": "rgba(238,233,223,0.02)", "edge": 0.30, "tint": 0.16, "deep": 1.0},
    "light": {"bg": "#EEE9DF", "text": "#1B2632", "soft": "#2C3B4D", "rule": "rgba(27,38,50,0.14)",
              "empty": "rgba(255,255,255,0.35)", "edge": 0.45, "tint": 0.26, "deep": 0.72},
}
STILL = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
_fonts = {}
_used = set()


# ------------------------------------------------------------------ lettering


def _font(weight):
    if weight not in _fonts:
        font = TTFont(FONTS / f"Barlow-{WEIGHTS[weight]}.ttf")
        _fonts[weight] = (font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm)
    return _fonts[weight]


def width(text, size, weight=400):
    glyphs, cmap, upem = _font(weight)
    return sum(glyphs[cmap[ord(c)]].width for c in text) * size / upem


def text(value, x, y, size, weight=400, anchor="start", **attrs):
    """value as glyph outlines; x, y is the baseline point, anchor start, middle or end.
    Each glyph is drawn once in <defs> (see _defs) and placed with <use>."""
    glyphs, cmap, upem = _font(weight)
    if anchor == "middle":
        x -= width(value, size, weight) / 2
    elif anchor == "end":
        x -= width(value, size, weight)
    uses, cursor = [], 0
    for c in value:
        name = cmap[ord(c)]
        if c != " ":
            _used.add((weight, name))
            uses.append(f'<use href="#{_glyph_id(weight, name)}" x="{cursor}"/>')
        cursor += glyphs[name].width
    scale = size / upem
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f} {-scale:.5f})"{extra}>'
            f'{"".join(uses)}</g>')


def _glyph_id(weight, name):
    return f"g{weight}-{''.join(c if c.isalnum() else '_' for c in name)}"


def _defs():
    """the outlines of every glyph used since the last call, in font units"""
    out = []
    for weight, name in sorted(_used):
        glyphs = _font(weight)[0]
        pen = SVGPathPen(glyphs, ntos=lambda v: str(round(v)))
        glyphs[name].draw(pen)
        out.append(f'<path id="{_glyph_id(weight, name)}" d="{pen.getCommands()}"/>')
    _used.clear()
    return f'<defs>{"".join(out)}</defs>'


def _rgba(color, alpha, deep=1.0):
    r, g, b = (round(int(color[i:i + 2], 16) * deep) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ------------------------------------------------------------------ one element


def _element(e, x, y, size, detail=False):
    """the filled square: number, symbol, and with detail the family and name"""
    family = FAMILIES[e["family"]]
    fill = f"#{family[3]}"
    parts = [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * 0.085:.1f}" fill="{fill}"/>']
    if detail:
        pad = size * 0.085
        parts.append(text(f'{e["number"]:02d}', x + pad, y + pad + 9, 11, 700, fill=INK))
        parts.append(text(family[1], x + size - pad, y + pad + 9, 11, 600, "end", fill=INK))
        parts.append(text(e["symbol"], x + size / 2, y + size * 0.62, size * 0.44, 700, "middle", fill=INK))
        parts.append(text(e["name"], x + size / 2, y + size * 0.80, 12.5, 600, "middle", fill=INK))
        if e.get("platforms"):
            parts.append(text(e["platforms"], x + size / 2, y + size * 0.91, 10.5, 500, "middle", fill=INK))
    else:
        parts.append(text(f'{e["number"]:02d}', x + size * 0.1, y + size * 0.24, size * 0.17, 700, fill=INK))
        parts.append(text(e["symbol"], x + size / 2, y + size * 0.71, size * 0.44, 700, "middle", fill=INK))
    return "".join(parts)


def tile(e, size=96):
    """a standalone SVG of one element, the same in both themes"""
    label = f'{e["number"]:02d} {e["symbol"]}: {e["name"]}'
    body = _element(e, 0, 0, 96)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="{size}" height="{size}" '
            f'role="img" aria-label="{label}"><title>{label}</title>{_defs()}{body}</svg>\n')


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


def table(theme, elements):
    t = THEMES[theme]
    places = _places(elements)
    latest = max(elements, key=lambda e: e["number"])
    blocks = {f[2]: f[3] for f in FAMILIES.values()}
    css = [f".cell{{stroke-width:1;fill:{t['empty']};animation:8s ease-in-out infinite}}",
           ".glow{animation:glow 3.2s ease-in-out infinite}@keyframes glow{0%,100%{opacity:.12}50%{opacity:.7}}"]
    for block, color in blocks.items():
        css.append(f".b{block}{{stroke:{_rgba(color, t['edge'], t['deep'])};animation-name:w{block}}}"
                   f"@keyframes w{block}{{0%,30%,100%{{fill:{t['empty']}}}15%{{fill:{_rgba(color, t['tint'])}}}}}")

    out = [text("The periodic table of Nas.", PAD, 74, 36, 700, fill=t["text"]),
           text("Every project is an element. The number is the order it shipped, the block is the kind of work.",
                PAD, 102, 15, 500, fill=t["soft"])]
    right = W - PAD
    for value, label in ((min(e.get("year", 9999) for e in elements), "since"), (len(FAMILIES), "families"),
                         (len(elements), "shipped")):
        out.append(text(str(value), right, 72, 22, 600, "end", fill=t["text"]))
        out.append(text(label, right, 90, 11, 400, "end", fill=t["soft"]))
        right -= max(width(str(value), 22, 600), width(label, 11)) + 28

    for col, row, block in _cells():
        x, y = _x(col), _y(row)
        e = places.get((col, row))
        if e is None:
            delay = (col + row) * 0.16
            out.append(f'<rect class="cell b{block}" x="{x + .5:.2f}" y="{y + .5}" width="{COL - 1:.2f}" '
                       f'height="{CELL - 1}" rx="6" style="animation-delay:{delay:.2f}s"/>')
            continue
        if e is latest:
            out.append(f'<rect class="glow" x="{x - 3:.2f}" y="{y - 3}" width="{COL + 6:.2f}" height="{CELL + 6}" '
                       f'rx="8" fill="none" stroke="#{FAMILIES[e["family"]][3]}" stroke-width="3"/>')
        fill = f'#{FAMILIES[e["family"]][3]}'
        out.append(f'<rect x="{x:.2f}" y="{y}" width="{COL:.2f}" height="{CELL}" rx="6" fill="{fill}"/>')
        out.append(text(f'{e["number"]:02d}', x + 4, y + 10, 7.5, 700, fill=INK))
        out.append(text(e["symbol"], x + COL / 2, y + 31, 19, 700, "middle", fill=INK))

    # the empty space at the top of the real table: the latest element up close, and the families
    size = 3 * CELL + 2 * GAP
    ix, iy = _x(3) + 12, _y(1)
    out.append(_element(latest, ix, iy, size, detail=True))
    x0, x1 = ix + size + 22, _x(13) - 14
    colw = (x1 - x0 - 18) / 2
    for i, (name, _, block, color, about) in enumerate(FAMILIES.values()):
        x, y = x0 + (i % 2) * (colw + 18), iy + 6 + (i // 2) * 72
        out.append(f'<line x1="{x:.2f}" y1="{y}" x2="{x + colw:.2f}" y2="{y}" stroke="{t["rule"]}"/>')
        out.append(f'<rect x="{x:.2f}" y="{y + 12}" width="9" height="9" rx="2" fill="#{color}"/>')
        out.append(text(name, x + 15, y + 21, 13, 600, fill=t["text"]))
        out.append(text(f"{block}-block", x + colw, y + 21, 10.5, 500, "end", fill=t["soft"]))
        out.append(text(about, x, y + 40, 11.5, 400, fill=t["soft"]))

    out.append(f'<line x1="{PAD}" y1="602" x2="{W - PAD}" y2="602" stroke="{t["rule"]}"/>')
    out.append(text("Empty cells are projects still in the lab.", PAD, 626, 12.5, 400, fill=t["soft"]))
    out.append(text("Planets run out. Elements don't.", W - PAD, 626, 12.5, 400, "end", fill=t["soft"]))

    shipped = ", ".join(f'{e["number"]:02d} {e["name"]}' for e in sorted(elements, key=lambda e: e["number"]))
    label = (f"The periodic table of Nas. Its four blocks are the families of work: products, client work, "
             f"experiments, design and study. Shipped: {shipped}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{label}"><title>The periodic table of Nas</title><style>{"".join(css)}{STILL}</style>'
            f'{_defs()}<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>{"".join(out)}</svg>\n')
