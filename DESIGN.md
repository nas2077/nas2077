# Nas design system

The visual language shared by my projects. Smooth typography and surfaces, tactile controls, pixel artwork.

| Token | Color | Use |
|---|---|---|
| Ink | `#1B2632` | Dark canvas; light-theme text |
| Slate | `#2C3B4D` | Raised surfaces; secondary text |
| Cream | `#EEE9DF` | Light canvas; dark-theme text |
| Sand | `#C9C1B1` | Secondary text; raised light surfaces |
| Rust | `#A35139` | Primary action |
| Orange | `#FFB162` | Pixel artwork accents |

## Components

Buttons and switches have a raised edge. Fields are recessed. Text remains flat. Inter is the primary typeface; code uses the system monospace font.

Spacing follows a 4, 8, 14, 24, 48, 72, and 96 pixel scale. Corners vary with the selected preset. Pixel artwork scales by whole numbers.

## Identity

The N signature identifies the author. Orbi is the orange ringed mascot, with a small moon, expressive poses, and discrete animation frames. Individual products use their own names and logos.

## Motion and accessibility

Dark and light themes use the same semantic roles. Keyboard focus remains visible. Reduced motion freezes decorative animation. A quiet preset keeps movement restrained; expressive and off options are also available.

## Project icons

Every project is an element of one periodic table, drawn in the shape of the
real one. Its four blocks are the four families of work: products (s-block,
orange), client work (d-block, blue), experiments (p-block, green), and design
and study (f-block, purple). An element is a filled square in its family's
color with the release number in the corner and a two-letter symbol in Barlow
Bold; empty cells keep the outline of their block. The table and the element
icons are drawn by [`tools/periodic.py`](tools/periodic.py) from
[`elements.json`](elements.json), with the lettering turned into paths.
