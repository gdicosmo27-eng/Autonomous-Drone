import urllib.request
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional

# This file implements the user notification system: logging to the
# console, and pushing ALERT-level notifications to the operator's phone via
# ntfy.sh.

# Class defining the urgency of the notification
class NotifyLevel(str, Enum):
    INFO = "info" # log only, not sent to the operator
    ALERT = "alert" # push to the operator, threshold met

# Implements the push notifications to the user's iphone
class Notifier(ABC):
    @abstractmethod
    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        ...

# Handle logging to console
class ConsoleNotifier(Notifier):
    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        print(f"[{level.value.upper()}] {message}")

# Distribute a notification out to multiple notifiers.
class CompositeNotifier(Notifier):
    def __init__(self, notifiers: list[Notifier]):
        self._notifiers = notifiers

    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        for notifier in self._notifiers:
            try:
                notifier.notify(message, level)
            except Exception as exc:
                print(f"[notifier] {notifier.__class__.__name__} failed: {exc}")

def _default_http_post(url: str, data: bytes, headers: dict) -> None:
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()

# Pushes a notification to the operator's phone (via the ntfy app) for
# ALERT-level notifications only. INFO-level notifications do not get
# pushed, only logged. A send failure must never crash the watch loop.
class NtfyNotifier(Notifier):
    def __init__(
        self,
        topic_url: str,
        access_token: Optional[str] = None,
        http_post: Optional[Callable[[str, bytes, dict], None]] = None,
    ):
        self._topic_url = topic_url
        self._access_token = access_token
        # Injectable for tests; defaults to a real HTTP POST.
        self._http_post = http_post or _default_http_post

    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        if level != NotifyLevel.ALERT:
            return
        headers = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            self._http_post(self._topic_url, message.encode("utf-8"), headers)
        except Exception as exc:
            print(f"[notifier] NtfyNotifier failed to push: {exc}")

class StubNotifier(Notifier):
    """Placeholder until a real ntfy topic is wired in. Logs ALERT-level
    notifications instead of pushing them, and records them for tests."""

    def __init__(self):
        self.sent: list[str] = []

    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        if level != NotifyLevel.ALERT:
            return
        self.sent.append(message)
        print(f"[stub-notify] {message}")
