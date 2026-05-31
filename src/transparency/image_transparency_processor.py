# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import deque
from collections.abc import Iterable

import cv2
import numpy as np
from PIL import Image

from transparency.transparency_selection import (
    ImagePoint,
    ImageSelectionRectangle,
    RgbColor,
)


class ImageTransparencyProcessor:
    def apply_transparent_colors(
        self,
        image: Image.Image,
        colors: Iterable[RgbColor],
    ) -> Image.Image:
        color_values = self._pack_colors(colors)
        result_array = np.array(image.convert("RGBA"))

        if color_values.size == 0:
            return Image.fromarray(result_array)

        rgb_values = self._pack_rgb_array(result_array[:, :, :3])
        transparent_mask = np.isin(rgb_values, color_values)
        result_array[:, :, 3][transparent_mask] = 0
        return Image.fromarray(result_array)

    def collect_rectangle_colors(
        self,
        image: Image.Image,
        rectangle: ImageSelectionRectangle,
    ) -> set[RgbColor]:
        image_width, image_height = image.size
        clamped_rectangle = rectangle.clamp(image_width, image_height)
        rgb_array = np.array(image.convert("RGB"))
        selected_area = rgb_array[
            clamped_rectangle.top : clamped_rectangle.bottom + 1,
            clamped_rectangle.left : clamped_rectangle.right + 1,
        ]
        unique_colors = np.unique(selected_area.reshape(-1, 3), axis=0)
        return {
            (int(red), int(green), int(blue))
            for red, green, blue in unique_colors
        }

    def collect_similar_color_mask(
        self,
        image: Image.Image,
        colors: Iterable[RgbColor],
        tolerance: float,
    ) -> np.ndarray:
        color_list = list(colors)
        image_rgba_array = np.array(image.convert("RGBA"))
        image_rgb_array = image_rgba_array[:, :, :3]
        visible_mask = image_rgba_array[:, :, 3] > 0
        if not color_list:
            return np.zeros(image_rgb_array.shape[:2], dtype=bool)

        if tolerance <= 0.0:
            return (
                self._collect_exact_color_mask(image_rgb_array, color_list)
                & visible_mask
            )

        image_hsv_array = cv2.cvtColor(
            image_rgb_array,
            cv2.COLOR_RGB2HSV,
        ).astype(np.float32)
        sample_hsv_array = self._convert_colors_to_hsv(color_list)
        hue_values = sample_hsv_array[:, 0] / 179.0
        saturation_values = sample_hsv_array[:, 1] / 255.0
        value_values = sample_hsv_array[:, 2] / 255.0

        hue_center = self._calculate_hue_center(hue_values)
        hue_spread = float(
            self._calculate_hue_distance(hue_values, hue_center).max(),
        )
        hue_limit = min(0.5, hue_spread + (tolerance * 0.18))
        saturation_margin = tolerance * 0.45
        value_margin = tolerance * 0.75

        image_hue = image_hsv_array[:, :, 0] / 179.0
        image_saturation = image_hsv_array[:, :, 1] / 255.0
        image_value = image_hsv_array[:, :, 2] / 255.0
        hue_mask = (
            self._calculate_hue_distance(image_hue, hue_center)
            <= hue_limit
        )
        saturation_min = float(saturation_values.min()) - saturation_margin
        saturation_max = float(saturation_values.max()) + saturation_margin
        saturation_mask = (
            image_saturation >= max(0.0, saturation_min)
        ) & (
            image_saturation <= min(1.0, saturation_max)
        )
        value_mask = (
            image_value >= max(0.0, float(value_values.min()) - value_margin)
        ) & (
            image_value <= min(1.0, float(value_values.max()) + value_margin)
        )
        return hue_mask & saturation_mask & value_mask & visible_mask

    def collect_area_mask(
        self,
        image: Image.Image,
        seed_point: ImagePoint,
    ) -> np.ndarray:
        edge_mask = self._build_edge_mask(image)
        fill_start = self._find_fill_start(edge_mask, seed_point)
        if fill_start is None:
            return np.zeros(edge_mask.shape, dtype=bool)

        return self._collect_seed_fill_mask(edge_mask, fill_start)

    def collect_detail_area_mask(
        self,
        image: Image.Image,
        selected_mask: np.ndarray,
        seed_point: ImagePoint,
    ) -> np.ndarray:
        normalized_mask = self._normalize_mask(selected_mask, image.size)
        seed_x, seed_y = self._clamp_point(seed_point, normalized_mask.shape)
        if not normalized_mask[seed_y, seed_x]:
            return np.zeros(normalized_mask.shape, dtype=bool)

        detail_edge_mask = self._build_detail_edge_mask(image)
        fillable_mask = normalized_mask & ~detail_edge_mask
        fill_start = self._find_fill_start_in_mask(
            fillable_mask,
            (seed_x, seed_y),
        )
        if fill_start is None:
            return np.zeros(normalized_mask.shape, dtype=bool)

        return self._collect_mask_fill(fillable_mask, fill_start)

    def apply_transparent_mask(
        self,
        image: Image.Image,
        area_mask: np.ndarray,
    ) -> Image.Image:
        result_array = np.array(image.convert("RGBA"))
        normalized_mask = self._normalize_mask(area_mask, image.size)
        result_array[:, :, 3][normalized_mask] = 0
        return Image.fromarray(result_array)

    def collect_rectangle_mask(
        self,
        image_size: tuple[int, int],
        rectangle: ImageSelectionRectangle,
    ) -> np.ndarray:
        image_width, image_height = image_size
        clamped_rectangle = rectangle.clamp(image_width, image_height)
        mask = np.zeros((image_height, image_width), dtype=bool)
        mask[
            clamped_rectangle.top : clamped_rectangle.bottom + 1,
            clamped_rectangle.left : clamped_rectangle.right + 1,
        ] = True
        return mask

    def collect_freeform_mask(
        self,
        image_size: tuple[int, int],
        points: list[ImagePoint],
    ) -> np.ndarray:
        image_width, image_height = image_size
        mask = np.zeros((image_height, image_width), dtype=np.uint8)
        if len(points) < 3:
            return mask.astype(bool)

        clipped_points = [
            self._clamp_point(point, mask.shape)
            for point in points
        ]
        polygon_array = np.asarray([clipped_points], dtype=np.int32)
        cv2.fillPoly(mask, polygon_array, 1)
        return mask.astype(bool)

    def subtract_area_mask(
        self,
        base_mask: np.ndarray,
        exclude_mask: np.ndarray,
    ) -> np.ndarray:
        if base_mask.shape != exclude_mask.shape:
            raise ValueError("선택 영역과 제외 영역 크기가 다릅니다.")

        return base_mask.astype(bool) & ~exclude_mask.astype(bool)

    def apply_selection_highlight(
        self,
        image: Image.Image,
        area_mask: np.ndarray | None,
    ) -> Image.Image:
        if area_mask is None:
            return image.copy().convert("RGBA")

        normalized_mask = self._normalize_mask(area_mask, image.size)
        if not normalized_mask.any():
            return image.copy().convert("RGBA")

        preview_array = np.array(image.convert("RGBA"), dtype=np.float32)
        highlight_color = np.array([64.0, 176.0, 255.0], dtype=np.float32)
        preview_array[normalized_mask, :3] = (
            preview_array[normalized_mask, :3] * 0.6
            + highlight_color * 0.4
        )
        preview_array[normalized_mask, 3] = np.maximum(
            preview_array[normalized_mask, 3],
            210.0,
        )

        boundary_mask = self._build_selection_boundary_mask(normalized_mask)
        dash_mask = self._build_dash_mask(boundary_mask)
        preview_array[boundary_mask & dash_mask, :3] = (255, 255, 255)
        preview_array[boundary_mask & ~dash_mask, :3] = (0, 0, 0)
        preview_array[boundary_mask, 3] = 255
        return Image.fromarray(
            np.clip(preview_array, 0, 255).astype(np.uint8),
        )

    def _build_edge_mask(self, image: Image.Image) -> np.ndarray:
        rgb_array = np.array(image.convert("RGB"))
        gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
        edge_array = cv2.Canny(gray_array, 80, 160)
        return edge_array > 0

    def _build_detail_edge_mask(self, image: Image.Image) -> np.ndarray:
        rgb_array = np.array(image.convert("RGB"))
        gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
        edge_array = cv2.Canny(gray_array, 30, 90)
        edge_mask = edge_array > 0
        kernel = np.ones((3, 3), dtype=np.uint8)
        return cv2.dilate(edge_mask.astype(np.uint8), kernel) > 0

    def _collect_seed_fill_mask(
        self,
        edge_mask: np.ndarray,
        seed_point: ImagePoint,
    ) -> np.ndarray:
        height, width = edge_mask.shape
        seed_x, seed_y = seed_point
        visited = np.zeros((height, width), dtype=bool)
        queue: deque[tuple[int, int]] = deque()

        visited[seed_y, seed_x] = True
        queue.append((seed_x, seed_y))

        while queue:
            x_position, y_position = queue.popleft()
            for next_x, next_y in self._iter_neighbor_points(
                x_position,
                y_position,
                width,
                height,
            ):
                if visited[next_y, next_x] or edge_mask[next_y, next_x]:
                    continue

                visited[next_y, next_x] = True
                queue.append((next_x, next_y))

        return visited

    def _collect_mask_fill(
        self,
        fillable_mask: np.ndarray,
        seed_point: ImagePoint,
    ) -> np.ndarray:
        height, width = fillable_mask.shape
        seed_x, seed_y = seed_point
        visited = np.zeros((height, width), dtype=bool)
        queue: deque[tuple[int, int]] = deque()

        visited[seed_y, seed_x] = True
        queue.append((seed_x, seed_y))

        while queue:
            x_position, y_position = queue.popleft()
            for next_x, next_y in self._iter_neighbor_points(
                x_position,
                y_position,
                width,
                height,
            ):
                if visited[next_y, next_x] or not fillable_mask[next_y, next_x]:
                    continue

                visited[next_y, next_x] = True
                queue.append((next_x, next_y))

        return visited

    def _find_fill_start(
        self,
        edge_mask: np.ndarray,
        seed_point: ImagePoint,
    ) -> ImagePoint | None:
        height, width = edge_mask.shape
        seed_x, seed_y = self._clamp_point(seed_point, edge_mask.shape)
        if not edge_mask[seed_y, seed_x]:
            return seed_x, seed_y

        for radius in range(1, 4):
            for y_position in range(seed_y - radius, seed_y + radius + 1):
                for x_position in range(seed_x - radius, seed_x + radius + 1):
                    if (
                        x_position < 0
                        or y_position < 0
                        or x_position >= width
                        or y_position >= height
                    ):
                        continue
                    if not edge_mask[y_position, x_position]:
                        return x_position, y_position

        return None

    def _find_fill_start_in_mask(
        self,
        fillable_mask: np.ndarray,
        seed_point: ImagePoint,
    ) -> ImagePoint | None:
        height, width = fillable_mask.shape
        seed_x, seed_y = self._clamp_point(seed_point, fillable_mask.shape)
        if fillable_mask[seed_y, seed_x]:
            return seed_x, seed_y

        for radius in range(1, 8):
            for y_position in range(seed_y - radius, seed_y + radius + 1):
                for x_position in range(seed_x - radius, seed_x + radius + 1):
                    if (
                        x_position < 0
                        or y_position < 0
                        or x_position >= width
                        or y_position >= height
                    ):
                        continue
                    if fillable_mask[y_position, x_position]:
                        return x_position, y_position

        return None

    def _clamp_point(
        self,
        point: ImagePoint,
        mask_shape: tuple[int, int],
    ) -> ImagePoint:
        height, width = mask_shape
        point_x = max(0, min(width - 1, point[0]))
        point_y = max(0, min(height - 1, point[1]))
        return point_x, point_y

    def _iter_neighbor_points(
        self,
        x_position: int,
        y_position: int,
        width: int,
        height: int,
    ) -> Iterable[tuple[int, int]]:
        if x_position > 0:
            yield x_position - 1, y_position
        if x_position < width - 1:
            yield x_position + 1, y_position
        if y_position > 0:
            yield x_position, y_position - 1
        if y_position < height - 1:
            yield x_position, y_position + 1

    def _pack_colors(self, colors: Iterable[RgbColor]) -> np.ndarray:
        color_list = list(colors)
        if not color_list:
            return np.array([], dtype=np.uint32)

        color_array = np.asarray(color_list, dtype=np.uint32)
        return self._pack_rgb_array(color_array)

    def _pack_rgb_array(self, rgb_array: np.ndarray) -> np.ndarray:
        rgb_values = rgb_array.astype(np.uint32)
        return (
            (rgb_values[..., 0] << 16)
            | (rgb_values[..., 1] << 8)
            | rgb_values[..., 2]
        )

    def _collect_exact_color_mask(
        self,
        rgb_array: np.ndarray,
        colors: Iterable[RgbColor],
    ) -> np.ndarray:
        color_values = self._pack_colors(colors)
        if color_values.size == 0:
            return np.zeros(rgb_array.shape[:2], dtype=bool)

        rgb_values = self._pack_rgb_array(rgb_array[:, :, :3])
        return np.isin(rgb_values, color_values)

    def _convert_colors_to_hsv(
        self,
        colors: list[RgbColor],
    ) -> np.ndarray:
        color_array = np.asarray(colors, dtype=np.uint8).reshape(-1, 1, 3)
        return cv2.cvtColor(color_array, cv2.COLOR_RGB2HSV).reshape(-1, 3)

    def _calculate_hue_center(self, hue_values: np.ndarray) -> float:
        hue_angles = hue_values * 2.0 * np.pi
        sine_mean = float(np.sin(hue_angles).mean())
        cosine_mean = float(np.cos(hue_angles).mean())
        if abs(sine_mean) < 1e-6 and abs(cosine_mean) < 1e-6:
            return float(hue_values[0])

        center_angle = np.arctan2(sine_mean, cosine_mean)
        if center_angle < 0:
            center_angle += 2.0 * np.pi
        return float(center_angle / (2.0 * np.pi))

    def _calculate_hue_distance(
        self,
        hue_values: np.ndarray,
        hue_center: float,
    ) -> np.ndarray:
        hue_diff = np.abs(hue_values - hue_center)
        return np.minimum(hue_diff, 1.0 - hue_diff)

    def _normalize_mask(
        self,
        area_mask: np.ndarray,
        image_size: tuple[int, int],
    ) -> np.ndarray:
        image_width, image_height = image_size
        expected_shape = (image_height, image_width)
        if area_mask.shape != expected_shape:
            raise ValueError("선택 영역 크기가 이미지 크기와 다릅니다.")

        return area_mask.astype(bool, copy=False)

    def _build_selection_boundary_mask(self, area_mask: np.ndarray) -> np.ndarray:
        mask_array = area_mask.astype(np.uint8)
        kernel = np.ones((3, 3), dtype=np.uint8)
        eroded_array = cv2.erode(mask_array, kernel, iterations=1)
        return area_mask & ~(eroded_array > 0)

    def _build_dash_mask(self, boundary_mask: np.ndarray) -> np.ndarray:
        y_indices, x_indices = np.indices(boundary_mask.shape)
        dash_mask = ((x_indices + y_indices) // 4) % 2 == 0
        return dash_mask & boundary_mask
