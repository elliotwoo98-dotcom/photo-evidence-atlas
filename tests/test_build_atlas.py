import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "photo-evidence-atlas" / "scripts" / "build_atlas.py"
SPEC = importlib.util.spec_from_file_location("build_atlas", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BuildAtlasTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source_path = self.root / "source.png"
        source = Image.new("RGB", (240, 120), (205, 46, 52))
        for x in range(120, 240):
            for y in range(120):
                source.putpixel((x, y), (27, 91, 140))
        source.save(self.source_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_analysis_records_source_geometry(self):
        with Image.open(self.source_path) as source:
            result = MODULE.analyze_image(source)
        self.assertEqual(result["source"]["width"], 240)
        self.assertEqual(result["source"]["height"], 120)
        self.assertEqual(result["source"]["orientation"], "landscape")
        self.assertEqual(result["source"]["aspect_ratio"], 2.0)

    def test_analysis_has_complete_derived_modules(self):
        with Image.open(self.source_path) as source:
            result = MODULE.analyze_image(source)
        self.assertEqual(len(result["palette"]), 5)
        self.assertEqual(len(result["field_map"]), 4)
        self.assertTrue(all(len(row) == 6 for row in result["field_map"]))
        self.assertEqual(len(result["luminance"]["horizontal_profile"]), 32)
        self.assertEqual(len(result["luminance"]["vertical_profile"]), 32)

    def test_palette_is_source_derived(self):
        with Image.open(self.source_path) as source:
            result = MODULE.analyze_image(source)
        first_two = {value.upper() for value in result["palette"][:2]}
        self.assertIn("#CD2E34", first_two)
        self.assertIn("#1B5B8C", first_two)

    def test_small_chromatic_accent_is_retained(self):
        source = Image.new("RGB", (300, 200), (178, 181, 180))
        for x in range(120, 180):
            for y in range(90, 110):
                source.putpixel((x, y), (190, 25, 35))
        result = MODULE.analyze_image(source)
        colors = [MODULE._hex_to_rgb(value) for value in result["palette"]]
        self.assertTrue(any(red > 150 and red > green * 3 for red, green, _ in colors))

    def test_portrait_render_dimensions_and_nonblank_pixels(self):
        output = self.root / "atlas.png"
        MODULE.build_atlas(self.source_path, output, "Red Interval")
        with Image.open(output) as image:
            self.assertEqual(image.size, (1600, 2000))
            extrema = ImageChops.difference(image, Image.new("RGB", image.size, image.getpixel((0, 0)))).getbbox()
            self.assertIsNotNone(extrema)

    def test_all_output_formats(self):
        expected = {"portrait": (1600, 2000), "square": (1600, 1600), "landscape": (2000, 1400)}
        for output_format, size in expected.items():
            with self.subTest(output_format=output_format):
                output = self.root / f"atlas-{output_format}.png"
                MODULE.build_atlas(self.source_path, output, "Measured Field", output_format=output_format)
                with Image.open(output) as image:
                    self.assertEqual(image.size, size)

    def test_analysis_json_matches_return_value(self):
        output = self.root / "atlas.png"
        json_path = self.root / "atlas.json"
        returned = MODULE.build_atlas(self.source_path, output, "Measured Field", analysis_json=json_path)
        saved = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(saved, returned)

    def test_long_title_and_note_render(self):
        for output_format in MODULE.FORMATS:
            with self.subTest(output_format=output_format):
                output = self.root / f"long-title-{output_format}.png"
                MODULE.build_atlas(
                    self.source_path,
                    output,
                    "A Deliberately Long Exact Exhibition Title",
                    note="This factual note is also intentionally long enough to wrap safely",
                    output_format=output_format,
                )
                self.assertTrue(output.is_file())

    def test_unbroken_title_wraps_without_changing_characters(self):
        canvas = Image.new("RGB", (1600, 2000), "white")
        draw = MODULE.ImageDraw.Draw(canvas)
        title = "COASTALOBSERVATIONFIELDNOTESREDINTERVALCONCRETE"
        font = MODULE._load_font(64, bold=True)
        lines = MODULE._wrap_text(draw, title, font, 600)
        self.assertGreater(len(lines), 1)
        self.assertEqual("".join(lines), title)
        self.assertTrue(all(MODULE._text_width(draw, line, font) <= 600 for line in lines))

    def test_transparent_source_uses_neutral_matte(self):
        transparent = Image.new("RGBA", (120, 80), (0, 0, 0, 0))
        result = MODULE.analyze_image(transparent)
        expected = "#%02X%02X%02X" % MODULE.TRANSPARENCY_MATTE
        self.assertEqual(result["palette"][0], expected)
        self.assertGreater(result["luminance"]["mean"], 0.8)

    def test_empty_title_is_rejected(self):
        output = self.root / "empty.png"
        with self.assertRaises(ValueError):
            MODULE.build_atlas(self.source_path, output, "   ")

    def test_missing_source_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            MODULE.build_atlas(self.root / "missing.jpg", self.root / "missing.png", "Missing")


if __name__ == "__main__":
    unittest.main()
