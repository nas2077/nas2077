"""The periodic table of Nas, drawn in pixels like the header: every project is an element.

The table has the shape of the real one, and its four blocks are the four
families of work. The number is the order of release, the two letters are the
project's symbol, the block (and its color) is the kind of work:

    s-block  Products        apps you can download
    d-block  Client work     sites for real clients
    p-block  Experiments     side projects for fun
    f-block  Design & study  systems, identity, notes

It uses the same pieces as the header (tools/build_profile.py): the Nas 5 x 7
pixel letters and 3 x 5 digits from tools/element.py, the system monospace
font for running text, square pixel corners, and twinkling stars in the empty
parts of the table. Everything sits on a 2 px grid.

    tile(element)          -> one element as a standalone pixel SVG
    table(theme, elements) -> the whole table, animated, for the profile README
"""
import random

from element import DIGITS, LETTERS

INK = "#1B2632"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
EXTRA = {",": "..... ..... ..... ..... ..##. ..##. .##..", "'": "..#.. ..#.. .#... ..... ..... ..... .....",
         " ": "..... ..... ..... ..... ..... ..... .....", ".": "..... ..... ..... ..... ..... ..##. ..##.",
         "p": "..... ..... ####. #...# #...# ####. #...."}   # a taller bowl reads better at title size

# key: (name, singular, block, color, what it holds)
FAMILIES = {
    "product": ("products", "product", "s", "FFB162", "apps you can download."),
    "client": ("client work", "client", "d", "8FB8E8", "sites for real clients."),
    "experiment": ("experiments", "experiment", "p", "7FC8A9", "side projects for fun."),
    "design": ("design & study", "design", "f", "C59BE0", "systems, identity, notes."),
}
THEMES = {
    "dark": {"bg": "#1B2632", "text": "#EEE9DF", "soft": "#C9C1B1", "star": "#EEE9DF", "accent": "#FFB162",
             "rule": "rgba(238,233,223,0.14)", "empty": "rgba(238,233,223,0.03)",
             "edge": 0.34, "tint": 0.20, "deep": 1.0},
    "light": {"bg": "#EEE9DF", "text": "#1B2632", "soft": "#2C3B4D", "star": "#A35139", "accent": "#A35139",
              "rule": "rgba(27,38,50,0.16)", "empty": "rgba(255,255,255,0.40)",
              "edge": 0.55, "tint": 0.30, "deep": 0.72},
}
STILL = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# ------------------------------------------------------------------ pixels


def _runs(glyph, x, y, scale, width):
    """a glyph ('#' and '.', rows split by spaces) as merged horizontal runs"""
    out = []
    for gy, row in enumerate(glyph.split()):
        gx = 0
        while gx < width:
            if row[gx] == "#":
                end = gx
                while end < width and row[end] == "#":
                    end += 1
                out.append(f"M{x + gx * scale} {y + gy * scale}h{(end - gx) * scale}v{scale}h{-(end - gx) * scale}z")
                gx = end
            else:
                gx += 1
    return out


def pixel_text(value, x, y, scale, fill, **attrs):
    """value in the Nas 5 x 7 letters, top-left at x, y; returns (svg, right edge)"""
    d, cursor = [], x
    for ch in value:
        d += _runs(EXTRA.get(ch) or LETTERS[ch], cursor, y, scale, 5)
        cursor += 6 * scale
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<path d="{"".join(d)}" fill="{fill}"{extra}/>', cursor - scale


def pixel_digits(value, x, y, scale, fill):
    """value in the Nas 3 x 5 digits, top-left at x, y"""
    d = []
    for i, ch in enumerate(value):
        d += _runs(DIGITS[ch], x + i * 4 * scale, y, scale, 3)
    return f'<path d="{"".join(d)}" fill="{fill}"/>'


def digits_width(value, scale):
    return (len(value) * 4 - 1) * scale


def letters_width(value, scale):
    return (len(value) * 6 - 1) * scale


def notched(x, y, w, h, n=2):
    """a square with its corner pixels taken off, the pixel way of rounding"""
    return f"M{x + n} {y}h{w - 2 * n}v{n}h{n}v{h - 2 * n}h{-n}v{n}h{-(w - 2 * n)}v{-n}h{-n}v{-(h - 2 * n)}h{n}z"


