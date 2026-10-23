"""Build the animated profile artwork: the header with Orbi and the periodic table.

    python tools/build_profile.py <folder with orbi.json, orbi-scuro.png, orbi-chiaro.png>

Needs Pillow. Writes assets/header-{dark,light}.svg and assets/table-{dark,light}.svg.
Everything is plain SVG with CSS animation, so GitHub shows it as an image;
readers who ask for reduced motion get a still picture.
"""
import base64
import io
import json
import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import element  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ELEMENTS = json.loads((ROOT / "elements.json").read_text(encoding="utf-8"))

THEMES = {
    "dark": {"bg": "#1B2632", "text": "#EEE9DF", "soft": "#C9C1B1", "star": "#EEE9DF",
             "accent": "#FFB162", "panel": "#2C3B4D", "sprite": "orbi-scuro.png"},
    "light": {"bg": "#EEE9DF", "text": "#1B2632", "soft": "#2C3B4D", "star": "#A35139",
              "accent": "#A35139", "panel": "#D9CDB8", "sprite": "orbi-chiaro.png"},
}
STILL = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
EXTRA = {",": "..... ..... ..... ..... ..##. ..##. .##..", "'": "..#.. ..#.. .#... ..... ..... ..... .....",
         " ": "..... ..... ..... ..... ..... ..... .....", "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
         ".": "..... ..... ..... ..... ..... ..##. ..##."}


def pixel_text(text, x, y, scale, fill):
    """the Nas 5 x 7 letters as SVG rects"""
    out, cursor = [], x
    for ch in text:
        glyph = EXTRA.get(ch) or element.LETTERS[ch]
        rows = glyph.split()
        for gy, row in enumerate(rows):
            gx = 0
            while gx < 5:
                if row[gx] == "#":
                    end = gx
                    while end < 5 and row[end] == "#":
                        end += 1
                    out.append(f'<rect x="{cursor + gx * scale}" y="{y + gy * scale}" '
                               f'width="{(end - gx) * scale}" height="{scale}" fill="{fill}"/>')
                    gx = end
                else:
                    gx += 1
        cursor += 6 * scale
    return "".join(out), cursor


# ------------------------------------------------------------------ Orbi


def orbi_sequence(meta):
    """a show reel: Orbi idles, and between idles does his tricks"""
    anims = meta["animazioni"]
    idle = anims["idle"]["fotogrammi"]
    plan = [("idle", 40), ("occhiolino", None), ("idle", 30), ("wow", None), ("idle", 30),
            ("inseguiLuna", None), ("idle", 24), ("felice", None), ("idle", 30), ("bonk", None),
            ("idle", 30), ("sbadiglio", None), ("nanna", None), ("risveglio", None), ("idle", 20)]
    frames, cursor = [], 0
    for name, count in plan:
        if name == "idle":
            for _ in range(count):
                frames.append(idle[cursor % len(idle)])
                cursor += 1
        else:
            frames += anims[name]["fotogrammi"]
    return frames, anims["idle"]["ms"]


