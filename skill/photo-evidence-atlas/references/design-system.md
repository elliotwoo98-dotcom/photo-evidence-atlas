# Photo Evidence Atlas Design System

## Purpose

Translate a photograph into an editorial record, not an illustration. The photograph is the evidence window. The surrounding modules reveal measurable color, luminance, proportion, and spatial rhythm without pretending to explain what the image means.

## Fixed Visual Grammar

Use all six modules in one quiet, continuous canvas:

1. **Index line** - a small plate identifier and source aspect ratio at the top.
2. **Evidence window** - the complete, proportionally scaled source photograph with no filter or generated extension.
3. **Sample rail** - five source-derived color fields aligned beside the photograph.
4. **Title block** - one short title and an optional factual note.
5. **Field map** - a 6 x 4 low-resolution color observation of the photograph.
6. **Twin trace** - measured horizontal and vertical luminance profiles plotted as two thin lines.

These modules form an atlas page rather than a split photo-and-art panel. Keep their roles legible. Do not replace them with painted marks, silhouettes, icons, decorative geometry, or a miniature tracing of the scene.

## Canvas And Layout

- Use a pale mineral canvas (`#E9EEEB`) with near-black type (`#171B1D`) by default.
- Keep the evidence window dominant, occupying roughly half of the canvas height and three quarters of its width.
- Align the sample rail to the evidence window instead of placing swatches loosely below it.
- Use one continuous baseline system and generous open space. Avoid frames within frames, floating cards, torn edges, tape, shadows, mockups, and textured paper.
- Keep corners square. Use hairline rules only where they separate information.
- Set type in a neutral sans serif. Do not simulate luxury-editorial styling with high-contrast serifs or exaggerated tracking.
- Never place title text on top of the photograph.

## Source Fidelity

The evidence window may receive only:

- EXIF orientation correction;
- color-mode conversion needed for output compatibility;
- proportional downscaling;
- neutral letterboxing when its aspect ratio differs from the window.

Do not alter source content. Exclude filters, tonal grading, background replacement, object removal, beautification, depth blur, added grain, vectorization, posterization, generative fill, and aggressive crop.

## Derived Graphics

Derive every graphic deterministically from source pixels:

- Select four separated dominant colors from a reduced image palette and reserve one slot for a measured chromatic accent when it occupies enough source pixels to be meaningful.
- Build the field map from average colors in a 6 x 4 sampling grid.
- Calculate twin traces from 32-bin grayscale averages across rows and columns.
- Report source width, source height, aspect ratio, mean luminance, and local contrast energy.

Do not add colors merely to balance the composition. The canvas and ink colors are interface neutrals; all chromatic marks must come from the photograph.

## Titling

Use one to four words anchored in visible evidence. Favor a subject plus a relationship, interval, direction, light condition, or material fact.

Good patterns:

- `Red Interval`
- `After the Crossing`
- `Two Windows North`
- `Low Water Line`

Avoid vague emotional abstractions, destination slogans, camera jargon, and unsupported narrative. Keep the optional note factual and short. If exact user text is supplied, reproduce it without rewriting.

## Theme Variants

Use `paper` by default. Use `carbon` only when the user requests a dark presentation or the publishing context clearly requires it. The module structure and source-fidelity rules remain unchanged.

## Quality Gate

Before delivery, verify:

- the complete photograph is visible and undistorted;
- no generated pixels appear inside the evidence window;
- sample colors and field-map colors exist in the source analysis;
- the title is exact and fits its block;
- every module stays inside the canvas;
- the output is visually nonblank and has the requested dimensions;
- the prior version remains available when this is a revision.