def frame(x, y, w, h, t=2):
    """a t px outline with open corners, as one path"""
    return (f"M{x + t} {y}h{w - 2 * t}v{t}h{-(w - 2 * t)}z"
            f"M{x + t} {y + h - t}h{w - 2 * t}v{t}h{-(w - 2 * t)}z"
            f"M{x} {y + t}h{t}v{h - 2 * t}h{-t}z"
            f"M{x + w - t} {y + t}h{t}v{h - 2 * t}h{-t}z")


def mono(value, x, y, size, fill, weight=400, anchor="start", cls=None):
    value = value.replace("&", "&amp;")
    extra = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{value}</text>')


def _rgba(color, alpha, deep=1.0):
    r, g, b = (round(int(color[i:i + 2], 16) * deep) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ------------------------------------------------------------------ one element


def _cell(e, x, y, size):
    """an element in the table: number in the corner, symbol in the middle"""
    fill = f'#{FAMILIES[e["family"]][3]}'
    sx = x + (size - letters_width(e["symbol"], 2)) // 2
    symbol, _ = pixel_text(e["symbol"], sx, y + 24, 2, INK)
    return (f'<path d="{notched(x, y, size, size)}" fill="{fill}"/>'
            + pixel_digits(f'{e["number"]:02d}', x + 4, y + 4, 2, INK) + symbol)


def _card(e, x, y, size):
    """the latest element up close: number, family, a big symbol, name and platforms"""
    family = FAMILIES[e["family"]]
    sx = x + (size - letters_width(e["symbol"], 7)) // 2
    symbol, _ = pixel_text(e["symbol"], sx, y + 36, 7, INK)
    parts = [f'<path d="{notched(x, y, size, size, 4)}" fill="#{family[3]}"/>',
             pixel_digits(f'{e["number"]:02d}', x + 8, y + 8, 3, INK),
             mono(family[1], x + size - 8, y + 19, 11, INK, 700, "end"),
             symbol,
             mono(e["name"], x + size / 2, y + 112, 12, INK, 700, "middle")]
    if e.get("platforms"):
        parts.append(mono(e["platforms"], x + size / 2, y + 130, 9.5, INK, 400, "middle"))
    return "".join(parts)


def tile(e, size=96):
    """a standalone pixel SVG of one element on a 24 x 24 grid, the same in both themes"""
    label = f'{e["number"]:02d} {e["symbol"]}: {e["name"]}'
    symbol, _ = pixel_text(e["symbol"], (24 - letters_width(e["symbol"], 1)) // 2, 12, 1, INK)
    body = (f'<path d="{notched(0, 0, 24, 24, 1)}" fill="#{FAMILIES[e["family"]][3]}"/>'
            + pixel_digits(f'{e["number"]:02d}', 2, 2, 1, INK) + symbol)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{label}"><title>{label}</title>{body}</svg>\n')


# ------------------------------------------------------------------ the table

W, H = 960, 720
PAD, GAP, CELL, TOP = 32, 4, 46, 176   # 18 * 46 + 17 * 4 = 896 = W - 2 * PAD


def _x(col):
    return PAD + (col - 1) * (CELL + GAP)


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


def _stars(t, taken):
    """the header's twinkling stars, only where nothing else is drawn"""
    rng = random.Random(77)
    out = []
    for _ in range(400):
        sx, sy = rng.randrange(6, W - 10) // 2 * 2, rng.randrange(6, H - 10) // 2 * 2
        size = rng.choice((2, 2, 2, 4))
        if any(x0 - 8 < sx + size and sx < x1 + 8 and y0 - 8 < sy + size and sy < y1 + 8
               for x0, y0, x1, y1 in taken):
            continue
        taken.append((sx, sy, sx + size, sy + size))
        out.append(f'<rect class="star" x="{sx}" y="{sy}" width="{size}" height="{size}" '
                   f'style="animation-duration:{rng.uniform(2.2, 5.5):.1f}s;animation-delay:-{rng.uniform(0, 5):.1f}s"/>')
        if len(out) == 38:
            break
    return "".join(out)


def table(theme, elements):
    t = THEMES[theme]
    places = _places(elements)
    latest = max(elements, key=lambda e: e["number"])
    blocks = {f[2]: f[3] for f in FAMILIES.values()}
    css = [f".star{{fill:{t['star']};animation:twinkle 4s ease-in-out infinite}}"
           "@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.9}}",
           f".cell{{fill:{t['empty']};animation:8s steps(4,end) infinite}}",
           ".blink{animation:blink 1.6s steps(1,end) infinite}@keyframes blink{0%{opacity:1}50%{opacity:0}}",
           f".shoot{{stroke:{t['accent']};stroke-width:3;stroke-linecap:square;opacity:0;animation:shoot 13s linear infinite}}"
           "@keyframes shoot{0%,82%{opacity:0;transform:translate(0,0)}84%{opacity:1}92%{opacity:0;transform:translate(-200px,90px)}100%{opacity:0}}"]
    for block, color in blocks.items():
        css.append(f".e{block}{{fill:{_rgba(color, t['edge'], t['deep'])}}}"
                   f".b{block}{{animation-name:w{block}}}"
                   f"@keyframes w{block}{{0%,30%,100%{{fill:{t['empty']}}}15%{{fill:{_rgba(color, t['tint'])}}}}}")

    # the title, set like "hi, i'm Nas." in the header
    words, end = pixel_text("the periodic table of ", 40, 40, 5, t["text"])
    nas, end = pixel_text("Nas", end + 5, 40, 5, t["accent"])
    dot, end = pixel_text(".", end, 40, 5, t["text"])
    years = min(e.get("year", 9999) for e in elements)
    out = [f'<g shape-rendering="crispEdges">{words}{nas}{dot}</g>',
           mono("every project is an element. the number is the order it shipped.", 42, 112, 17, t["text"], 600),
           mono(f"{len(elements)} shipped · {len(FAMILIES)} families · since {years} · the block is the kind of work",
                42, 140, 14, t["soft"])]
    taken = [(36, 36, end, 80), (40, 94, 740, 146)]

    pixels = []
    for col, row, block in _cells():
        x, y = _x(col), _y(row)
        taken.append((x, y, x + CELL, y + CELL))
        e = places.get((col, row))
        if e is None:
            delay = (col + row) * 0.16
            pixels.append(f'<rect class="cell b{block}" x="{x + 2}" y="{y + 2}" width="{CELL - 4}" '
                          f'height="{CELL - 4}" style="animation-delay:{delay:.2f}s"/>'
                          f'<path class="e{block}" d="{frame(x, y, CELL, CELL)}"/>')
            continue
        if e is latest:
            pixels.append(f'<path class="blink" fill="#{FAMILIES[e["family"]][3]}" '
                          f'd="{frame(x - 4, y - 4, CELL + 8, CELL + 8)}"/>')
        pixels.append(_cell(e, x, y, CELL))

    # the empty space at the top of the real table: the latest element up close, and the families
    size = 3 * CELL + 2 * GAP
    ix, iy = _x(3) + 14, _y(1)
    pixels.append(_card(latest, ix, iy, size))
    x0, x1 = ix + size + 22, _x(13) - 16
    taken.append((ix, iy, x1, iy + size))
    for i, (name, _, block, color, about) in enumerate(FAMILIES.values()):
        y = iy + i * 37
        pixels.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="2" fill="{t["rule"]}"/>')
        pixels.append(f'<path d="{notched(x0, y + 8, 10, 10)}" fill="#{color}"/>')
        out.append(mono(name, x0 + 18, y + 18, 13, t["text"], 700))
        out.append(mono(f"{block}-block", x1, y + 18, 11, t["soft"], 400, "end"))
        out.append(mono(about, x0 + 18, y + 32, 11, t["soft"]))

    rule = _y(10) + CELL + 18
    pixels.append(f'<rect x="{PAD}" y="{rule}" width="{W - 2 * PAD}" height="2" fill="{t["rule"]}"/>')
    out.append(mono("empty cells are projects still in the lab.", PAD, rule + 26, 13, t["soft"]))
    out.append(mono("planets run out. elements don't.", W - PAD, rule + 26, 13, t["soft"], 400, "end"))
    taken.append((PAD, rule, W - PAD, H))

    shipped = ", ".join(f'{e["number"]:02d} {e["name"]}' for e in sorted(elements, key=lambda e: e["number"]))
    label = (f"The periodic table of Nas. Its four blocks are the families of work: products, client work, "
             f"experiments, design and study. Shipped: {shipped}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{label}"><title>The periodic table of Nas</title><style>{"".join(css)}{STILL}</style>'
            f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>{_stars(t, taken)}'
            f'<line class="shoot" x1="900" y1="20" x2="940" y2="2"/>'
            f'<g shape-rendering="crispEdges">{"".join(pixels)}</g>{"".join(out)}</svg>\n')
