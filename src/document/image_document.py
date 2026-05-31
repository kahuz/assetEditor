# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


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
