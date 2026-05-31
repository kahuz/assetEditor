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
    TransparencyExcludeMode,
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

    def test_area_mask_subtraction_removes_only_excluded_pixels(self) -> None:
        base_mask = np.ones((3, 3), dtype=bool)
        exclude_mask = np.zeros((3, 3), dtype=bool)
        exclude_mask[1, :] = True

        result = self.processor.subtract_area_mask(base_mask, exclude_mask)

        self.assertEqual(int(result.sum()), 6)
        self.assertTrue(result[0, 0])
        self.assertFalse(result[1, 1])
        self.assertTrue(result[2, 2])

    def test_area_mask_subtraction_rejects_different_size(self) -> None:
        base_mask = np.ones((3, 3), dtype=bool)
        exclude_mask = np.ones((2, 2), dtype=bool)

        with self.assertRaises(ValueError):
            self.processor.subtract_area_mask(base_mask, exclude_mask)

    def test_rectangle_mask_supports_manual_area_exclusion(self) -> None:
        rectangle = ImageSelectionRectangle(1, 1, 3, 2)

        exclude_mask = self.processor.collect_rectangle_mask(
            (5, 4),
            rectangle,
        )

        self.assertEqual(int(exclude_mask.sum()), 6)
        self.assertTrue(exclude_mask[1, 1])
        self.assertTrue(exclude_mask[2, 3])
        self.assertFalse(exclude_mask[0, 0])

    def test_freeform_mask_supports_manual_area_exclusion(self) -> None:
        points = [(1, 1), (4, 1), (1, 4)]

        exclude_mask = self.processor.collect_freeform_mask((6, 6), points)

        self.assertTrue(exclude_mask[2, 2])
        self.assertFalse(exclude_mask[5, 5])

    def test_freeform_mask_requires_enough_points(self) -> None:
        exclude_mask = self.processor.collect_freeform_mask(
            (6, 6),
            [(1, 1), (2, 2)],
        )

        self.assertEqual(int(exclude_mask.sum()), 0)

    def test_detail_area_mask_supports_area_based_exclusion(self) -> None:
        image = Image.new("RGBA", (40, 20), (255, 255, 255, 255))
        for y_position in range(0, 20):
            image.putpixel((19, y_position), (0, 0, 0, 255))
            image.putpixel((20, y_position), (0, 0, 0, 255))

        selection_mask = np.ones((20, 40), dtype=bool)
        exclude_mask = self.processor.collect_detail_area_mask(
            image,
            selection_mask,
            (5, 10),
        )
        result = self.processor.subtract_area_mask(selection_mask, exclude_mask)

        self.assertTrue(exclude_mask[10, 5])
        self.assertFalse(exclude_mask[10, 30])
        self.assertFalse(result[10, 5])
        self.assertTrue(result[10, 30])

    def test_detail_area_mask_ignores_points_outside_selection(self) -> None:
        image = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        selection_mask = np.zeros((10, 10), dtype=bool)
        selection_mask[4:7, 4:7] = True

        exclude_mask = self.processor.collect_detail_area_mask(
            image,
            selection_mask,
            (0, 0),
        )

        self.assertEqual(int(exclude_mask.sum()), 0)

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
            self.assertTrue(dpg.does_item_exist(app.area_exclude_check_tag))
            self.assertTrue(dpg.does_item_exist(app.area_exclude_mode_combo_tag))
            self.assertTrue(dpg.does_item_exist(app.preview_pan_check_tag))
            self.assertTrue(
                dpg.does_item_exist(app.transparency_selection_summary_tag),
            )
            self.assertIn("영역 선택", TransparencySelectionMode.labels())
            self.assertIn("사각형", TransparencyExcludeMode.labels())
            self.assertIn("자유형", TransparencyExcludeMode.labels())
            self.assertNotIn("외곽 선택", TransparencySelectionMode.labels())
        finally:
            dpg.destroy_context()

    def test_area_exclude_drag_start_is_not_restarted(self) -> None:
        app = AssetEditorApplication()
        app.transparency_selection.mode = TransparencySelectionMode.AREA
        app.area_exclude_enabled = True
        app.area_exclude_mode = TransparencyExcludeMode.RECTANGLE
        app._update_selection_overlay = lambda: None

        self.assertTrue(app._start_area_exclude_drag((1, 1)))
        self.assertTrue(app._start_area_exclude_drag((5, 5)))

        self.assertEqual(app.transparency_selection.drag_start, (1, 1))
        self.assertEqual(app.transparency_selection.drag_end, (1, 1))

    def test_color_selection_drag_collects_rectangle_colors(self) -> None:
        app = AssetEditorApplication()
        app.document.working_image = Image.new("RGBA", (3, 3), (9, 9, 9, 255))
        app.document.working_image.putpixel((0, 0), (10, 0, 0, 255))
        app.document.working_image.putpixel((1, 0), (0, 20, 0, 255))
        app.document.working_image.putpixel((0, 1), (10, 0, 0, 255))
        app.transparency_selection.set_mode(TransparencySelectionMode.COLOR)
        app.transparency_selection.start_drag((0, 0))
        app.transparency_selection.update_drag((1, 1))
        app._clear_selection_overlay = lambda: None
        app._update_selection_summary = lambda: None
        app._set_status = lambda _message: None

        app._finish_color_selection()
        selected_colors = app.transparency_selection.selected_colors

        self.assertEqual(
            selected_colors,
            {(10, 0, 0), (0, 20, 0), (9, 9, 9)},
        )
        self.assertEqual(
            app.transparency_selection.rectangle,
            ImageSelectionRectangle(0, 0, 1, 1),
        )

    def test_color_selection_drag_transparency_applies_all_colors(self) -> None:
        app = AssetEditorApplication()
        app.document.working_image = Image.new("RGBA", (3, 1), (9, 9, 9, 255))
        app.document.working_image.putpixel((0, 0), (10, 0, 0, 255))
        app.document.working_image.putpixel((1, 0), (0, 20, 0, 255))
        app.transparency_selection.set_mode(TransparencySelectionMode.COLOR)
        app.transparency_selection.start_drag((0, 0))
        app.transparency_selection.update_drag((1, 0))
        app._clear_selection_overlay = lambda: None
        app._update_selection_summary = lambda: None
        app._apply_preview = lambda: None
        app._set_status = lambda _message: None

        app._finish_color_selection()
        app._apply_transparency_selection()

        self.assertEqual(app.document.working_image.getpixel((0, 0))[3], 0)
        self.assertEqual(app.document.working_image.getpixel((1, 0))[3], 0)
        self.assertEqual(app.document.working_image.getpixel((2, 0))[3], 255)

    def test_preview_area_supports_horizontal_scrollbar(self) -> None:
        app = AssetEditorApplication()
        dpg.create_context()
        try:
            with dpg.window(tag="test_window"):
                app._build_preview_area()

            self.assertTrue(
                dpg.get_item_configuration(
                    app.preview_area_tag,
                )["horizontal_scrollbar"],
            )
        finally:
            dpg.destroy_context()

    def test_preview_pan_drag_updates_view_scroll(self) -> None:
        app = AssetEditorApplication()
        mouse_positions = [(10.0, 10.0)]
        recorded_scroll_positions = []

        app._is_preview_pan_start_active = lambda: True
        app._get_mouse_display_position = lambda: mouse_positions[-1]
        app._get_scroll_position = lambda _tag: (100.0, 50.0)
        app._set_scroll_position = (
            lambda tag, position: recorded_scroll_positions.append(
                (tag, position),
            )
        )
        app._update_selection_overlay = lambda: None

        self.assertTrue(app._start_preview_pan())
        mouse_positions.append((30.0, 5.0))

        self.assertTrue(app._update_preview_pan())
        self.assertEqual(
            recorded_scroll_positions,
            [(app.preview_area_tag, (80.0, 55.0))],
        )
        self.assertTrue(app._finish_preview_pan())
        self.assertFalse(app.preview_pan_active)

    def test_preview_pan_scroll_clamp_keeps_other_axis_movable(self) -> None:
        app = AssetEditorApplication()

        scroll_position = app._calculate_pan_scroll_position(
            (5.0, 50.0),
            (10.0, 10.0),
            (30.0, 5.0),
        )
        clamped_position = app._clamp_scroll_position(
            scroll_position,
            (100.0, 60.0),
        )

        self.assertEqual(scroll_position, (-15.0, 55.0))
        self.assertEqual(clamped_position, (0.0, 55.0))

    def test_preview_pan_skips_overlay_when_scroll_is_blocked(self) -> None:
        app = AssetEditorApplication()
        mouse_positions = [(10.0, 10.0)]
        overlay_updates = []

        app._is_preview_pan_start_active = lambda: True
        app._get_mouse_display_position = lambda: mouse_positions[-1]
        app._get_scroll_position = lambda _tag: (0.0, 55.0)
        app._set_scroll_position = lambda _tag, _position: False
        app._update_selection_overlay = lambda: overlay_updates.append(True)

        self.assertTrue(app._start_preview_pan())
        mouse_positions.append((30.0, 5.0))

        self.assertTrue(app._update_preview_pan())
        self.assertEqual(overlay_updates, [])

    def test_scroll_axis_changes_ignore_same_position(self) -> None:
        app = AssetEditorApplication()

        self.assertEqual(
            app._get_scroll_axis_changes((0.0, 55.0), (0.0, 55.0)),
            (False, False),
        )
        self.assertEqual(
            app._get_scroll_axis_changes((0.0, 55.0), (0.0, 58.0)),
            (False, True),
        )

    def test_area_exclude_method_control_tracks_exclude_enabled(self) -> None:
        app = AssetEditorApplication()
        dpg.create_context()
        try:
            with dpg.window(tag="test_window"):
                app._build_controls()

            app.transparency_selection.set_mode(TransparencySelectionMode.COLOR)
            app.area_exclude_enabled = True
            app._sync_area_exclude_state()
            self.assertFalse(app.area_exclude_enabled)
            self.assertFalse(
                dpg.get_item_configuration(
                    app.area_exclude_check_tag,
                )["enabled"],
            )
            self.assertFalse(
                dpg.get_item_configuration(
                    app.area_exclude_mode_combo_tag,
                )["enabled"],
            )

            app.transparency_selection.set_mode(TransparencySelectionMode.AREA)
            app.area_exclude_enabled = False
            app._sync_area_exclude_state()
            self.assertFalse(
                dpg.get_item_configuration(
                    app.area_exclude_mode_combo_tag,
                )["enabled"],
            )

            app._on_area_exclude_mode_changed(None, True)
            self.assertTrue(app.area_exclude_enabled)
            self.assertTrue(
                dpg.get_item_configuration(
                    app.area_exclude_mode_combo_tag,
                )["enabled"],
            )

            app._on_area_exclude_mode_changed(None, False)
            self.assertFalse(app.area_exclude_enabled)
            self.assertFalse(
                dpg.get_item_configuration(
                    app.area_exclude_mode_combo_tag,
                )["enabled"],
            )
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
