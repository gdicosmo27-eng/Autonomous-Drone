import os
from dataclasses import dataclass
from typing import Optional

# This file loads the settings for pushing alerts via ntfy.sh (or a
# self-hosted ntfy server). NTFY_TOPIC is effectively a shared secret on
# public ntfy.sh — use a long, random, hard-to-guess name, not something
# like "my-alerts".

_DEFAULT_SERVER = "https://ntfy.sh"

@dataclass(frozen=True)
class NtfyConfig:
    server: str
    topic: str
    access_token: Optional[str] = None

    @property
    def topic_url(self) -> str:
        return f"{self.server.rstrip('/')}/{self.topic}"

    @classmethod
    def from_env(cls) -> "NtfyConfig":
        topic = os.environ.get("NTFY_TOPIC")
        if not topic:
            raise RuntimeError(
                "Missing required env var NTFY_TOPIC. Pick a long, random topic name "
                "(e.g. drone-watch-x7f3k2q9) and subscribe to it in the ntfy app."
            )
        return cls(
            server=os.environ.get("NTFY_SERVER", _DEFAULT_SERVER),
            topic=topic,
            access_token=os.environ.get("NTFY_ACCESS_TOKEN") or None,
        )
