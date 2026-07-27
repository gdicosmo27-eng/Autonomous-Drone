import threading

from flask import Flask, request
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from .confirmation import ConfirmationBroker
from .twilio_config import TwilioConfig

# This file handles user response to the TwilioSms confirmation notification
# a y/n response resolves the pending confirmation

_APPROVE_WORDS = {"YES", "Y", "yes", "y"}
_DENY_WORDS = {"NO", "N", "no", "n"}

# Handles the SMS replies
def handle_sms_reply(
    from_number: str, body: str, broker: ConfirmationBroker, operator_number: str
) -> str:
    if from_number != operator_number:
        return ""

    normalized = body.strip().upper()
    if normalized in _APPROVE_WORDS:
        approved = True
    elif normalized in _DENY_WORDS:
        approved = False
    else:
        return "Reply YES to approve or NO to deny."

    pending = broker.pending_requests()
    if not pending:
        return "No pending confirmation."

    req = min(pending, key=lambda r: r.created_at)
    if approved:
        broker.approve(req.request_id)
        return f"{req.action.value} approved."
    broker.deny(req.request_id)
    return f"{req.action.value} denied."

# Create flask
def create_app(broker: ConfirmationBroker, config: TwilioConfig) -> Flask:
    app = Flask(__name__)
    validator = RequestValidator(config.auth_token)

    @app.post("/sms")
    def sms():
        signature = request.headers.get("X-Twilio-Signature", "")
        if not validator.validate(request.url, request.form, signature):
            return "invalid signature", 403

        reply_text = handle_sms_reply(
            request.form.get("From", ""),
            request.form.get("Body", ""),
            broker,
            config.operator_number,
        )
        twiml = MessagingResponse()
        if reply_text:
            twiml.message(reply_text)
        return str(twiml), 200, {"Content-Type": "text/xml"}

    return app

# Run the webhook server
def run_webhook_server(app: Flask, host: str = "0.0.0.0", port: int = 5000) -> threading.Thread:
    thread = threading.Thread(
        target=app.run, kwargs={"host": host, "port": port}, daemon=True
    )
    thread.start()
    return thread
