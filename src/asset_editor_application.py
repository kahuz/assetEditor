# -*- coding: utf-8 -*-
from __future__ import annotations

import dearpygui.dearpygui as dpg

from common import APP_TITLE
from document.image_document import ImageDocument
from fonts.korean_font_manager import KoreanFontManager
from history.image_history_cache import ImageHistoryCache
from preview.image_preview_processor import ImagePreviewProcessor
from preview.preview_options import PreviewOptions
from ui.help_widget import HelpWidget


class AssetEditorApplication:
    def __init__(self) -> None:
        self.document = ImageDocument()
        self.options = PreviewOptions()
        self.processor = ImagePreviewProcessor()
        self.font_manager = KoreanFontManager()
        self.history_cache = ImageHistoryCache()
        self.help_widget = HelpWidget()
        self.texture_tag = "preview_texture"
        self.preview_image_tag = "preview_image"
        self.empty_preview_tag = "empty_preview_text"
        self.status_tag = "status_text"
        self.metadata_tag = "metadata_text"
        self.canvas_group_tag = "canvas_group"
        self.history_combo_tag = "history_combo"
        self.zoom_slider_enabled = False
        self.zoom_slider_enabled_tag = "zoom_slider_enabled_check"

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
            with dpg.menu(label="히스토리"):
                dpg.add_menu_item(
                    label="선택한 히스토리 열기",
                    callback=self._open_selected_history,
                )
                dpg.add_menu_item(
                    label="히스토리 비우기",
                    callback=self._clear_history,
                )

    def _build_controls(self) -> None:
        with dpg.child_window(width=300, autosize_y=True, border=True):
            dpg.add_text("도구")
            dpg.add_separator()
            self.help_widget.add_button(
                label="이미지 열기",
                tooltip="편집하거나 확인할 이미지 파일을 불러옵니다.",
                callback=lambda: dpg.show_item("open_dialog"),
            )
            self.help_widget.add_button(
                label="다른 이름으로 저장",
                tooltip="현재 프리뷰 결과를 새 이미지 파일로 저장합니다.",
                callback=lambda: dpg.show_item("save_dialog"),
            )
            self.help_widget.add_button(
                label="초기화",
                tooltip="프리뷰 옵션을 기본값으로 되돌립니다.",
                callback=self._reset_preview,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("최근 이미지")
            self.help_widget.add_combo(
                tag=self.history_combo_tag,
                tooltip=(
                    "이전에 열었던 이미지 경로입니다. "
                    "cache 파일에서 앱 시작 시 자동으로 불러옵니다."
                ),
                items=self.history_cache.history,
            )
            self.help_widget.add_button(
                label="히스토리 열기",
                tooltip="최근 이미지 목록에서 선택한 파일을 다시 엽니다.",
                callback=self._open_selected_history,
            )
            self.help_widget.add_button(
                label="히스토리 비우기",
                tooltip="저장된 최근 이미지 cache를 비웁니다.",
                callback=self._clear_history,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("프리뷰")
            self.help_widget.add_checkbox(
                label="그레이스케일",
                tag="grayscale_check",
                tooltip="이미지를 흑백으로 변환해 색상 없이 명암만 확인합니다.",
                callback=self._on_grayscale_changed,
            )
            self.help_widget.add_checkbox(
                label="엣지 프리뷰",
                tag="edge_check",
                tooltip=(
                    "OpenCV Canny 알고리즘으로 이미지의 윤곽선만 "
                    "추출해 보여줍니다."
                ),
                callback=self._on_edge_preview_changed,
            )
            self.help_widget.add_lockable_slider(
                label="확대",
                check_tag=self.zoom_slider_enabled_tag,
                slider_tag="zoom_slider",
                tooltip=(
                    "체크하면 확대 배율을 조정할 수 있습니다. "
                    "체크를 해제해도 현재 확대 값은 유지됩니다."
                ),
                default_value=1.0,
                min_value=0.25,
                max_value=3.0,
                check_callback=self._on_zoom_slider_enabled_changed,
                slider_callback=self._on_zoom_changed,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("이미지 정보")
            dpg.add_text("로드된 이미지 없음", tag=self.metadata_tag, wrap=270)

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
            self.history_cache.add(selected_path)
            self._refresh_history_items()
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

    def _on_zoom_slider_enabled_changed(self, _sender, app_data) -> None:
        self.zoom_slider_enabled = bool(app_data)
        self._sync_zoom_slider_state()

    def _on_zoom_changed(self, _sender, app_data) -> None:
        self.options.zoom = float(app_data)
        self._refresh_preview_texture()

    def _open_selected_history(self) -> None:
        selected_path = dpg.get_value(self.history_combo_tag)
        if not selected_path:
            self._set_status("선택된 히스토리가 없습니다.")
            return

        try:
            self.document.load(selected_path)
            self.history_cache.add(selected_path)
            self._refresh_history_items()
            self.options.reset()
            self._sync_controls()
            self._apply_preview()
            self._set_status(f"히스토리에서 이미지를 열었습니다: {selected_path}")
        except Exception as exc:
            self._set_status(f"히스토리 이미지 열기 실패: {exc}")

    def _clear_history(self) -> None:
        self.history_cache.clear()
        self._refresh_history_items()
        self._set_status("이미지 히스토리를 비웠습니다.")

    def _reset_preview(self) -> None:
        self.options.reset()
        self._sync_controls()
        self._apply_preview()

    def _refresh_history_items(self) -> None:
        if not dpg.does_item_exist(self.history_combo_tag):
            return

        dpg.configure_item(
            self.history_combo_tag,
            items=self.history_cache.history,
        )
        selected_value = (
            self.history_cache.history[0]
            if self.history_cache.history
            else ""
        )
        dpg.set_value(self.history_combo_tag, selected_value)

    def _sync_controls(self) -> None:
        control_values = {
            "grayscale_check": self.options.grayscale,
            "edge_check": self.options.edge_preview,
            self.zoom_slider_enabled_tag: self.zoom_slider_enabled,
            "zoom_slider": self.options.zoom,
        }

        for tag, value in control_values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

        self._sync_zoom_slider_state()

    def _sync_zoom_slider_state(self) -> None:
        if dpg.does_item_exist("zoom_slider"):
            dpg.configure_item(
                "zoom_slider",
                enabled=self.zoom_slider_enabled,
            )

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
