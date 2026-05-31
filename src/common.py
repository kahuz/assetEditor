# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


APP_TITLE = "assetEditor"
DEFAULT_CANVAS_WIDTH = 960
DEFAULT_CANVAS_HEIGHT = 640
DEFAULT_FONT_SIZE = 18
ZOOM_MIN = 0.25
ZOOM_MAX = 10.0
ZOOM_WHEEL_STEP = 0.1
COLOR_TOLERANCE_MIN = 0.0
COLOR_TOLERANCE_MAX = 1.0
CACHE_FILE_PATH = Path(".cache/asset_editor_history.json")
MAX_HISTORY_SIZE = 20
KOREAN_FONT_PATHS = (
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("C:/Windows/Fonts/NotoSansKR-Regular.otf"),
)
