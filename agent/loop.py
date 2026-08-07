import time
from typing import Any, Optional

from .notifier import NotifyLevel, Notifier
from .outcome import Outcome
from .vision import DetectionResult, VisionEvaluator
from .watch_config import WatchConfig

# This file implements the agent's watch loop. It evaluates a frame against the
# configured target and notifies the user when it is seen.

class WatchLoop:

    def __init__(
        self,
        vision: VisionEvaluator,
        notifier: Notifier,
        config: WatchConfig,
    ):
        self.vision = vision
        self.notifier = notifier
        self.config = config
        self._last_alert_at: Optional[float] = None

    # Process each frame
    def process_frame(self, frame: Any) -> Outcome:
        result = self.vision.evaluate(frame)
        return self._decide(result)

    # Decide what to do after detection
    def _decide(self, result: DetectionResult) -> Outcome:
        if not (result.detected and result.confidence >= self.config.confidence_threshold):
            return Outcome.NOT_DETECTED

        now = time.time()
        if self._last_alert_at is not None and (now - self._last_alert_at) < self.config.cooldown_s:
            self.notifier.notify(
                f"Target seen again (confidence={result.confidence:.2f}, label={result.label!r}) "
                "— still in cooldown, not alerting.",
                NotifyLevel.INFO,
            )
            return Outcome.SUPPRESSED_COOLDOWN

        self._last_alert_at = now
        self.notifier.notify(
            f"Target detected (confidence={result.confidence:.2f}, label={result.label!r})",
            NotifyLevel.ALERT,
        )
        return Outcome.ALERT_SENT
