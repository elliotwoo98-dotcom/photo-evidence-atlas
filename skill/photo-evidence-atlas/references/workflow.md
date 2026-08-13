# Rendering Workflow

## 1. Prepare

Use Python 3.10 or newer with Pillow installed:

```bash
python -m pip install Pillow
```

Work from the skill directory or call `scripts/build_atlas.py` by absolute path. Keep the source file unchanged.

## 2. Inspect And Name

Open the source image before rendering. Identify only facts supported by the pixels. Choose a short title and optional note using the titling rules in `design-system.md`.

Do not infer a precise location, identity, date, event, or relationship from appearance alone. When a requested title contains exact text, pass it unchanged.

## 3. Render

Portrait default:

```bash
python scripts/build_atlas.py source.jpg atlas.png \
  --title "Low Water Line" \
  --plate-id "FIELD 01" \
  --analysis-json atlas.json
```

Format and theme variants:

```bash
python scripts/build_atlas.py source.jpg atlas-square.png \
  --title "North Window" \
  --format square \
  --theme carbon \
  --analysis-json atlas-square.json
```

The renderer always uses a no-crop contain fit. Do not preprocess the input with an image generator.

## 4. Validate

Inspect the PNG at full size and verify:

- source orientation and aspect ratio;
- exact title and note text;
- readable small labels;
- no overlap or clipped modules;
- plausible photo-derived palette and field map;
- correct output dimensions;
- no unintended personal data in the title, note, plate identifier, or filename.

Compare the JSON source dimensions with the input. The JSON records the palette and traces used by the renderer and is the audit trail for the visual modules.

## 5. Iterate Safely

Change only one variable per revision: title, note, format, theme, or plate identifier. Write to a new filename such as `atlas-v2.png`; do not overwrite an approved output unless the user explicitly asks.

## Edge Cases

- **Very wide panoramas:** use landscape output; accept neutral letterboxing rather than cropping.
- **Very tall images:** use portrait output; keep the full frame and let side margins widen.
- **Transparent input:** composite transparency onto the neutral photo-window matte only; record the original dimensions normally.
- **Monochrome input:** repeat distinct gray roles when five separated colors are unavailable; do not invent chroma.
- **Long exact title:** the renderer reduces type size and wraps within the title block. Inspect the result instead of shortening user text.
- **Unreadable source:** stop and report the decode error. Do not substitute a generated approximation.
