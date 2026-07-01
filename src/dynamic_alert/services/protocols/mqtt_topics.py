from __future__ import annotations

import json
from pathlib import Path


class MqttTopicRepository:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def resolve(self, topic_set: str | None = None) -> list[str]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        return self._resolve_topics(payload, topic_set=topic_set)

    def topic_sets(self) -> list[str]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        if isinstance(payload, dict) and isinstance(payload.get("topic_sets"), dict):
            return list(payload["topic_sets"].keys())
        return []

    @staticmethod
    def _resolve_topics(payload: object, *, topic_set: str | None) -> list[str]:
        if isinstance(payload, list):
            return [str(item) for item in payload if str(item).strip()]
        if not isinstance(payload, dict):
            return []

        topic_sets = payload.get("topic_sets")
        if not isinstance(topic_sets, dict):
            return []

        selected_set = topic_set or payload.get("default_set")
        if selected_set:
            topics = topic_sets.get(selected_set, [])
            return [str(item) for item in topics if str(item).strip()] if isinstance(topics, list) else []

        combined: list[str] = []
        for topics in topic_sets.values():
            if isinstance(topics, list):
                combined.extend(str(item) for item in topics if str(item).strip())
        return combined
