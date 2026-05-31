# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image, ImageOps


APP_TITLE = "assetEditor"
DEFAULT_CANVAS_WIDTH = 960
DEFAULT_CANVAS_HEIGHT = 640
DEFAULT_FONT_SIZE = 18
KOREAN_FONT_PATHS = (
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("C:/Windows/Fonts/NotoSansKR-Regular.otf"),
)


@dataclass
class ImageDocument:
    source_path: Path | None = None
    original_image: Image.Image | None = None
    preview_image: Image.Image | None = None

    def load(self, path: str) -> None:
        image_path = Path(path)
        self.original_image = Image.open(image_path).convert("RGBA")
        self.preview_image = self.original_image.copy()
        self.source_path = image_path

    def save(self, path: str) -> None:
        if self.preview_image is None:
            raise ValueError("저장할 이미지가 없습니다.")

        save_path = Path(path)
        image = self.preview_image
        if save_path.suffix.lower() in {".jpg", ".jpeg"}:
            image = image.convert("RGB")
        image.save(save_path)

    def has_image(self) -> bool:
        return self.original_image is not None and self.preview_image is not None


@dataclass
class PreviewOptions:
    grayscale: bool = False
    edge_preview: bool = False
    zoom: float = 1.0

    def reset(self) -> None:
        self.grayscale = False
        self.edge_preview = False
        self.zoom = 1.0


class ImagePreviewProcessor:
    def apply(self, image: Image.Image, options: PreviewOptions) -> Image.Image:
        preview = image.copy().convert("RGBA")

        if options.grayscale:
            preview = ImageOps.grayscale(preview).convert("RGBA")

        if options.edge_preview:
            rgb_array = np.array(preview.convert("RGB"))
            gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
            edge_array = cv2.Canny(gray_array, 80, 160)
            preview = Image.fromarray(edge_array).convert("RGBA")

        return preview

    def resize_for_canvas(
        self,
        image: Image.Image,
        zoom: float,
        canvas_width: int = DEFAULT_CANVAS_WIDTH,
        canvas_height: int = DEFAULT_CANVAS_HEIGHT,
    ) -> Image.Image:
        max_width = max(1, int(canvas_width * zoom))
        max_height = max(1, int(canvas_height * zoom))
        preview = image.convert("RGBA").copy()
        preview.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return preview

    def to_texture_data(self, image: Image.Image) -> list[float]:
        rgba_array = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255.0
        return rgba_array.ravel().tolist()


class KoreanFontManager:
    def __init__(
        self,
        font_paths: tuple[Path, ...] = KOREAN_FONT_PATHS,
        font_size: int = DEFAULT_FONT_SIZE,
    ) -> None:
        self.font_paths = font_paths
        self.font_size = font_size
        self.font_tag = "korean_default_font"

    def bind(self) -> None:
        font_path = self._find_font_path()
        if font_path is None:
            return

        with dpg.font_registry():
            dpg.add_font(str(font_path), self.font_size, tag=self.font_tag)

        dpg.bind_font(self.font_tag)

    def _find_font_path(self) -> Path | None:
        for font_path in self.font_paths:
            if font_path.exists():
                return font_path
        return None


