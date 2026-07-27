import os
from dataclasses import dataclass

# This file loads the Twilio credentials and phone numbers used for
# notifications and webhook.

_ENV_VARS = (
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
    "TWILIO_OPERATOR_NUMBER",
)

@dataclass(frozen=True)
class TwilioConfig:
    account_sid: str
    auth_token: str
    from_number: str
    operator_number: str

    @classmethod
    def from_env(cls) -> "TwilioConfig":
        values = {name: os.environ.get(name) for name in _ENV_VARS}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required Twilio env vars: {', '.join(missing)}")
        return cls(
            account_sid=values["TWILIO_ACCOUNT_SID"],
            auth_token=values["TWILIO_AUTH_TOKEN"],
            from_number=values["TWILIO_FROM_NUMBER"],
            operator_number=values["TWILIO_OPERATOR_NUMBER"],
        )
