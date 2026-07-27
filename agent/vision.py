from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

# This file implements the vision interface for the drone

# An abstract class definition for detection results
# Frozen so that once the detection results are created
# they cannot accidentally be changed
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
    