class AssetEditorApplication:
    def __init__(self) -> None:
        self.document = ImageDocument()
        self.options = PreviewOptions()
        self.processor = ImagePreviewProcessor()
        self.font_manager = KoreanFontManager()
        self.texture_tag = "preview_texture"
        self.preview_image_tag = "preview_image"
        self.empty_preview_tag = "empty_preview_text"
        self.status_tag = "status_text"
        self.metadata_tag = "metadata_text"
        self.canvas_group_tag = "canvas_group"

    def run(self) -> None:
        self._build_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _build_ui(self) -> None:
        dpg.create_context()
        self.font_manager.bind()
        self._build_file_dialogs()

        with dpg.window(tag="primary_window", label=APP_TITLE):
            self._build_menu()
            with dpg.group(horizontal=True):
                self._build_controls()
                self._build_preview_area()
            dpg.add_separator()
            dpg.add_text("준비됨", tag=self.status_tag)

        dpg.create_viewport(title=APP_TITLE, width=1280, height=820)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary_window", True)

    def _build_file_dialogs(self) -> None:
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self._on_file_open,
            tag="open_dialog",
            width=720,
            height=420,
        ):
            dpg.add_file_extension(
                "이미지 파일 (*.png *.jpg *.jpeg *.webp *.bmp)"
                "{.png,.jpg,.jpeg,.webp,.bmp}"
            )
            dpg.add_file_extension(".*")

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self._on_file_save,
            tag="save_dialog",
            width=720,
            height=420,
            default_filename="preview.png",
        ):
            dpg.add_file_extension(".png", color=(80, 180, 120, 255))
            dpg.add_file_extension(".jpg", color=(120, 180, 240, 255))
            dpg.add_file_extension(".webp", color=(220, 180, 80, 255))

    def _build_menu(self) -> None:
        with dpg.menu_bar():
            with dpg.menu(label="파일"):
                dpg.add_menu_item(
                    label="열기",
                    callback=lambda: dpg.show_item("open_dialog"),
                )
                dpg.add_menu_item(
                    label="다른 이름으로 저장",
                    callback=lambda: dpg.show_item("save_dialog"),
                )
            with dpg.menu(label="편집"):
                dpg.add_menu_item(label="초기화", callback=self._reset_preview)

    def _build_controls(self) -> None:
        with dpg.child_window(width=300, autosize_y=True, border=True):
            dpg.add_text("도구")
            dpg.add_separator()
            self._add_button_with_help(
                label="이미지 열기",
                tooltip="편집하거나 확인할 이미지 파일을 불러옵니다.",
                callback=lambda: dpg.show_item("open_dialog"),
            )
            self._add_button_with_help(
                label="다른 이름으로 저장",
                tooltip="현재 프리뷰 결과를 새 이미지 파일로 저장합니다.",
                callback=lambda: dpg.show_item("save_dialog"),
            )
            self._add_button_with_help(
                label="초기화",
                tooltip="프리뷰 옵션을 기본값으로 되돌립니다.",
                callback=self._reset_preview,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("프리뷰")
            self._add_checkbox_with_help(
                label="그레이스케일",
                tag="grayscale_check",
                tooltip="이미지를 흑백으로 변환해 색상 없이 명암만 확인합니다.",
                callback=self._on_grayscale_changed,
            )
            self._add_checkbox_with_help(
                label="엣지 프리뷰",
                tag="edge_check",
                tooltip=(
                    "OpenCV Canny 알고리즘으로 이미지의 윤곽선만 "
                    "추출해 보여줍니다."
                ),
                callback=self._on_edge_preview_changed,
            )
            self._add_slider_with_help(
                label="확대",
                tag="zoom_slider",
                tooltip="프리뷰 표시 크기를 확대하거나 축소합니다.",
                default_value=1.0,
                min_value=0.25,
                max_value=3.0,
                callback=self._on_zoom_changed,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("이미지 정보")
            dpg.add_text("로드된 이미지 없음", tag=self.metadata_tag, wrap=270)

    def _add_button_with_help(self, label: str, tooltip: str, callback) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(label=label, width=250, callback=callback)
            self._add_help_icon(tooltip)

    def _add_checkbox_with_help(
        self,
        label: str,
        tag: str,
        tooltip: str,
        callback,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label=label, tag=tag, callback=callback)
            self._add_help_icon(tooltip)

    def _add_slider_with_help(
        self,
        label: str,
        tag: str,
        tooltip: str,
        default_value: float,
        min_value: float,
        max_value: float,
        callback,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text(label)
            self._add_help_icon(tooltip)
        dpg.add_slider_float(
            tag=tag,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            callback=callback,
            width=-1,
        )

    def _add_help_icon(self, tooltip: str) -> None:
        help_item = dpg.add_text("?", color=(120, 170, 255, 255))
        with dpg.tooltip(help_item):
            dpg.add_text(tooltip, wrap=260)

    def _build_preview_area(self) -> None:
        with dpg.child_window(autosize_x=True, autosize_y=True, border=True):
            dpg.add_text("프리뷰")
            dpg.add_separator()
            with dpg.group(tag=self.canvas_group_tag):
                dpg.add_text(
                    "이미지를 열면 프리뷰가 표시됩니다.",
                    tag=self.empty_preview_tag,
                )

    def _on_file_open(self, _sender, app_data) -> None:
        selections = app_data.get("selections", {})
        if not selections:
            return

        selected_path = next(iter(selections.values()))
        try:
            self.document.load(selected_path)
            self.options.reset()
            self._sync_controls()
            self._apply_preview()
            self._set_status(f"이미지를 열었습니다: {selected_path}")
        except Exception as exc:
            self._set_status(f"이미지 열기 실패: {exc}")

    def _on_file_save(self, _sender, app_data) -> None:
        file_path = app_data.get("file_path_name")
        if not file_path:
            return

        try:
            self.document.save(file_path)
            self._set_status(f"이미지를 저장했습니다: {file_path}")
        except Exception as exc:
            self._set_status(f"이미지 저장 실패: {exc}")

    def _on_grayscale_changed(self, _sender, app_data) -> None:
        self.options.grayscale = bool(app_data)
        self._apply_preview()

    def _on_edge_preview_changed(self, _sender, app_data) -> None:
        self.options.edge_preview = bool(app_data)
        self._apply_preview()

    def _on_zoom_changed(self, _sender, app_data) -> None:
        self.options.zoom = float(app_data)
        self._refresh_preview_texture()

    def _reset_preview(self) -> None:
        self.options.reset()
        self._sync_controls()
        self._apply_preview()

    def _sync_controls(self) -> None:
        control_values = {
            "grayscale_check": self.options.grayscale,
            "edge_check": self.options.edge_preview,
            "zoom_slider": self.options.zoom,
        }

        for tag, value in control_values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

    def _apply_preview(self) -> None:
        if self.document.original_image is None:
            return

        self.document.preview_image = self.processor.apply(
            self.document.original_image,
            self.options,
        )
        self._refresh_preview_texture()

    def _refresh_preview_texture(self) -> None:
        if self.document.preview_image is None:
            return

        preview = self.processor.resize_for_canvas(
            self.document.preview_image,
            self.options.zoom,
        )
        width, height = preview.size
        texture_data = self.processor.to_texture_data(preview)

        self._clear_preview_items()

        with dpg.texture_registry(show=False):
            dpg.add_static_texture(
                width,
                height,
                texture_data,
                tag=self.texture_tag,
            )

        dpg.add_image(
            self.texture_tag,
            parent=self.canvas_group_tag,
            tag=self.preview_image_tag,
        )
        self._update_metadata()

    def _clear_preview_items(self) -> None:
        for tag in (
            self.empty_preview_tag,
            self.preview_image_tag,
            self.texture_tag,
        ):
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)

    def _update_metadata(self) -> None:
        if not self.document.has_image():
            dpg.set_value(self.metadata_tag, "로드된 이미지 없음")
            return

        source_name = (
            self.document.source_path.name
            if self.document.source_path
            else "이름 없음"
        )
        original_width, original_height = self.document.original_image.size
        preview_width, preview_height = self.document.preview_image.size
        mode = "엣지 프리뷰" if self.options.edge_preview else "일반 프리뷰"

        dpg.set_value(
            self.metadata_tag,
            f"{source_name}\n"
            f"원본: {original_width} x {original_height}\n"
            f"프리뷰: {preview_width} x {preview_height}\n"
            f"모드: {mode}",
        )

    def _set_status(self, message: str) -> None:
        dpg.set_value(self.status_tag, message)


if __name__ == "__main__":
    AssetEditorApplication().run()
