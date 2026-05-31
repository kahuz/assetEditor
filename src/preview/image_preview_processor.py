# -*- coding: utf-8 -*-
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageOps

from common import DEFAULT_CANVAS_HEIGHT, DEFAULT_CANVAS_WIDTH
from preview.preview_options import PreviewOptions


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
