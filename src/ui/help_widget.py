# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Callable

import dearpygui.dearpygui as dpg


class HelpWidget:
    def add_button(
        self,
        label: str,
        tooltip: str,
        callback: Callable,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(label=label, width=250, callback=callback)
            self.add_icon(tooltip)

    def add_checkbox(
        self,
        label: str,
        tag: str,
        tooltip: str,
        callback: Callable,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label=label, tag=tag, callback=callback)
            self.add_icon(tooltip)

    def add_combo(
        self,
        tag: str,
        tooltip: str,
        items: list[str],
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_combo(items, tag=tag, width=250)
            self.add_icon(tooltip)

    def add_slider(
        self,
        label: str,
        tag: str,
        tooltip: str,
        default_value: float,
        min_value: float,
        max_value: float,
        callback: Callable,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text(label)
            self.add_icon(tooltip)
        dpg.add_slider_float(
            tag=tag,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            callback=callback,
            width=-1,
        )

    def add_lockable_slider(
        self,
        label: str,
        check_tag: str,
        slider_tag: str,
        tooltip: str,
        default_value: float,
        min_value: float,
        max_value: float,
        check_callback: Callable,
        slider_callback: Callable,
    ) -> None:
        with dpg.group(horizontal=True):
            dpg.add_checkbox(
                label=label,
                tag=check_tag,
                callback=check_callback,
            )
            self.add_icon(tooltip)
        dpg.add_slider_float(
            tag=slider_tag,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            callback=slider_callback,
            width=-1,
        )

    def add_icon(self, tooltip: str) -> None:
        help_item = dpg.add_text("?", color=(120, 170, 255, 255))
        with dpg.tooltip(help_item):
            dpg.add_text(tooltip, wrap=260)
