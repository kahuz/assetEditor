# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PreviewOptions:
    grayscale: bool = False
    edge_preview: bool = False
    zoom: float = 1.0

    def reset(self) -> None:
        self.grayscale = False
        self.edge_preview = False
        self.zoom = 1.0
