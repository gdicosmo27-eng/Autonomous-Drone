import os

from agent.confirmation import ConfirmationBroker
from agent.flight_controller import StubFlightController
from agent.loop import AgentLoop
from agent.notifier import CompositeNotifier, ConsoleNotifier, TwilioNotifier
from agent.sms_client import StubTwilioClient, TwilioSmsClient
from agent.sms_webhook import create_app, run_webhook_server
from agent.twilio_config import TwilioConfig
from agent.vision import StubVisionEvaluator

# Wires the agent loop to Twilio and confimation response webhook
def build_sms_client(config: TwilioConfig):
    if os.environ.get("AGENT_SMS_STUB") == "1":
        return StubTwilioClient()
    return TwilioSmsClient(config.account_sid, config.auth_token)

def main():
    config = TwilioConfig.from_env()
    sms_client = build_sms_client(config)

    notifier = CompositeNotifier(
        [ConsoleNotifier(), TwilioNotifier(sms_client, config.from_number, config.operator_number)]
    )
    broker = ConfirmationBroker()

    webhook_app = create_app(broker, config)
    run_webhook_server(webhook_app)

    loop = AgentLoop(
        vision=StubVisionEvaluator(),
        flight_controller=StubFlightController(),
        notifier=notifier,
        confirmation_broker=broker,
    )
    return loop

if __name__ == "__main__":
    main()
