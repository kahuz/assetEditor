# -*- coding: utf-8 -*-
from __future__ import annotations

import dearpygui.dearpygui as dpg

from common import APP_TITLE, ZOOM_MAX, ZOOM_MIN, ZOOM_WHEEL_STEP
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
        self.primary_window_tag = "primary_window"
        self.texture_tag = "preview_texture"
        self.preview_image_tag = "preview_image"
        self.empty_preview_tag = "empty_preview_text"
        self.status_tag = "status_text"
        self.metadata_tag = "metadata_text"
        self.open_dialog_tag = "open_dialog"
        self.save_dialog_tag = "save_dialog"
        self.canvas_group_tag = "canvas_group"
        self.preview_area_tag = "preview_area"
        self.history_combo_tag = "history_combo"
        self.grayscale_check_tag = "grayscale_check"
        self.edge_check_tag = "edge_check"
        self.zoom_slider_tag = "zoom_slider"
        self.zoom_slider_enabled = False
        self.zoom_slider_enabled_tag = "zoom_slider_enabled_check"
        self.wheel_scroll_blocked = False

    def run(self) -> None:
        self._build_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _build_ui(self) -> None:
        dpg.create_context()
        self.font_manager.bind()
        self._build_file_dialogs()
        self._build_global_handlers()

        with dpg.window(
            tag=self.primary_window_tag,
            label=APP_TITLE,
        ):
            self._build_menu()
            with dpg.group(horizontal=True):
                self._build_controls()
                self._build_preview_area()
            dpg.add_separator()
            dpg.add_text("준비됨", tag=self.status_tag)

        dpg.create_viewport(title=APP_TITLE, width=1280, height=820)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.primary_window_tag, True)
        self._set_wheel_scroll_blocked(False)

    def _build_file_dialogs(self) -> None:
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self._on_file_open,
            tag=self.open_dialog_tag,
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
            tag=self.save_dialog_tag,
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
                    callback=lambda: dpg.show_item(self.open_dialog_tag),
                )
                dpg.add_menu_item(
                    label="다른 이름으로 저장",
                    callback=lambda: dpg.show_item(self.save_dialog_tag),
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
                callback=lambda: dpg.show_item(self.open_dialog_tag),
            )
            self.help_widget.add_button(
                label="다른 이름으로 저장",
                tooltip="현재 프리뷰 결과를 새 이미지 파일로 저장합니다.",
                callback=lambda: dpg.show_item(self.save_dialog_tag),
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
                tag=self.grayscale_check_tag,
                tooltip="이미지를 흑백으로 변환해 색상 없이 명암만 확인합니다.",
                callback=self._on_grayscale_changed,
            )
            self.help_widget.add_checkbox(
                label="엣지 프리뷰",
                tag=self.edge_check_tag,
                tooltip=(
                    "OpenCV Canny 알고리즘으로 이미지의 윤곽선만 "
                    "추출해 보여줍니다."
                ),
                callback=self._on_edge_preview_changed,
            )
            self.help_widget.add_lockable_slider(
                label="확대",
                check_tag=self.zoom_slider_enabled_tag,
                slider_tag=self.zoom_slider_tag,
                tooltip=(
                    "체크하면 확대 배율을 조정할 수 있습니다. "
                    "프리뷰 영역에서는 마우스 휠로도 조정할 수 있습니다. "
                    "체크를 해제해도 현재 확대 값은 유지됩니다."
                ),
                default_value=1.0,
                min_value=ZOOM_MIN,
                max_value=ZOOM_MAX,
                check_callback=self._on_zoom_slider_enabled_changed,
                slider_callback=self._on_zoom_changed,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("이미지 정보")
            dpg.add_text("로드된 이미지 없음", tag=self.metadata_tag, wrap=270)

    def _build_preview_area(self) -> None:
        with dpg.child_window(
            autosize_x=True,
            autosize_y=True,
            border=True,
            tag=self.preview_area_tag,
        ):
            dpg.add_text("프리뷰")
            dpg.add_separator()
            with dpg.group(tag=self.canvas_group_tag):
                dpg.add_text(
                    "이미지를 열면 프리뷰가 표시됩니다.",
                    tag=self.empty_preview_tag,
                )

    def _build_global_handlers(self) -> None:
        with dpg.handler_registry():
            dpg.add_mouse_move_handler(callback=self._on_mouse_move)
            dpg.add_mouse_wheel_handler(callback=self._on_mouse_wheel)

    def _on_file_open(self, _sender, app_data) -> None:
        selections = app_data.get("selections", {})
        if not selections:
            return

        selected_path = next(iter(selections.values()))
        self._open_image_path(
            selected_path,
            success_message=f"이미지를 열었습니다: {selected_path}",
            failure_prefix="이미지 열기 실패",
        )

    def _open_image_path(
        self,
        path: str,
        success_message: str,
        failure_prefix: str,
    ) -> None:
        try:
            self.document.load(path)
            self.history_cache.add(path)
            self._refresh_history_items()
            self._reset_options_and_refresh()
            self._set_status(success_message)
        except Exception as exc:
            self._set_status(f"{failure_prefix}: {exc}")

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

    def _on_mouse_wheel(self, _sender, app_data) -> None:
        if not self._sync_wheel_scroll_block():
            return

        scroll_position = self._get_primary_scroll_position()
        self._change_zoom_by_wheel_delta(float(app_data))
        self._restore_primary_scroll_position(scroll_position)

    def _on_mouse_move(self, _sender, _app_data) -> None:
        self._sync_wheel_scroll_block()

    def _sync_wheel_scroll_block(self) -> bool:
        zoom_active = self._is_preview_wheel_zoom_active()
        self._set_wheel_scroll_blocked(zoom_active)
        return zoom_active

    def _is_preview_wheel_zoom_active(self) -> bool:
        if not self.zoom_slider_enabled:
            return False
        if self.document.preview_image is None:
            return False
        if not dpg.does_item_exist(self.preview_area_tag):
            return False
        return bool(dpg.is_item_hovered(self.preview_area_tag))

    def _set_wheel_scroll_blocked(self, blocked: bool) -> None:
        if self.wheel_scroll_blocked == blocked:
            return

        self.wheel_scroll_blocked = blocked
        for tag in (self.primary_window_tag, self.preview_area_tag):
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, no_scroll_with_mouse=blocked)

    def _change_zoom_by_wheel_delta(self, wheel_delta: float) -> None:
        next_zoom = self.options.zoom + (wheel_delta * ZOOM_WHEEL_STEP)
        self.options.zoom = max(ZOOM_MIN, min(ZOOM_MAX, next_zoom))

        if dpg.does_item_exist(self.zoom_slider_tag):
            dpg.set_value(self.zoom_slider_tag, self.options.zoom)

        self._refresh_preview_texture()

    def _get_primary_scroll_position(self) -> tuple[float, float]:
        return (
            dpg.get_x_scroll(self.primary_window_tag),
            dpg.get_y_scroll(self.primary_window_tag),
        )

    def _restore_primary_scroll_position(
        self,
        scroll_position: tuple[float, float],
    ) -> None:
        self._set_primary_scroll_position(scroll_position)
        next_frame = dpg.get_frame_count() + 1
        dpg.set_frame_callback(
            next_frame,
            callback=lambda: self._set_primary_scroll_position(
                scroll_position,
            ),
        )

    def _set_primary_scroll_position(
        self,
        scroll_position: tuple[float, float],
    ) -> None:
        x_position, y_position = scroll_position
        dpg.set_x_scroll(self.primary_window_tag, x_position)
        dpg.set_y_scroll(self.primary_window_tag, y_position)

    def _open_selected_history(self) -> None:
        selected_path = dpg.get_value(self.history_combo_tag)
        if not selected_path:
            self._set_status("선택된 히스토리가 없습니다.")
            return

        self._open_image_path(
            selected_path,
            success_message=(
                f"히스토리에서 이미지를 열었습니다: {selected_path}"
            ),
            failure_prefix="히스토리 이미지 열기 실패",
        )

    def _clear_history(self) -> None:
        self.history_cache.clear()
        self._refresh_history_items()
        self._set_status("이미지 히스토리를 비웠습니다.")

    def _reset_preview(self) -> None:
        self._reset_options_and_refresh()

    def _reset_options_and_refresh(self) -> None:
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
            self.grayscale_check_tag: self.options.grayscale,
            self.edge_check_tag: self.options.edge_preview,
            self.zoom_slider_enabled_tag: self.zoom_slider_enabled,
            self.zoom_slider_tag: self.options.zoom,
        }

        for tag, value in control_values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

        self._sync_zoom_slider_state()

    def _sync_zoom_slider_state(self) -> None:
        if dpg.does_item_exist(self.zoom_slider_tag):
            dpg.configure_item(
                self.zoom_slider_tag,
                enabled=self.zoom_slider_enabled,
            )
        self._sync_wheel_scroll_block()

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
