# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import dearpygui.dearpygui as dpg

from common import DEFAULT_FONT_SIZE, KOREAN_FONT_PATHS


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
