---
name: photo-evidence-atlas
description: Turn one supplied photograph into a restrained editorial evidence plate that keeps the source photo visibly intact and surrounds it with photo-derived color samples, tonal traces, a field map, and concise titling. Use when asked for a photo archive page, visual field note, exhibition index plate, photographic contact sheet, image evidence poster, or factual editorial composition without redrawing, filtering, or generatively altering the photograph.
---

# Photo Evidence Atlas

Build one finished evidence plate from one user-supplied photograph. Preserve the photograph as the record; derive every supporting graphic from measured image data.

## Workflow

1. Inspect the photograph and identify its concrete subject, dominant direction, light condition, and strongest spatial interval.
2. Read [references/design-system.md](references/design-system.md) before composing. Read [references/workflow.md](references/workflow.md) when running the renderer or handling edge cases.
3. Write one factual title of one to four words. Keep any optional note to four to twelve words. Do not invent a place, date, person, event, or story.
4. Run `scripts/build_atlas.py` with the source image, exact title, output path, and an analysis JSON path. Prefer the portrait format unless the requested destination calls for square or landscape.
5. Inspect both outputs. Confirm that the photograph remains unfiltered and uncropped, the title is exact, the sampled graphics reflect the source, and no text or marks overlap.
6. Return the finished plate and, when useful, the analysis JSON. Keep alternate versions as separately named files.

```bash
python scripts/build_atlas.py input.jpg output.png \
  --title "Measured Silence" \
  --note "A red interval holds the empty platform" \
  --plate-id "FIELD 01" \
  --analysis-json output.json
```

## Hard Rules

- Treat the supplied photograph as the only visual source.
- Allow EXIF orientation correction and proportional scaling. Do not redraw, retouch, recolor, filter, outpaint, replace, or generatively reconstruct the photo.
- Keep the whole photograph visible by default. Crop only when the user explicitly requests it; the bundled renderer uses a no-crop contain fit.
- Derive the sample rail, field map, luminance traces, palette, and numeric observations from the source pixels.
- Keep the modules functional: image window, sample rail, title block, field map, twin trace, and source metrics. Do not turn them into free decoration.
- Render user-supplied title and note text verbatim. Never add a logo, signature, watermark, fabricated credit, or promotional copy.
- Use one plate per source image unless the user explicitly requests a series.
- Do not reuse subjects, palettes, titles, or layouts from repository examples.

## Output Contract

- Default: one 1600 x 2000 PNG evidence plate plus one JSON analysis record.
- Square: 1600 x 1600. Landscape: 2000 x 1400.
- Keep important content inside the built-in safe margins.
- Preserve previous deliverables; create a versioned filename for revisions.
- Report technical validation separately from the user's visual approval.
