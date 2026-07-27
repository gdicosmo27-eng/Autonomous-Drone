import uuid
from abc import ABC, abstractmethod

from twilio.rest import Client

# This file implements the SMS transport used by TwilioNotifier and the 
# confirmation webhook

class SmsClient(ABC):
    @abstractmethod
    def send(self, to: str, from_: str, body: str) -> str:
        ...

# Handle TwilioSms
class TwilioSmsClient(SmsClient):
    def __init__(self, account_sid: str, auth_token: str):
        self._client = Client(account_sid, auth_token)

    def send(self, to: str, from_: str, body: str) -> str:
        message = self._client.messages.create(to=to, from_=from_, body=body)
        return message.sid

class StubTwilioClient(SmsClient):
    """Placeholder until real Twilio credentials are wired in. Logs the
    message instead of sending it and records it for assertions in tests."""

    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, from_: str, body: str) -> str:
        self.sent.append((to, from_, body))
        print(f"[sms_client] SMS to {to}: {body}")
        return uuid.uuid4().hex
