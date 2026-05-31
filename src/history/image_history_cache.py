# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from common import CACHE_FILE_PATH, MAX_HISTORY_SIZE


class ImageHistoryCache:
    def __init__(
        self,
        cache_path: Path = CACHE_FILE_PATH,
        max_history_size: int = MAX_HISTORY_SIZE,
    ) -> None:
        self.cache_path = cache_path
        self.max_history_size = max_history_size
        self.history = self.load()

    def load(self) -> list[str]:
        if not self.cache_path.exists():
            return []

        try:
            cache_data = json.loads(
                self.cache_path.read_text(encoding="utf-8"),
            )
        except (OSError, json.JSONDecodeError):
            return []

        paths = cache_data.get("paths", [])
        if not isinstance(paths, list):
            return []

        return [path for path in paths if isinstance(path, str)]

    def add(self, path: str) -> None:
        history_path = str(Path(path).resolve())
        self.history = [
            saved_path
            for saved_path in self.history
            if saved_path.lower() != history_path.lower()
        ]
        self.history.insert(0, history_path)
        self.history = self.history[: self.max_history_size]
        self.save()

    def get_recent_image_directory(self) -> str:
        if not self.history:
            return ""

        recent_image_path = Path(self.history[0])
        recent_directory = recent_image_path.parent
        if not recent_directory.exists():
            return ""

        return str(recent_directory)

    def clear(self) -> None:
        self.history = []
        self.save()

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {"paths": self.history}
        self.cache_path.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
