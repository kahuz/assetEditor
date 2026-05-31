# -*- coding: utf-8 -*-
from __future__ import annotations

import dearpygui.dearpygui as dpg

from common import (
    APP_TITLE,
    ZOOM_MAX,
    ZOOM_MIN,
    ZOOM_WHEEL_STEP,
)
from document.image_document import ImageDocument
from fonts.korean_font_manager import KoreanFontManager
from history.image_history_cache import ImageHistoryCache
from preview.image_preview_processor import ImagePreviewProcessor
from preview.preview_options import PreviewOptions
from transparency.image_transparency_processor import ImageTransparencyProcessor
from transparency.transparency_selection import (
    ImageSelectionRectangle,
    TransparencyExcludeMode,
    TransparencySelection,
    TransparencySelectionMode,
)
from ui.help_widget import HelpWidget


class AssetEditorApplication:
    def __init__(self) -> None:
        self.document = ImageDocument()
        self.options = PreviewOptions()
        self.processor = ImagePreviewProcessor()
        self.transparency_processor = ImageTransparencyProcessor()
        self.transparency_selection = TransparencySelection()
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
        self.transparency_mode_combo_tag = "transparency_mode_combo"
        self.area_exclude_check_tag = "area_exclude_check"
        self.area_exclude_mode_combo_tag = "area_exclude_mode_combo"
        self.transparency_selection_summary_tag = "transparency_selection_text"
        self.selection_overlay_tag = "selection_overlay"
        self.selection_rectangle_tag = "selection_rectangle"
        self.selection_freeform_tag = "selection_freeform"
        self.zoom_slider_tag = "zoom_slider"
        self.zoom_slider_enabled = False
        self.area_exclude_enabled = False
        self.area_exclude_mode = TransparencyExcludeMode.DETAIL
        self.left_mouse_active = False
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
        dpg.add_viewport_drawlist(tag=self.selection_overlay_tag, front=True)
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
                tooltip="현재 투명 처리 결과를 새 이미지 파일로 저장합니다.",
                callback=lambda: dpg.show_item(self.save_dialog_tag),
            )
            self.help_widget.add_button(
                label="초기화",
                tooltip="View 옵션과 투명 처리 결과를 원본 상태로 되돌립니다.",
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
            dpg.add_text("View")
            self.help_widget.add_checkbox(
                label="그레이스케일",
                tag=self.grayscale_check_tag,
                tooltip="이미지를 흑백으로 변환해 색상 없이 명암만 확인합니다.",
                callback=self._on_grayscale_changed,
            )
            self.help_widget.add_checkbox(
                label="엣지 View",
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
                    "View 영역에서는 마우스 휠로도 조정할 수 있습니다. "
                    "체크를 해제해도 현재 확대 값은 유지됩니다."
                ),
                default_value=1.0,
                min_value=ZOOM_MIN,
                max_value=ZOOM_MAX,
                check_callback=self._on_zoom_slider_enabled_changed,
                slider_callback=self._on_zoom_changed,
            )

            dpg.add_spacer(height=10)
            dpg.add_text("배경 투명 처리")
            with dpg.group(horizontal=True):
                dpg.add_combo(
                    TransparencySelectionMode.labels(),
                    tag=self.transparency_mode_combo_tag,
                    width=250,
                    default_value=self.transparency_selection.mode,
                    callback=self._on_transparency_mode_changed,
                )
                self.help_widget.add_icon(
                    "컬러, 사각형, 클릭 영역 기준으로 투명 처리 대상을 선택합니다.",
                )
            self.help_widget.add_checkbox(
                label="영역 제외 모드",
                tag=self.area_exclude_check_tag,
                tooltip=(
                    "영역 선택 상태에서 켜면 선택 영역 일부를 제외합니다."
                ),
                callback=self._on_area_exclude_mode_changed,
            )
            with dpg.group(horizontal=True):
                dpg.add_combo(
                    TransparencyExcludeMode.labels(),
                    tag=self.area_exclude_mode_combo_tag,
                    width=250,
                    default_value=self.area_exclude_mode,
                    callback=self._on_area_exclude_method_changed,
                )
                self.help_widget.add_icon(
                    "세부 영역, 사각형, 자유형 중 제외 방식을 선택합니다.",
                )
            self.help_widget.add_button(
                label="투명 처리 적용",
                tooltip="현재 선택한 컬러 또는 영역 기준으로 alpha를 0으로 만듭니다.",
                callback=self._apply_transparency_selection,
            )
            self.help_widget.add_button(
                label="선택 해제",
                tooltip="투명 처리 선택 상태를 비웁니다.",
                callback=self._clear_transparency_selection,
            )
            dpg.add_text(
                "선택 없음",
                tag=self.transparency_selection_summary_tag,
                wrap=270,
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
            dpg.add_text("View")
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
            dpg.add_mouse_down_handler(
                button=dpg.mvMouseButton_Left,
                callback=self._on_mouse_down,
            )
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Left,
                threshold=0.0,
                callback=self._on_mouse_drag,
            )
            dpg.add_mouse_release_handler(
                button=dpg.mvMouseButton_Left,
                callback=self._on_mouse_release,
            )

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

    def _on_transparency_mode_changed(self, _sender, app_data) -> None:
        self.transparency_selection.set_mode(str(app_data))
        if self.transparency_selection.mode != TransparencySelectionMode.AREA:
            self.area_exclude_enabled = False
        self._clear_selection_overlay()
        self._sync_area_exclude_state()
        self._update_selection_summary()
        self._apply_preview()

    def _on_area_exclude_mode_changed(self, _sender, app_data) -> None:
        if self.transparency_selection.mode != TransparencySelectionMode.AREA:
            self.area_exclude_enabled = False
            self._sync_area_exclude_state()
            return

        self.area_exclude_enabled = bool(app_data)
        self.transparency_selection.clear_drag_state()
        self._clear_selection_overlay()
        self._sync_area_exclude_state()
        self._update_selection_summary()

    def _on_area_exclude_method_changed(self, _sender, app_data) -> None:
        if str(app_data) not in TransparencyExcludeMode.labels():
            return

        self.area_exclude_mode = str(app_data)
        self.transparency_selection.clear_drag_state()
        self._clear_selection_overlay()
        self._update_selection_summary()

    def _apply_transparency_selection(self) -> None:
        if self.document.working_image is None:
            self._set_status("투명 처리할 이미지가 없습니다.")
            return

        mode = self.transparency_selection.mode
        if mode == TransparencySelectionMode.AREA:
            area_mask = self.transparency_selection.area_mask
            if area_mask is None or not area_mask.any():
                self._set_status("투명 처리할 선택 영역이 없습니다.")
                return

            self.document.working_image = (
                self.transparency_processor.apply_transparent_mask(
                    self.document.working_image,
                    area_mask,
                )
            )
            transparent_pixels = int(area_mask.sum())
            self.transparency_selection.clear()
            self.area_exclude_enabled = False
            self._sync_area_exclude_state()
            self._apply_preview()
            self._update_selection_summary()
            self._set_status(
                f"선택 영역 {transparent_pixels}픽셀을 투명 처리했습니다.",
            )
            return

        selected_colors = self.transparency_selection.selected_colors
        if not selected_colors:
            self._set_status("투명 처리할 선택 항목이 없습니다.")
            return

        self.document.working_image = (
            self.transparency_processor.apply_transparent_colors(
                self.document.working_image,
                selected_colors,
            )
        )
        self._apply_preview()
        self._set_status(
            f"{len(selected_colors)}개 RGB 컬러를 투명 처리했습니다.",
        )

    def _clear_transparency_selection(self) -> None:
        self.transparency_selection.clear()
        self.area_exclude_enabled = False
        self._clear_selection_overlay()
        self._sync_area_exclude_state()
        self._update_selection_summary()
        self._apply_preview()
        self._set_status("투명 처리 선택을 해제했습니다.")

    def _on_mouse_down(self, _sender, _app_data) -> None:
        if self.left_mouse_active:
            return
        if not self._is_preview_click_active():
            return

        image_point = self._get_mouse_image_point()
        if image_point is None:
            return

        self.left_mouse_active = True
        mode = self.transparency_selection.mode
        if mode == TransparencySelectionMode.COLOR:
            self._select_color_at_point(image_point)
        elif mode == TransparencySelectionMode.RECTANGLE:
            if self.transparency_selection.drag_start is not None:
                return

            self.transparency_selection.start_drag(image_point)
            self._update_selection_overlay()
        elif mode == TransparencySelectionMode.AREA:
            if self._start_area_exclude_drag(image_point):
                return
            self._select_area_at_point(image_point)

    def _on_mouse_drag(self, _sender, _app_data) -> None:
        if self._update_area_exclude_drag():
            return

        if self.transparency_selection.mode != TransparencySelectionMode.RECTANGLE:
            return
        if self.transparency_selection.drag_start is None:
            return

        image_point = self._get_mouse_image_point(clamp=True)
        if image_point is None:
            return

        self.transparency_selection.update_drag(image_point)
        self._update_selection_overlay()

    def _on_mouse_release(self, _sender, _app_data) -> None:
        try:
            if self._finish_area_exclude_drag():
                return

            if (
                self.transparency_selection.mode
                != TransparencySelectionMode.RECTANGLE
            ):
                return
            if self.transparency_selection.drag_start is None:
                return

            image_point = self._get_mouse_image_point(clamp=True)
            if image_point is not None:
                self.transparency_selection.update_drag(image_point)

            self._finish_rectangle_selection()
        finally:
            self.left_mouse_active = False

    def _start_area_exclude_drag(self, image_point: tuple[int, int]) -> bool:
        if not self._is_area_exclude_drag_mode():
            return False
        if self.transparency_selection.drag_start is not None:
            return True

        if self.area_exclude_mode == TransparencyExcludeMode.RECTANGLE:
            self.transparency_selection.start_drag(image_point)
        else:
            self.transparency_selection.start_freeform(image_point)

        self._update_selection_overlay()
        return True

    def _update_area_exclude_drag(self) -> bool:
        if not self._is_area_exclude_drag_mode():
            return False
        if self.transparency_selection.drag_start is None:
            return False

        image_point = self._get_mouse_image_point(clamp=True)
        if image_point is None:
            return True

        if self.area_exclude_mode == TransparencyExcludeMode.RECTANGLE:
            self.transparency_selection.update_drag(image_point)
        else:
            self.transparency_selection.add_freeform_point(image_point)

        self._update_selection_overlay()
        return True

    def _finish_area_exclude_drag(self) -> bool:
        if not self._is_area_exclude_drag_mode():
            return False
        if self.transparency_selection.drag_start is None:
            return False

        image_point = self._get_mouse_image_point(clamp=True)
        if image_point is not None:
            if self.area_exclude_mode == TransparencyExcludeMode.RECTANGLE:
                self.transparency_selection.update_drag(image_point)
            else:
                self.transparency_selection.add_freeform_point(image_point)

        if self.area_exclude_mode == TransparencyExcludeMode.RECTANGLE:
            self._exclude_rectangle_area()
        else:
            self._exclude_freeform_area()

        self.transparency_selection.clear_drag_state()
        self._clear_selection_overlay()
        return True

    def _is_area_exclude_drag_mode(self) -> bool:
        return (
            self.transparency_selection.mode == TransparencySelectionMode.AREA
            and self.area_exclude_enabled
            and self.area_exclude_mode in {
                TransparencyExcludeMode.RECTANGLE,
                TransparencyExcludeMode.FREEFORM,
            }
        )

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

    def _is_preview_click_active(self) -> bool:
        if self.document.preview_image is None:
            return False
        if not dpg.does_item_exist(self.preview_image_tag):
            return False
        return bool(dpg.is_item_hovered(self.preview_image_tag))

    def _change_zoom_by_wheel_delta(self, wheel_delta: float) -> None:
        next_zoom = self.options.zoom + (wheel_delta * ZOOM_WHEEL_STEP)
        self.options.zoom = max(ZOOM_MIN, min(ZOOM_MAX, next_zoom))

        if dpg.does_item_exist(self.zoom_slider_tag):
            dpg.set_value(self.zoom_slider_tag, self.options.zoom)

        self._refresh_preview_texture()

    def _get_primary_scroll_position(self) -> tuple[float, float]:
        scroll_position = self._get_scroll_position(self.primary_window_tag)
        if scroll_position is None:
            return 0.0, 0.0
        return scroll_position

    def _restore_primary_scroll_position(
        self,
        scroll_position: tuple[float, float],
    ) -> None:
        self._restore_scroll_snapshot(
            {self.primary_window_tag: scroll_position},
        )

    def _get_preview_scroll_snapshot(self) -> dict[str, tuple[float, float]]:
        snapshot = {}
        for tag in (self.primary_window_tag, self.preview_area_tag):
            scroll_position = self._get_scroll_position(tag)
            if scroll_position is not None:
                snapshot[tag] = scroll_position
        return snapshot

    def _get_scroll_position(
        self,
        item_tag: str,
    ) -> tuple[float, float] | None:
        if not dpg.does_item_exist(item_tag):
            return None

        return (
            dpg.get_x_scroll(item_tag),
            dpg.get_y_scroll(item_tag),
        )

    def _restore_scroll_snapshot(
        self,
        snapshot: dict[str, tuple[float, float]],
    ) -> None:
        if not snapshot:
            return

        self._set_scroll_snapshot(snapshot)
        next_frame = dpg.get_frame_count() + 1
        dpg.set_frame_callback(
            next_frame,
            callback=lambda: self._set_scroll_snapshot(snapshot),
        )

    def _set_scroll_snapshot(
        self,
        snapshot: dict[str, tuple[float, float]],
    ) -> None:
        for item_tag, scroll_position in snapshot.items():
            self._set_scroll_position(item_tag, scroll_position)

    def _set_scroll_position(
        self,
        item_tag: str,
        scroll_position: tuple[float, float],
    ) -> None:
        if not dpg.does_item_exist(item_tag):
            return

        x_position, y_position = scroll_position
        dpg.set_x_scroll(item_tag, x_position)
        dpg.set_y_scroll(item_tag, y_position)

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
        self.document.reset_working_image()
        self.transparency_selection.clear()
        self.area_exclude_enabled = False
        self.area_exclude_mode = TransparencyExcludeMode.DETAIL
        self._clear_selection_overlay()
        self._sync_controls()
        self._update_selection_summary()
        self._apply_preview(preserve_scroll=False)

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
            self.transparency_mode_combo_tag: self.transparency_selection.mode,
            self.area_exclude_check_tag: self.area_exclude_enabled,
            self.area_exclude_mode_combo_tag: self.area_exclude_mode,
        }

        for tag, value in control_values.items():
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

        self._sync_zoom_slider_state()
        self._sync_area_exclude_state()

    def _sync_zoom_slider_state(self) -> None:
        if dpg.does_item_exist(self.zoom_slider_tag):
            dpg.configure_item(
                self.zoom_slider_tag,
                enabled=self.zoom_slider_enabled,
            )
        self._sync_wheel_scroll_block()

    def _sync_area_exclude_state(self) -> None:
        area_mode = (
            self.transparency_selection.mode == TransparencySelectionMode.AREA
        )
        if not area_mode:
            self.area_exclude_enabled = False

        if not dpg.does_item_exist(self.area_exclude_check_tag):
            return

        dpg.configure_item(self.area_exclude_check_tag, enabled=area_mode)
        dpg.set_value(self.area_exclude_check_tag, self.area_exclude_enabled)
        if dpg.does_item_exist(self.area_exclude_mode_combo_tag):
            exclude_method_enabled = area_mode and self.area_exclude_enabled
            dpg.configure_item(
                self.area_exclude_mode_combo_tag,
                enabled=exclude_method_enabled,
            )
            dpg.set_value(
                self.area_exclude_mode_combo_tag,
                self.area_exclude_mode,
            )

    def _apply_preview(self, preserve_scroll: bool = True) -> None:
        if self.document.working_image is None:
            return

        self.document.preview_image = self.processor.apply(
            self.document.working_image,
            self.options,
        )
        self.document.preview_image = (
            self.transparency_processor.apply_selection_highlight(
                self.document.preview_image,
                self.transparency_selection.area_mask,
            )
        )
        self._refresh_preview_texture(preserve_scroll)

    def _refresh_preview_texture(self, preserve_scroll: bool = True) -> None:
        if self.document.preview_image is None:
            return

        scroll_snapshot = {}
        if preserve_scroll:
            scroll_snapshot = self._get_preview_scroll_snapshot()
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
        self._restore_scroll_snapshot(scroll_snapshot)
        self._update_selection_overlay()
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
        transparent_pixels = self._count_transparent_pixels()
        mode = "엣지 View" if self.options.edge_preview else "일반 View"

        dpg.set_value(
            self.metadata_tag,
            f"{source_name}\n"
            f"원본: {original_width} x {original_height}\n"
            f"View: {preview_width} x {preview_height}\n"
            f"투명 픽셀: {transparent_pixels}\n"
            f"모드: {mode}",
        )

    def _select_color_at_point(self, image_point: tuple[int, int]) -> None:
        if self.document.working_image is None:
            return

        color = self.document.working_image.convert("RGB").getpixel(
            image_point,
        )
        self.transparency_selection.set_color(color)
        self._clear_selection_overlay()
        self._update_selection_summary()
        self._set_status(
            f"RGB{color} 컬러를 선택했습니다. 적용 버튼을 누르면 투명 처리됩니다.",
        )

    def _finish_rectangle_selection(self) -> None:
        if self.document.working_image is None:
            return

        rectangle = self.transparency_selection.get_drag_rectangle()
        if rectangle is None:
            return

        image_width, image_height = self.document.working_image.size
        rectangle = rectangle.clamp(image_width, image_height)
        colors = self.transparency_processor.collect_rectangle_colors(
            self.document.working_image,
            rectangle,
        )
        self.transparency_selection.set_rectangle(rectangle, colors)
        self._clear_selection_overlay()
        self._update_selection_summary()
        self._set_status(
            f"사각형 영역에서 {len(colors)}개 RGB 컬러를 선택했습니다.",
        )

    def _select_area_at_point(self, image_point: tuple[int, int]) -> None:
        if self.document.working_image is None:
            return

        if self.area_exclude_enabled:
            if self.area_exclude_mode == TransparencyExcludeMode.DETAIL:
                self._exclude_detail_area_at_point(image_point)
            return

        area_mask = self.transparency_processor.collect_area_mask(
            self.document.working_image,
            image_point,
        )
        if not area_mask.any():
            self.transparency_selection.clear()
            self._apply_preview()
            self._update_selection_summary()
            self._set_status("선택할 수 있는 영역을 찾지 못했습니다.")
            return

        self.transparency_selection.set_area_mask(image_point, area_mask)
        self._clear_selection_overlay()
        self._update_selection_summary()
        self._apply_preview()
        self._set_status(
            f"영역 {int(area_mask.sum())}픽셀을 선택했습니다.",
        )

    def _exclude_detail_area_at_point(self, image_point: tuple[int, int]) -> None:
        if self.document.working_image is None:
            return

        current_mask = self.transparency_selection.area_mask
        if current_mask is None or not current_mask.any():
            self._set_status("먼저 제외 기준이 될 영역을 선택하세요.")
            return

        exclude_mask = self.transparency_processor.collect_detail_area_mask(
            self.document.working_image,
            current_mask,
            image_point,
        )
        self._apply_area_exclude_mask(exclude_mask, "세부 영역")

    def _exclude_rectangle_area(self) -> None:
        if self.document.working_image is None:
            return

        rectangle = self.transparency_selection.get_drag_rectangle()
        if rectangle is None:
            self._set_status("제외할 사각형 영역이 없습니다.")
            return

        exclude_mask = self.transparency_processor.collect_rectangle_mask(
            self.document.working_image.size,
            rectangle,
        )
        self._apply_area_exclude_mask(exclude_mask, "사각형 영역")

    def _exclude_freeform_area(self) -> None:
        if self.document.working_image is None:
            return

        points = self.transparency_selection.freeform_points
        if len(points) < 3:
            self._set_status("제외할 자유형 영역이 너무 작습니다.")
            return

        exclude_mask = self.transparency_processor.collect_freeform_mask(
            self.document.working_image.size,
            points,
        )
        self._apply_area_exclude_mask(exclude_mask, "자유형 영역")

    def _apply_area_exclude_mask(
        self,
        exclude_mask,
        label: str,
    ) -> None:
        current_mask = self.transparency_selection.area_mask
        if current_mask is None or not current_mask.any():
            self._set_status("먼저 제외 기준이 될 영역을 선택하세요.")
            return

        overlap_mask = current_mask & exclude_mask
        if not overlap_mask.any():
            self._set_status("현재 선택 영역과 겹치는 제외 영역이 없습니다.")
            return

        next_mask = self.transparency_processor.subtract_area_mask(
            current_mask,
            exclude_mask,
        )
        removed_pixels = int(overlap_mask.sum())
        if not next_mask.any():
            self.transparency_selection.clear()
            self.area_exclude_enabled = False
            self._sync_area_exclude_state()
            self._update_selection_summary()
            self._apply_preview()
            self._set_status("제외 후 남은 선택 영역이 없습니다.")
            return

        seed_point = self.transparency_selection.area_seed_point or (0, 0)
        self.transparency_selection.set_area_mask(seed_point, next_mask)
        self._update_selection_summary()
        self._apply_preview()
        self._set_status(
            f"선택 영역에서 {label} {removed_pixels}픽셀을 제외했습니다.",
        )

    def _get_mouse_image_point(
        self,
        clamp: bool = False,
    ) -> tuple[int, int] | None:
        mouse_x, mouse_y = dpg.get_mouse_pos(local=False)
        return self._display_point_to_image_point(mouse_x, mouse_y, clamp)

    def _display_point_to_image_point(
        self,
        display_x: float,
        display_y: float,
        clamp: bool = False,
    ) -> tuple[int, int] | None:
        if self.document.working_image is None:
            return None

        preview_rect = self._get_preview_display_rect()
        if preview_rect is None:
            return None

        left, top, width, height = preview_rect
        if width <= 0 or height <= 0:
            return None

        relative_x = display_x - left
        relative_y = display_y - top

        if clamp:
            relative_x = max(0.0, min(width - 1, relative_x))
            relative_y = max(0.0, min(height - 1, relative_y))
        elif (
            relative_x < 0
            or relative_y < 0
            or relative_x >= width
            or relative_y >= height
        ):
            return None

        image_width, image_height = self.document.working_image.size
        image_x = int(relative_x * image_width / width)
        image_y = int(relative_y * image_height / height)
        image_x = max(0, min(image_width - 1, image_x))
        image_y = max(0, min(image_height - 1, image_y))
        return image_x, image_y

    def _get_preview_display_rect(self) -> tuple[float, float, float, float] | None:
        if not dpg.does_item_exist(self.preview_image_tag):
            return None

        left, top = dpg.get_item_rect_min(self.preview_image_tag)
        width, height = dpg.get_item_rect_size(self.preview_image_tag)
        return float(left), float(top), float(width), float(height)

    def _update_selection_overlay(self) -> None:
        self._clear_selection_overlay()
        if not dpg.does_item_exist(self.selection_overlay_tag):
            return

        if self._is_area_exclude_drag_mode():
            self._update_area_exclude_overlay()
            return

        if self.transparency_selection.mode != TransparencySelectionMode.RECTANGLE:
            return

        rectangle = self.transparency_selection.get_drag_rectangle()
        if rectangle is None:
            return

        self._draw_rectangle_overlay(rectangle)

    def _update_area_exclude_overlay(self) -> None:
        if self.area_exclude_mode == TransparencyExcludeMode.RECTANGLE:
            rectangle = self.transparency_selection.get_drag_rectangle()
            if rectangle is None:
                return

            self._draw_rectangle_overlay(rectangle)
            return

        if self.area_exclude_mode != TransparencyExcludeMode.FREEFORM:
            return

        display_points = self._image_points_to_display_points(
            self.transparency_selection.freeform_points,
        )
        if len(display_points) < 2:
            return

        if len(display_points) >= 3:
            dpg.draw_polygon(
                display_points,
                parent=self.selection_overlay_tag,
                tag=self.selection_freeform_tag,
                color=(255, 220, 80, 255),
                fill=(255, 220, 80, 35),
                thickness=2.0,
            )
            return

        dpg.draw_polyline(
            display_points,
            parent=self.selection_overlay_tag,
            tag=self.selection_freeform_tag,
            color=(255, 220, 80, 255),
            thickness=2.0,
        )

    def _draw_rectangle_overlay(
        self,
        rectangle: ImageSelectionRectangle,
    ) -> None:
        display_bounds = self._image_rectangle_to_display_bounds(rectangle)
        if display_bounds is None:
            return

        left, top, right, bottom = display_bounds
        dpg.draw_rectangle(
            (left, top),
            (right, bottom),
            parent=self.selection_overlay_tag,
            tag=self.selection_rectangle_tag,
            color=(80, 180, 255, 255),
            fill=(80, 180, 255, 45),
            thickness=2.0,
        )

    def _clear_selection_overlay(self) -> None:
        for tag in (self.selection_rectangle_tag, self.selection_freeform_tag):
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)

    def _image_rectangle_to_display_bounds(
        self,
        rectangle: ImageSelectionRectangle,
    ) -> tuple[float, float, float, float] | None:
        if self.document.working_image is None:
            return None

        preview_rect = self._get_preview_display_rect()
        if preview_rect is None:
            return None

        left, top, width, height = preview_rect
        image_width, image_height = self.document.working_image.size
        return (
            left + (rectangle.left * width / image_width),
            top + (rectangle.top * height / image_height),
            left + ((rectangle.right + 1) * width / image_width),
            top + ((rectangle.bottom + 1) * height / image_height),
        )

    def _image_points_to_display_points(
        self,
        points: list[tuple[int, int]],
    ) -> list[list[float]]:
        display_points = []
        for point in points:
            display_point = self._image_point_to_display_point(point)
            if display_point is not None:
                display_points.append([display_point[0], display_point[1]])
        return display_points

    def _image_point_to_display_point(
        self,
        point: tuple[int, int],
    ) -> tuple[float, float] | None:
        if self.document.working_image is None:
            return None

        preview_rect = self._get_preview_display_rect()
        if preview_rect is None:
            return None

        left, top, width, height = preview_rect
        image_width, image_height = self.document.working_image.size
        point_x, point_y = point
        return (
            left + (point_x * width / image_width),
            top + (point_y * height / image_height),
        )

    def _update_selection_summary(self) -> None:
        if not dpg.does_item_exist(self.transparency_selection_summary_tag):
            return

        selection = self.transparency_selection
        if selection.mode == TransparencySelectionMode.AREA:
            exclude_status = "켜짐" if self.area_exclude_enabled else "꺼짐"
            if selection.area_mask is None:
                message = (
                    "영역 선택: View에서 처리할 영역을 클릭하세요."
                    f"\n제외 모드: {exclude_status}"
                    f"\n제외 방식: {self.area_exclude_mode}"
                )
            else:
                seed_x, seed_y = selection.area_seed_point or (0, 0)
                message = (
                    f"선택 영역: {int(selection.area_mask.sum())}픽셀"
                    f"\n기준점: {seed_x}, {seed_y}"
                    f"\n제외 모드: {exclude_status}"
                    f"\n제외 방식: {self.area_exclude_mode}"
                )
        elif not selection.selected_colors:
            message = "선택 없음"
        elif selection.mode == TransparencySelectionMode.COLOR:
            color = next(iter(selection.selected_colors))
            message = f"선택 컬러: RGB{color}"
        else:
            rectangle = selection.rectangle
            area_text = ""
            if rectangle is not None:
                area_text = (
                    f"\n영역: {rectangle.left}, {rectangle.top} - "
                    f"{rectangle.right}, {rectangle.bottom}"
                )
            message = f"선택 컬러 수: {len(selection.selected_colors)}{area_text}"

        dpg.set_value(self.transparency_selection_summary_tag, message)

    def _count_transparent_pixels(self) -> int:
        if self.document.working_image is None:
            return 0

        alpha_values = self.document.working_image.getchannel("A")
        return int(alpha_values.histogram()[0])

    def _set_status(self, message: str) -> None:
        dpg.set_value(self.status_tag, message)


if __name__ == "__main__":
    AssetEditorApplication().run()
