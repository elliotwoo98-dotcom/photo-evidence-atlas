#!/usr/bin/env python3
"""Build a deterministic visual-evidence plate from one source photograph."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, Optional, Sequence

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat
except ImportError as exc:  # pragma: no cover - exercised only without the dependency
    raise SystemExit("Pillow is required. Install it with: python -m pip install Pillow") from exc


FORMATS = {
    "portrait": (1600, 2000),
    "square": (1600, 1600),
    "landscape": (2000, 1400),
}

THEMES = {
    "paper": {
        "canvas": (233, 238, 235),
        "ink": (23, 27, 29),
        "muted": (91, 101, 99),
        "rule": (174, 184, 180),
        "matte": (218, 224, 221),
    },
    "carbon": {
        "canvas": (21, 25, 27),
        "ink": (239, 242, 239),
        "muted": (166, 176, 172),
        "rule": (70, 79, 77),
        "matte": (35, 41, 42),
    },
}

TRANSPARENCY_MATTE = THEMES["paper"]["matte"]

FONT_CANDIDATES = {
    "regular": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    key = "bold" if bold else "regular"
    for candidate in FONT_CANDIDATES[key]:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _rgb_distance(first: Sequence[int], second: Sequence[int]) -> float:
    return math.sqrt(sum((int(a) - int(b)) ** 2 for a, b in zip(first, second)))


def _color_chroma(color: Sequence[int]) -> int:
    return max(color) - min(color)


def _normalized_rgb(image: Image.Image) -> Image.Image:
    source = ImageOps.exif_transpose(image)
    has_alpha = source.mode in {"RGBA", "LA"} or "transparency" in source.info
    if not has_alpha:
        return source.convert("RGB")

    rgba = source.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (*TRANSPARENCY_MATTE, 255))
    return Image.alpha_composite(background, rgba).convert("RGB")


def _dominant_palette(image: Image.Image, count: int = 5) -> list[tuple[int, int, int]]:
    sample = ImageOps.contain(image.convert("RGB"), (192, 192), Image.Resampling.LANCZOS)
    quantized = sample.quantize(colors=32, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette() or []
    ranked = sorted(quantized.getcolors() or [], reverse=True)
    weighted_colors: list[tuple[int, tuple[int, int, int]]] = []
    for pixel_count, index in ranked:
        offset = index * 3
        color = tuple(raw_palette[offset : offset + 3])
        if len(color) == 3:
            weighted_colors.append((pixel_count, color))

    candidates: list[tuple[int, int, int]] = []
    for _, color in weighted_colors:
        if not candidates or all(_rgb_distance(color, existing) >= 34 for existing in candidates):
            candidates.append(color)
        if len(candidates) == count:
            break

    # Reserve one slot for a measured accent when a small chromatic region would
    # otherwise disappear behind the four most common neutral fields.
    total_pixels = max(1, sample.width * sample.height)
    accent_pool = [
        (pixel_count * (_color_chroma(color) ** 2), color)
        for pixel_count, color in weighted_colors
        if pixel_count / total_pixels >= 0.006
        and _color_chroma(color) >= 36
        and all(_rgb_distance(color, existing) >= 34 for existing in candidates[:4])
    ]
    if accent_pool:
        accent = max(accent_pool)[1]
        candidates = candidates[: max(0, count - 1)] + [accent]

    if not candidates:
        candidates = [(128, 128, 128)]
    while len(candidates) < count:
        candidates.append(candidates[-1])
    return candidates


def _profiles(image: Image.Image, bins: int = 32) -> tuple[list[float], list[float]]:
    grid = image.convert("L").resize((bins, bins), Image.Resampling.BOX)
    pixels = grid.load()
    horizontal = [sum(pixels[x, y] for y in range(bins)) / (255 * bins) for x in range(bins)]
    vertical = [sum(pixels[x, y] for x in range(bins)) / (255 * bins) for y in range(bins)]
    return horizontal, vertical


def _field_map(image: Image.Image, columns: int = 6, rows: int = 4) -> list[list[tuple[int, int, int]]]:
    reduced = image.convert("RGB").resize((columns, rows), Image.Resampling.BOX)
    pixels = reduced.load()
    return [[tuple(pixels[x, y]) for x in range(columns)] for y in range(rows)]


def _contrast_energy(image: Image.Image) -> float:
    gray = image.convert("L").resize((96, 96), Image.Resampling.BOX)
    pixels = gray.load()
    total = 0
    comparisons = 0
    for y in range(96):
        for x in range(96):
            if x + 1 < 96:
                total += abs(pixels[x + 1, y] - pixels[x, y])
                comparisons += 1
            if y + 1 < 96:
                total += abs(pixels[x, y + 1] - pixels[x, y])
                comparisons += 1
    return total / (255 * comparisons) if comparisons else 0.0


def analyze_image(image: Image.Image) -> dict:
    source = _normalized_rgb(image)
    width, height = source.size
    horizontal, vertical = _profiles(source)
    palette = _dominant_palette(source)
    field = _field_map(source)
    mean_luminance = ImageStat.Stat(source.convert("L")).mean[0] / 255
    return {
        "source": {
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 6),
            "orientation": "landscape" if width > height else "portrait" if height > width else "square",
        },
        "palette": ["#%02X%02X%02X" % color for color in palette],
        "field_map": [["#%02X%02X%02X" % color for color in row] for row in field],
        "luminance": {
            "mean": round(mean_luminance, 6),
            "horizontal_profile": [round(value, 6) for value in horizontal],
            "vertical_profile": [round(value, 6) for value in vertical],
        },
        "contrast_energy": round(_contrast_energy(source), 6),
    }


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _split_token(draw: ImageDraw.ImageDraw, token: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if _text_width(draw, token, font) <= max_width:
        return [token]
    parts: list[str] = []
    current = ""
    for character in token:
        candidate = current + character
        if current and _text_width(draw, candidate, font) > max_width:
            parts.append(current)
            current = character
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            for part_index, part in enumerate(_split_token(draw, word, font, max_width)):
                separator = " " if current and part_index == 0 else ""
                candidate = f"{current}{separator}{part}"
                if not current or _text_width(draw, candidate, font) <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = part
        if current:
            lines.append(current)
    return lines


def _fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    start: int,
    minimum: int,
    bold: bool,
    max_lines: int,
    line_gap: int,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    absolute_minimum = max(12, min(minimum, start))
    for size in range(start, absolute_minimum - 1, -2):
        font = _load_font(size, bold=bold)
        lines = _wrap_text(draw, text, font, max_width)
        line_box = draw.textbbox((0, 0), "Ag", font=font)
        line_height = line_box[3] - line_box[1] + line_gap
        widths = [_text_width(draw, line, font) for line in lines]
        block_height = len(lines) * line_height
        if len(lines) <= max_lines and max(widths, default=0) <= max_width and block_height <= max_height:
            return font, lines, line_height
    raise ValueError(f"text does not fit the {max_lines}-line layout: {text!r}")


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _place_source(canvas: Image.Image, source: Image.Image, box: tuple[int, int, int, int], matte: tuple[int, int, int]) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    canvas.paste(matte, box)
    fitted = ImageOps.contain(source, (width, height), Image.Resampling.LANCZOS)
    x = left + (width - fitted.width) // 2
    y = top + (height - fitted.height) // 2
    canvas.paste(fitted, (x, y))


def _plot_profile(
    draw: ImageDraw.ImageDraw,
    values: Iterable[float],
    box: tuple[int, int, int, int],
    color: tuple[int, int, int],
    width: int,
) -> None:
    values = list(values)
    left, top, right, bottom = box
    if len(values) < 2:
        return
    points = []
    for index, value in enumerate(values):
        x = left + (right - left) * index / (len(values) - 1)
        y = bottom - (bottom - top) * min(1.0, max(0.0, value))
        points.append((round(x), round(y)))
    draw.line(points, fill=color, width=width, joint="curve")


def _save_image(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.convert("RGB").save(output_path, quality=95, optimize=True)
    elif suffix == ".webp":
        image.save(output_path, quality=95, method=6)
    else:
        image.save(output_path, format="PNG", optimize=True)


def render_plate(
    source: Image.Image,
    analysis: dict,
    title: str,
    note: str = "",
    plate_id: str = "FIELD 01",
    output_format: str = "portrait",
    theme_name: str = "paper",
) -> Image.Image:
    if not title.strip():
        raise ValueError("title must not be empty")
    if output_format not in FORMATS:
        raise ValueError(f"unknown format: {output_format}")
    if theme_name not in THEMES:
        raise ValueError(f"unknown theme: {theme_name}")

    source = _normalized_rgb(source)
    width, height = FORMATS[output_format]
    theme = THEMES[theme_name]
    canvas = Image.new("RGB", (width, height), theme["canvas"])
    draw = ImageDraw.Draw(canvas)
    scale = min(width / 1600, height / 2000)
    margin = round(width * 0.055)
    vertical_margin = round(height * 0.055)
    line_width = max(2, round(2 * scale))

    tiny = _load_font(max(14, round(16 * scale)))
    label_font = _load_font(max(16, round(18 * scale)), bold=True)

    header_y = round(height * 0.045)
    draw.text((margin, header_y), plate_id.upper(), font=label_font, fill=theme["ink"])
    source_meta = analysis["source"]
    ratio_text = f"SOURCE {source_meta['width']} x {source_meta['height']}  /  RATIO {source_meta['aspect_ratio']:.3f}"
    ratio_width = draw.textbbox((0, 0), ratio_text, font=tiny)[2]
    draw.text((width - margin - ratio_width, header_y), ratio_text, font=tiny, fill=theme["muted"])
    rule_y = header_y + max(round(height * 0.025), round(36 * scale))
    draw.line((margin, rule_y, width - margin, rule_y), fill=theme["rule"], width=line_width)

    photo_top = round(height * 0.125)
    photo_bottom = round(height * (0.625 if output_format == "portrait" else 0.60))
    photo_left = margin
    photo_right = round(width * 0.82)
    photo_box = (photo_left, photo_top, photo_right, photo_bottom)
    _place_source(canvas, source, photo_box, theme["matte"])
    draw.rectangle(photo_box, outline=theme["rule"], width=line_width)

    rail_left = round(width * 0.855)
    rail_right = width - margin
    rail_label_y = photo_top - round(33 * scale)
    draw.text((rail_left, rail_label_y), "SAMPLED COLOR", font=tiny, fill=theme["muted"])
    palette = [_hex_to_rgb(value) for value in analysis["palette"]]
    rail_gap = max(4, round(7 * scale))
    rail_height = photo_bottom - photo_top
    swatch_height = (rail_height - rail_gap * (len(palette) - 1)) // len(palette)
    for index, color in enumerate(palette):
        top = photo_top + index * (swatch_height + rail_gap)
        bottom = photo_bottom if index == len(palette) - 1 else top + swatch_height
        draw.rectangle((rail_left, top, rail_right, bottom), fill=color)
        label = f"{index + 1:02d}"
        label_color = (245, 245, 242) if sum(color) < 360 else (20, 22, 23)
        draw.text((rail_left + round(10 * scale), top + round(8 * scale)), label, font=tiny, fill=label_color)

    content_top = photo_bottom + round(height * 0.04)
    title_width = round(width * 0.56)
    metrics_y = round(height * 0.82)
    text_bottom = metrics_y - max(round(24 * scale), round(height * 0.012))
    text_height = text_bottom - content_top
    note_gap = max(12, round(22 * scale)) if note else 0
    note_lines: list[str] = []
    note_line_height = 0
    if note:
        note_height_limit = max(round(48 * scale), round(text_height * 0.34))
        note_font, note_lines, note_line_height = _fit_text_block(
            draw,
            note,
            title_width,
            note_height_limit,
            max(18, round(27 * scale)),
            max(14, round(18 * scale)),
            False,
            2,
            max(5, round(8 * scale)),
        )
    note_height = len(note_lines) * note_line_height
    title_height_limit = text_height - note_gap - note_height
    title_font, title_lines, title_line_height = _fit_text_block(
        draw,
        title,
        title_width,
        title_height_limit,
        max(44, round(80 * scale)),
        max(26, round(40 * scale)),
        True,
        2,
        max(6, round(10 * scale)),
    )
    for index, line in enumerate(title_lines):
        draw.text((margin, content_top + index * title_line_height), line, font=title_font, fill=theme["ink"])

    note_y = content_top + len(title_lines) * title_line_height + note_gap
    if note:
        for index, line in enumerate(note_lines):
            draw.text((margin, note_y + index * note_line_height), line, font=note_font, fill=theme["muted"])

    metric_text = (
        f"LUMA {analysis['luminance']['mean']:.3f}  /  "
        f"LOCAL ENERGY {analysis['contrast_energy']:.3f}  /  NO-CROP CONTAIN"
    )
    draw.text((margin, metrics_y), metric_text, font=tiny, fill=theme["muted"])

    map_left = round(width * 0.67)
    map_top = content_top
    map_right = width - margin
    map_bottom = round(height * 0.79)
    draw.text((map_left, map_top - round(32 * scale)), "FIELD MAP  6 x 4", font=tiny, fill=theme["muted"])
    field = [[_hex_to_rgb(value) for value in row] for row in analysis["field_map"]]
    columns = len(field[0])
    rows = len(field)
    cell_gap = max(3, round(5 * scale))
    cell_width = (map_right - map_left - cell_gap * (columns - 1)) // columns
    cell_height = (map_bottom - map_top - cell_gap * (rows - 1)) // rows
    for row_index, row in enumerate(field):
        for column_index, color in enumerate(row):
            left = map_left + column_index * (cell_width + cell_gap)
            top = map_top + row_index * (cell_height + cell_gap)
            draw.rectangle((left, top, left + cell_width, top + cell_height), fill=color)

    trace_top = round(height * 0.89)
    trace_bottom = height - vertical_margin
    trace_left = margin
    trace_right = width - margin
    draw.text((trace_left, trace_top - round(34 * scale)), "TWIN LUMINANCE TRACE  /  H + V", font=tiny, fill=theme["muted"])
    draw.line((trace_left, trace_bottom, trace_right, trace_bottom), fill=theme["rule"], width=line_width)
    trace_color = palette[0]
    second_color = palette[1] if _rgb_distance(palette[0], palette[1]) >= 20 else theme["ink"]
    _plot_profile(draw, analysis["luminance"]["horizontal_profile"], (trace_left, trace_top, trace_right, trace_bottom), trace_color, max(3, round(4 * scale)))
    _plot_profile(draw, analysis["luminance"]["vertical_profile"], (trace_left, trace_top, trace_right, trace_bottom), second_color, max(2, round(2 * scale)))

    return canvas


def build_atlas(
    input_path: Path,
    output_path: Path,
    title: str,
    note: str = "",
    plate_id: str = "FIELD 01",
    output_format: str = "portrait",
    theme: str = "paper",
    analysis_json: Optional[Path] = None,
) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(f"source image not found: {input_path}")
    with Image.open(input_path) as opened:
        source = _normalized_rgb(opened)
    analysis = analyze_image(source)
    plate = render_plate(source, analysis, title, note, plate_id, output_format, theme)
    _save_image(plate, output_path)
    if analysis_json:
        analysis_json.parent.mkdir(parents=True, exist_ok=True)
        analysis_json.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="source photograph")
    parser.add_argument("output", type=Path, help="output PNG, JPEG, or WebP")
    parser.add_argument("--title", required=True, help="exact title to render")
    parser.add_argument("--note", default="", help="optional exact factual note")
    parser.add_argument("--plate-id", default="FIELD 01", help="short plate identifier")
    parser.add_argument("--format", choices=sorted(FORMATS), default="portrait", dest="output_format")
    parser.add_argument("--theme", choices=sorted(THEMES), default="paper")
    parser.add_argument("--analysis-json", type=Path, help="optional JSON audit record")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    build_atlas(
        args.input,
        args.output,
        args.title,
        note=args.note,
        plate_id=args.plate_id,
        output_format=args.output_format,
        theme=args.theme,
        analysis_json=args.analysis_json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
