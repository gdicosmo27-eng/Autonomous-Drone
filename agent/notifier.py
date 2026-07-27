from abc import ABC, abstractmethod
from enum import Enum

from .sms_client import SmsClient

# This file implements the user notification system and
# handles logging to the console

# Class defining the urgency of the notification
class NotifyLevel(str, Enum):
    INFO = "info" # log
    ACTION = "action" # push notification to user
    CRITICAL = "critical" 

# Implements the push notifications to the user's iphone
class Notifier(ABC):
    @abstractmethod
    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        ...

# Handle logging to console
class ConsoleNotifier(Notifier):
    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        print(f"[{level.value.upper()}] {message}")

# Fan a notification out to multiple notifiers. A failure in one
# does not suppress others
class CompositeNotifier(Notifier):
    def __init__(self, notifiers: list[Notifier]):
        self._notifiers = notifiers

    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        for notifier in self._notifiers:
            try:
                notifier.notify(message, level)
            except Exception as exc:
                print(f"[notifier] {notifier.__class__.__name__} failed: {exc}")

# Texts the operator for ACTION/CRITICAL notifications. INFO-level notifications 
# do not get sent to the user but rather get logged. Twilio failure cannot block
# battery_rth
class TwilioNotifier(Notifier):
    def __init__(self, sms_client: SmsClient, from_number: str, to_number: str):
        self._sms_client = sms_client
        self._from_number = from_number
        self._to_number = to_number

    def notify(self, message: str, level: NotifyLevel = NotifyLevel.INFO) -> None:
        if level == NotifyLevel.INFO:
            return
        try:
            self._sms_client.send(self._to_number, self._from_number, message)
        except Exception as exc:
            print(f"[notifier] TwilioNotifier failed to send SMS: {exc}")