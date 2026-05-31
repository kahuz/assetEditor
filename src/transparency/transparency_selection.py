# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


RgbColor = tuple[int, int, int]
ImagePoint = tuple[int, int]


class TransparencySelectionMode:
    COLOR = "컬러 선택"
    RECTANGLE = "사각형 선택"
    AREA = "영역 선택"

    @classmethod
    def labels(cls) -> list[str]:
        return [cls.COLOR, cls.RECTANGLE, cls.AREA]


@dataclass(frozen=True)
class ImageSelectionRectangle:
    left: int
    top: int
    right: int
    bottom: int

    @classmethod
    def from_points(
        cls,
        first_point: ImagePoint,
        second_point: ImagePoint,
    ) -> "ImageSelectionRectangle":
        first_x, first_y = first_point
        second_x, second_y = second_point
        return cls(
            left=min(first_x, second_x),
            top=min(first_y, second_y),
            right=max(first_x, second_x),
            bottom=max(first_y, second_y),
        )

    def clamp(self, width: int, height: int) -> "ImageSelectionRectangle":
        max_x = max(0, width - 1)
        max_y = max(0, height - 1)
        return ImageSelectionRectangle(
            left=max(0, min(max_x, self.left)),
            top=max(0, min(max_y, self.top)),
            right=max(0, min(max_x, self.right)),
            bottom=max(0, min(max_y, self.bottom)),
        )

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1


@dataclass
class TransparencySelection:
    mode: str = TransparencySelectionMode.COLOR
    selected_colors: set[RgbColor] = field(default_factory=set)
    rectangle: ImageSelectionRectangle | None = None
    area_seed_point: ImagePoint | None = None
    area_mask: np.ndarray | None = None
    drag_start: ImagePoint | None = None
    drag_end: ImagePoint | None = None

    def set_mode(self, mode: str) -> None:
        if mode not in TransparencySelectionMode.labels():
            return

        self.mode = mode
        self.clear()

    def set_color(self, color: RgbColor) -> None:
        self.selected_colors = {color}
        self.rectangle = None
        self.area_seed_point = None
        self.area_mask = None
        self.drag_start = None
        self.drag_end = None

    def set_rectangle(
        self,
        rectangle: ImageSelectionRectangle,
        colors: set[RgbColor],
    ) -> None:
        self.rectangle = rectangle
        self.selected_colors = set(colors)
        self.area_seed_point = None
        self.area_mask = None
        self.drag_start = None
        self.drag_end = None

    def set_area_mask(
        self,
        seed_point: ImagePoint,
        area_mask: np.ndarray,
    ) -> None:
        self.area_seed_point = seed_point
        self.area_mask = area_mask.copy()
        self.selected_colors.clear()
        self.rectangle = None
        self.drag_start = None
        self.drag_end = None

    def start_drag(self, point: ImagePoint) -> None:
        self.drag_start = point
        self.drag_end = point

    def update_drag(self, point: ImagePoint) -> None:
        if self.drag_start is None:
            return

        self.drag_end = point

    def get_drag_rectangle(self) -> ImageSelectionRectangle | None:
        if self.drag_start is None or self.drag_end is None:
            return None

        return ImageSelectionRectangle.from_points(
            self.drag_start,
            self.drag_end,
        )

    def clear(self) -> None:
        self.selected_colors.clear()
        self.rectangle = None
        self.area_seed_point = None
        self.area_mask = None
        self.drag_start = None
        self.drag_end = None
