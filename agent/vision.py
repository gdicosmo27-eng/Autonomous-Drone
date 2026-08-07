import base64
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

# This file implements the vision interface for the drone

# Detection results
@dataclass(frozen=True)
class DetectionResult:
    detected: bool
    confidence: float # 0.0 - 1.0
    label: str = ""
    raw_response: Any = None

# Defines the perception interface for image evaluation
class VisionEvaluator(ABC):
    @abstractmethod
    def evaluate(self, frame: Any) -> DetectionResult:
        ...

class StubVisionEvaluator(VisionEvaluator):
    """Deterministic placeholder so the loop is runnable before a real
    vision mode (or the screen-clip capture script) is wired in"""

    def __init__(self, fixed_result: Optional[DetectionResult] = None):
        self._fixed_result = fixed_result or DetectionResult(detected = False, confidence = 0)

    def evaluate(self, frame: Any) -> DetectionResult:
        return self._fixed_result


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)

_PROMPT_TEMPLATE = (
    "You are watching a single frame from a live FPV drone video feed. "
    "Determine whether the following target is visible in this frame: {target!r}\n\n"
    "Respond with ONLY a JSON object (no markdown, no other text) in this exact shape:\n"
    '{{"detected": true or false, "confidence": a number from 0.0 to 1.0, '
    '"label": a short string naming what you saw, "reasoning": a short string '
    "explaining your answer}}"
)

# Evaluates frames with a vision-capable Claude model against an arbitrary,
# natural-language target description (e.g. "a blue Ford Bronco"). This is
# what makes open-ended targets possible without training a custom detector.
class ClaudeVisionEvaluator(VisionEvaluator):
    def __init__(
        self,
        target_description: str,
        client: Optional[Any] = None,
        model: str = "claude-haiku-4-5-20251001",
        max_tokens: int = 300,
    ):
        if client is None:
            from anthropic import Anthropic
            client = Anthropic()
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._prompt = _PROMPT_TEMPLATE.format(target=target_description)

    def evaluate(self, frame: bytes) -> DetectionResult:
        try:
            image_b64 = base64.b64encode(frame).decode("utf-8")
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": self._prompt},
                        ],
                    }
                ],
            )
            text = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            )
        except Exception as exc:
            # A vision API failure (network, auth, rate limit, ...) must never
            # crash the watch loop — treat the frame as a non-detection.
            print(f"[vision] ClaudeVisionEvaluator request failed: {exc}")
            return DetectionResult(detected=False, confidence=0.0, raw_response=str(exc))

        return self._parse(text)

    def _parse(self, text: str) -> DetectionResult:
        match = _JSON_OBJECT_RE.search(text)
        if not match:
            print(f"[vision] ClaudeVisionEvaluator got no JSON in response: {text!r}")
            return DetectionResult(detected=False, confidence=0.0, raw_response=text)
        try:
            payload = json.loads(match.group(0))
            detected = bool(payload["detected"])
            confidence = max(0.0, min(1.0, float(payload["confidence"])))
            label = str(payload.get("label", ""))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(f"[vision] ClaudeVisionEvaluator got unparsable response ({exc}): {text!r}")
            return DetectionResult(detected=False, confidence=0.0, raw_response=text)
        return DetectionResult(detected=detected, confidence=confidence, label=label, raw_response=text)
