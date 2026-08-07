import os
from dataclasses import dataclass
from typing import Optional

# This file loads the parameters that define what the agent is watching for
# and how it should behave

_DEFAULT_CONFIDENCE_THRESHOLD = 0.7
_DEFAULT_COOLDOWN_S = 60.0
_DEFAULT_CAPTURE_INTERVAL_S = 5.0
_DEFAULT_VISION_MODEL = "claude-haiku-4-5-20251001"

@dataclass(frozen=True)
class WatchConfig:
    target_description: str
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD
    cooldown_s: float = _DEFAULT_COOLDOWN_S
    capture_interval_s: float = _DEFAULT_CAPTURE_INTERVAL_S
    vision_model: str = _DEFAULT_VISION_MODEL

    @classmethod
    def from_env(
        cls,
        target_override: Optional[str] = None,
        threshold_override: Optional[float] = None,
        interval_override: Optional[float] = None,
    ) -> "WatchConfig":
        target = target_override or os.environ.get("WATCH_TARGET")
        if not target:
            raise RuntimeError(
                "No watch target set. Provide --target or set WATCH_TARGET, "
                "e.g. WATCH_TARGET='a blue Ford Bronco'"
            )
        return cls(
            target_description=target,
            confidence_threshold=(
                threshold_override
                if threshold_override is not None
                else float(os.environ.get("WATCH_CONFIDENCE_THRESHOLD", _DEFAULT_CONFIDENCE_THRESHOLD))
            ),
            cooldown_s=float(os.environ.get("WATCH_COOLDOWN_S", _DEFAULT_COOLDOWN_S)),
            capture_interval_s=(
                interval_override
                if interval_override is not None
                else float(os.environ.get("WATCH_CAPTURE_INTERVAL_S", _DEFAULT_CAPTURE_INTERVAL_S))
            ),
            vision_model=os.environ.get("WATCH_VISION_MODEL", _DEFAULT_VISION_MODEL),
        )
