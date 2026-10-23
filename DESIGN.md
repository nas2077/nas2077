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

Every project is an element of one periodic table: a 32 x 32 pixel tile with its
release number, a two-letter symbol and the color of its category (app, game,
site, design, animation, study). Small sizes use a 16 x 16 badge with the symbol
only. The tiles are drawn by [`tools/element.py`](tools/element.py) from
[`elements.json`](elements.json).
