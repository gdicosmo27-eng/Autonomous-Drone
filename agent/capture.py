import os
import subprocess
import tempfile
from abc import ABC, abstractmethod

# This file implements screen capture of the VTX ground-station feed so
# frames can be handed to a VisionEvaluator for evaluation

class FrameSource(ABC):
    @abstractmethod
    def capture(self) -> bytes:
        ...

class ScreenGrabFrameSource(FrameSource):
    """Captures the full primary display via macOS's built-in `screencapture`
    CLI and returns JPEG-encoded bytes, ready to send to a vision evaluator."""

    def capture(self) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(["screencapture", "-x", "-t", "jpg", tmp_path], check=True)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.remove(tmp_path)

class StubFrameSource(FrameSource):
    """Placeholder until the real screen-grab capture is exercised on a
    machine with a display. Records call count for test assertions."""

    def __init__(self, fixed_bytes: bytes = b""):
        self._fixed_bytes = fixed_bytes
        self.capture_count = 0

    def capture(self) -> bytes:
        self.capture_count += 1
        return self._fixed_bytes
