"""Build the animated profile artwork: the header with Orbi and the periodic table.

    python tools/build_profile.py [folder with orbi.json, orbi-scuro.png, orbi-chiaro.png]

Needs Pillow and fontTools. Writes assets/table-{dark,light}.svg and one
assets/element-NN.svg per element; with the Orbi folder, also
assets/header-{dark,light}.svg.
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
import periodic  # noqa: E402

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


def main():
    ASSETS.mkdir(exist_ok=True)
    if len(sys.argv) > 1:
        sprite_dir = Path(sys.argv[1])
        meta = json.loads((sprite_dir / "orbi.json").read_text(encoding="utf-8"))
        for theme in THEMES:
            (ASSETS / f"header-{theme}.svg").write_text(header(sprite_dir, theme, meta), encoding="utf-8")
    for theme in periodic.THEMES:
        (ASSETS / f"table-{theme}.svg").write_text(periodic.table(theme, ELEMENTS["elements"]), encoding="utf-8")
    for e in ELEMENTS["elements"]:
        (ASSETS / f"element-{e['number']:02d}.svg").write_text(periodic.tile(e), encoding="utf-8")
    for path in sorted(ASSETS.glob("*.svg")):
        print(f"{path.name}: {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
