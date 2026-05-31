# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image

ROOT_PATH = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from asset_editor_application import AssetEditorApplication
from document.image_document import ImageDocument
from transparency.image_transparency_processor import ImageTransparencyProcessor
from transparency.transparency_selection import (
    ImageSelectionRectangle,
    TransparencySelectionMode,
)


class TransparencyWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = ImageTransparencyProcessor()

    def test_single_color_transparency_keeps_other_pixels(self) -> None:
        image = Image.new("RGBA", (3, 1))
        image.putdata(
            [
                (255, 0, 0, 255),
                (0, 255, 0, 255),
                (255, 0, 0, 128),
            ],
        )

        result = self.processor.apply_transparent_colors(
            image,
            {(255, 0, 0)},
        )

        self.assertEqual(result.getpixel((0, 0)), (255, 0, 0, 0))
        self.assertEqual(result.getpixel((1, 0)), (0, 255, 0, 255))
        self.assertEqual(result.getpixel((2, 0)), (255, 0, 0, 0))

    def test_rectangle_color_collection_and_transparency(self) -> None:
        image = Image.new("RGBA", (3, 3), (9, 9, 9, 255))
        image.putpixel((0, 0), (10, 0, 0, 255))
        image.putpixel((1, 0), (0, 20, 0, 255))
        image.putpixel((0, 1), (10, 0, 0, 255))
        rectangle = ImageSelectionRectangle(0, 0, 1, 1)

        colors = self.processor.collect_rectangle_colors(image, rectangle)
        result = self.processor.apply_transparent_colors(image, colors)

        self.assertEqual(colors, {(10, 0, 0), (0, 20, 0), (9, 9, 9)})
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((1, 0))[3], 0)
        self.assertEqual(result.getpixel((2, 2))[3], 0)

    def test_area_selection_keeps_edge_enclosed_foreground(self) -> None:
        image = Image.new("RGBA", (40, 40), (255, 255, 255, 255))
        for y_position in range(12, 28):
            for x_position in range(12, 28):
                image.putpixel((x_position, y_position), (0, 0, 0, 255))

        area_mask = self.processor.collect_area_mask(image, (0, 0))
        result = self.processor.apply_transparent_mask(image, area_mask)

        self.assertTrue(area_mask[0, 0])
        self.assertFalse(area_mask[20, 20])
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((5, 5))[3], 0)
        self.assertEqual(result.getpixel((20, 20))[3], 255)

    def test_area_selection_can_select_inner_region(self) -> None:
        image = Image.new("RGBA", (40, 40), (255, 255, 255, 255))
        for y_position in range(12, 28):
            for x_position in range(12, 28):
                image.putpixel((x_position, y_position), (0, 0, 0, 255))

        area_mask = self.processor.collect_area_mask(image, (20, 20))

        self.assertFalse(area_mask[0, 0])
        self.assertTrue(area_mask[20, 20])

    def test_selection_highlight_only_changes_masked_preview_pixels(self) -> None:
        image = Image.new("RGBA", (3, 3), (10, 20, 30, 255))
        area_mask = np.zeros((3, 3), dtype=bool)
        area_mask[1, 1] = True

        highlighted = self.processor.apply_selection_highlight(image, area_mask)

        self.assertEqual(highlighted.getpixel((0, 0)), (10, 20, 30, 255))
        self.assertNotEqual(highlighted.getpixel((1, 1)), (10, 20, 30, 255))

    def test_document_reset_restores_working_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "source.png"
            Image.new("RGBA", (1, 1), (1, 2, 3, 255)).save(image_path)

            document = ImageDocument()
            document.load(str(image_path))
            document.working_image = self.processor.apply_transparent_colors(
                document.working_image,
                {(1, 2, 3)},
            )
            document.reset_working_image()

            self.assertEqual(document.working_image.getpixel((0, 0))[3], 255)

    def test_document_save_uses_working_image_alpha_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "source.png"
            png_path = temp_path / "result.png"
            jpg_path = temp_path / "result.jpg"
            Image.new("RGBA", (1, 1), (1, 2, 3, 255)).save(source_path)

            document = ImageDocument()
            document.load(str(source_path))
            document.working_image = self.processor.apply_transparent_colors(
                document.working_image,
                {(1, 2, 3)},
            )
            document.save(str(png_path))
            document.save(str(jpg_path))

            with Image.open(png_path) as png_image:
                self.assertEqual(
                    png_image.convert("RGBA").getpixel((0, 0))[3],
                    0,
                )
            with Image.open(jpg_path) as jpg_image:
                self.assertEqual(jpg_image.mode, "RGB")

    def test_zoomed_display_point_maps_to_image_bounds(self) -> None:
        app = AssetEditorApplication()
        app.document.working_image = Image.new("RGBA", (100, 50))
        app._get_preview_display_rect = lambda: (10.0, 20.0, 200.0, 100.0)

        self.assertEqual(app._display_point_to_image_point(110, 70), (50, 25))
        self.assertEqual(
            app._display_point_to_image_point(250, 200, clamp=True),
            (99, 49),
        )
        self.assertIsNone(app._display_point_to_image_point(250, 200))

    def test_transparency_controls_are_created(self) -> None:
        app = AssetEditorApplication()
        dpg.create_context()
        try:
            with dpg.window(tag="test_window"):
                app._build_controls()

            self.assertTrue(dpg.does_item_exist(app.transparency_mode_combo_tag))
            self.assertTrue(
                dpg.does_item_exist(app.transparency_selection_summary_tag),
            )
            self.assertIn("영역 선택", TransparencySelectionMode.labels())
            self.assertNotIn("외곽 선택", TransparencySelectionMode.labels())
        finally:
            dpg.destroy_context()

    def test_preview_processor_keeps_grayscale_and_edge_views(self) -> None:
        from preview.image_preview_processor import ImagePreviewProcessor
        from preview.preview_options import PreviewOptions

        preview_processor = ImagePreviewProcessor()
        image = Image.fromarray(
            np.full((10, 10, 4), fill_value=255, dtype=np.uint8),
        )

        grayscale = preview_processor.apply(
            image,
            PreviewOptions(grayscale=True),
        )
        edge = preview_processor.apply(
            image,
            PreviewOptions(edge_preview=True),
        )

        self.assertEqual(grayscale.mode, "RGBA")
        self.assertEqual(edge.mode, "RGBA")


if __name__ == "__main__":
    unittest.main()
