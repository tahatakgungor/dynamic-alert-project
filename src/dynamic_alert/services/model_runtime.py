from dataclasses import dataclass

from dynamic_alert.config import Settings


@dataclass(slots=True)
class ModelSuggestion:
    name: str
    runtime: str
    purpose: str


class LocalModelRuntimePlanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def recommended_stack(self) -> list[ModelSuggestion]:
        return [
            ModelSuggestion(
                name="semantic-heuristic-v1",
                runtime="builtin",
                purpose="Always-on fallback for deterministic edge semantic inference",
            ),
            ModelSuggestion(
                name="phi-3.5-mini",
                runtime="ollama-or-onnx",
                purpose="Compact local reasoning for payload explanation and semantic mapping",
            ),
            ModelSuggestion(
                name="qwen2.5-instruct",
                runtime="ollama-or-vllm",
                purpose="General protocol notes, operator assistance, and mapping proposals",
            ),
        ]