def orbi_sheet(sprite_dir, sprite, frames, meta):
    """only the frames the reel uses, 16 per row, as an embedded PNG"""
    w, h = meta["meta"]["fotogramma"]["w"], meta["meta"]["fotogramma"]["h"]
    unique = sorted(set(frames))
    index = {f: i for i, f in enumerate(unique)}
    source = Image.open(sprite_dir / sprite).convert("RGBA")
    cols = 16
    rows = (len(unique) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    for frame, i in index.items():
        box = meta["fotogrammi"][frame]
        tile = source.crop((box["x"], box["y"], box["x"] + w, box["y"] + h))
        sheet.paste(tile, ((i % cols) * w, (i // cols) * h))
    buffer = io.BytesIO()
    sheet.save(buffer, "PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode(), index, cols, (cols * w, rows * h), (w, h)


def orbi_svg(sprite_dir, theme, x, y, scale, meta):
    frames, ms = orbi_sequence(meta)
    data, index, cols, (sw, sh), (w, h) = orbi_sheet(sprite_dir, THEMES[theme]["sprite"], frames, meta)
    total = len(frames) * ms / 1000
    steps = []
    for n, frame in enumerate(frames):
        i = index[frame]
        steps.append(f"{n * 100 / len(frames):.3f}%{{transform:translate({-(i % cols) * w}px,{-(i // cols) * h}px)}}")
    first = index[frames[0]]
    css = (f"#orbi-reel{{animation:orbi {total:.2f}s steps(1,end) infinite;"
           f"transform:translate({-(first % cols) * w}px,{-(first // cols) * h}px)}}"
           f"@keyframes orbi{{{''.join(steps)}}}")
    body = (f'<g transform="translate({x} {y}) scale({scale})"><clipPath id="orbi-frame"><rect width="{w}" height="{h}"/></clipPath>'
            f'<g clip-path="url(#orbi-frame)"><image id="orbi-reel" width="{sw}" height="{sh}" '
            f'image-rendering="optimizeSpeed" style="image-rendering:pixelated" '
            f'href="data:image/png;base64,{data}"/></g></g>')
    return css, body


# ------------------------------------------------------------------ header


def header(sprite_dir, theme, meta):
    t = THEMES[theme]
    rng = random.Random(77)
    W, H = 960, 320
    stars = []
    for n in range(70):
        sx, sy = rng.randrange(8, W - 8), rng.randrange(8, H - 8)
        if 40 < sx < 560 and 40 < sy < 250:   # keep the words readable
            continue
        size = rng.choice((2, 2, 2, 3, 4))
        stars.append(f'<rect class="star" x="{sx}" y="{sy}" width="{size}" height="{size}" '
                     f'style="animation-duration:{rng.uniform(2.2, 5.5):.1f}s;animation-delay:-{rng.uniform(0, 5):.1f}s"/>')
    hi, end = pixel_text("hi, i'm ", 56, 62, 6, t["text"])
    nas, end = pixel_text("Nas", end, 62, 6, t["accent"])
    dot, _ = pixel_text(".", end - 6, 62, 6, t["text"])
    lines = [
        "builds desktop tools that run on your computer.",
        "draws pixels. tiny ones. on purpose.",
        "lets a small planet named Orbi run the brand.",
        "just released element 01: TikTok Transcriber.",
    ]
    period = 4 * len(lines)
    taglines = "".join(
        f'<text class="line" x="58" y="166" style="animation-delay:{i * 4}s">{line}</text>'
        for i, line in enumerate(lines))
    orbi_css, orbi = orbi_svg(sprite_dir, theme, 648, 54, 4, meta)
    css = (f".star{{fill:{t['star']};animation:twinkle 4s ease-in-out infinite}}"
           f"@keyframes twinkle{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}"
           f".line{{font:600 22px {FONT};fill:{t['text']};opacity:0;animation:line {period}s infinite}}"
           f"@keyframes line{{0%{{opacity:0;transform:translateY(8px)}}3%,22%{{opacity:1;transform:none}}25%,100%{{opacity:0;transform:translateY(-6px)}}}}"
           f".shoot{{stroke:{t['accent']};stroke-width:3;stroke-linecap:square;opacity:0;animation:shoot 11s linear infinite}}"
           f"@keyframes shoot{{0%,82%{{opacity:0;transform:translate(0,0)}}84%{{opacity:1}}92%{{opacity:0;transform:translate(-260px,120px)}}100%{{opacity:0}}}}"
           f".meta{{font:15px {FONT};fill:{t['soft']}}}"
           + orbi_css + STILL)
    first_line_still = (f"@media (prefers-reduced-motion: reduce){{.line:first-of-type{{opacity:1}}}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="hi, I\'m Nas. I build desktop tools, draw pixel art, and let a planet named Orbi run the brand.">'
            f"<title>hi, I'm Nas</title><style>{css}{first_line_still}</style>"
            f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>{"".join(stars)}'
            f'<line class="shoot" x1="900" y1="20" x2="940" y2="2"/>'
            f'<g shape-rendering="crispEdges">{hi}{nas}{dot}</g>{taglines}'
            f'<text class="meta" x="58" y="214">python · javascript · pixel art · windows · macos · linux</text>'
            f'<text class="meta" x="58" y="240">currently: teaching a planet to wink on command</text>'
            f"{orbi}</svg>\n")


# ------------------------------------------------------------------ periodic table


def locked_tile(category):
    canvas = [["." for _ in range(32)] for _ in range(32)]
    for yy in range(32):
        for xx in range(32):
            canvas[yy][xx] = "k" if (yy in (0, 31) or xx in (0, 31)) else "n"
    for xx, yy in ((0, 0), (31, 0), (0, 31), (31, 31)):
        canvas[yy][xx] = "."
    question = EXTRA["?"].split()
    for i in range(2):
        for gy, row in enumerate(question):
            for gx, c in enumerate(row):
                if c == "#":
                    for dy in range(2):
                        for dx in range(2):
                            canvas[10 + gy * 2 + dy][5 + i * 12 + gx * 2 + dx] = "c"
    for xx in range(4, 28, 2):
        canvas[27][xx] = "k"
    return ["".join(r) for r in canvas]


def tile_svg(grid, category, theme, x, y, scale, cls="", dim=False):
    pal = element.palette(category, light=(theme == "light"))
    colors = {"k": f'fill="#{pal["k"]}"', "n": f'fill="#{pal["n"]}"',
              "c": f'fill="#{pal["k"] if dim else pal["c"]}"'}
    return (f'<g class="{cls}" transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges">'
            + element.rects(grid, colors) + "</g>")


def table(theme):
    t = THEMES[theme]
    W, H = 960, 330
    title, _ = pixel_text("the periodic table of Nas", 40, 34, 3, t["text"])
    parts, captions = [], []
    published = [e for e in ELEMENTS["elements"]]
    locked = ELEMENTS["classified"]
    slots = published + [{"locked": True, "category": c} for c in locked]
    size, gap = 96, 14
    x0, y0 = 40, 92
    for i, item in enumerate(slots):
        x = x0 + i * (size + gap)
        if item.get("locked"):
            parts.append(tile_svg(locked_tile(item["category"]), item["category"], theme, x, y0, 3,
                                  cls=f"locked l{i % 4}", dim=True))
            captions.append(f'<text class="cap dim" x="{x + size / 2}" y="{y0 + size + 22}">classified</text>')
        else:
            grid = element.tile(item["number"], item["symbol"], item["category"])
            parts.append(f'<rect class="glow" x="{x - 5}" y="{y0 - 5}" width="{size + 10}" height="{size + 10}" rx="6" '
                         f'fill="none" stroke="#{element.CATEGORIES[item["category"]]}" stroke-width="3"/>')
            parts.append(tile_svg(grid, item["category"], theme, x, y0, 3))
            words = item["name"].split(" ", 1)
            for n, word in enumerate(words):
                captions.append(f'<text class="cap" x="{x + size / 2}" y="{y0 + size + 22 + n * 16}">{word}</text>')
    legend, lx = [], 40
    for name, color in element.CATEGORIES.items():
        legend.append(f'<rect x="{lx}" y="{H - 52}" width="14" height="14" fill="#{color}"/>'
                      f'<text class="leg" x="{lx + 22}" y="{H - 40}">{name}</text>')
        lx += 36 + len(name) * 10
    css = (f".cap{{font:600 13px {FONT};fill:{t['text']};text-anchor:middle}}.dim{{fill:{t['soft']};opacity:.7}}"
           f".leg{{font:14px {FONT};fill:{t['soft']}}}.sub{{font:15px {FONT};fill:{t['soft']}}}"
           f".glow{{animation:glow 2.6s ease-in-out infinite}}@keyframes glow{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}"
           f".locked{{opacity:.55;animation:flicker 7s steps(1,end) infinite}}"
           f".l1{{animation-delay:-2s}}.l2{{animation-delay:-4.5s}}.l3{{animation-delay:-6s}}"
           f"@keyframes flicker{{0%,100%{{opacity:.55}}91%{{opacity:.55}}92%{{opacity:.9}}93%{{opacity:.4}}94%{{opacity:.8}}95%{{opacity:.55}}}}"
           + STILL)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="The periodic table of Nas: element 01 is TikTok Transcriber; the other projects are still classified.">'
            f"<title>The periodic table of Nas</title><style>{css}</style>"
            f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>'
            f'<g shape-rendering="crispEdges">{title}</g>'
            f'<text class="sub" x="40" y="74">one element per project · number = order of release · color = what it is</text>'
            f'{"".join(parts)}{"".join(captions)}{"".join(legend)}</svg>\n')


def main():
    sprite_dir = Path(sys.argv[1])
    meta = json.loads((sprite_dir / "orbi.json").read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"header-{theme}.svg").write_text(header(sprite_dir, theme, meta), encoding="utf-8")
        (ASSETS / f"table-{theme}.svg").write_text(table(theme), encoding="utf-8")
    for e in ELEMENTS["elements"]:
        grid = element.tile(e["number"], e["symbol"], e["category"])
        (ASSETS / f"element-{e['number']:02d}.svg").write_text(
            element.svg(grid, e["category"], e["name"], size=96), encoding="utf-8")
    for path in sorted(ASSETS.glob("*.svg")):
        print(f"{path.name}: {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
