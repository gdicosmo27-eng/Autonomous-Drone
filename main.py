import threading
import time

from agent.actions import Action
from agent.confirmation import ConfirmationBroker, ConfirmationDenied, ConfirmationTimeout
from agent.flight_controller import BatteryState, StubFlightController
from agent.loop import AgentConfig, AgentLoop
from agent.notifier import ConsoleNotifier, NotifyLevel, TwilioNotifier
from agent.sms_client import StubTwilioClient
from agent.sms_webhook import handle_sms_reply
from agent.vision import DetectionResult, StubVisionEvaluator


def run_autonomous_examples():
    print("\n-- autonomous decisions --")
    controller = StubFlightController()
    loop = AgentLoop(
        vision=StubVisionEvaluator(DetectionResult(detected=True, confidence=0.9, label="car")),
        flight_controller=controller,
        notifier=ConsoleNotifier(),
        confirmation_broker=ConfirmationBroker(),
    )
    assert loop.process_frame(frame=None) == Action.LOITER

    loop.vision = StubVisionEvaluator(DetectionResult(detected=True, confidence=0.5, label="car?"))
    assert loop.process_frame(frame=None) == Action.CAPTURE_FRAMES
    assert loop.process_frame(frame=None) == Action.CAPTURE_FRAMES
    assert loop.process_frame(frame=None) == Action.CONTINUE_MISSION  # streak limit hit

    loop.vision = StubVisionEvaluator(DetectionResult(detected=False, confidence=0.05))
    assert loop.process_frame(frame=None) == Action.CONTINUE_MISSION


def run_battery_rth_example():
    print("\n-- battery RTH (fail-open, no confirmation wait) --")
    controller = StubFlightController(battery_state=BatteryState(voltage=14.0, percent=15.0))
    loop = AgentLoop(
        vision=StubVisionEvaluator(),
        flight_controller=controller,
        notifier=ConsoleNotifier(),
        confirmation_broker=ConfirmationBroker(),
    )
    action = loop.process_frame(frame=None)
    assert action == Action.BATTERY_RTH


def run_user_rth_examples():
    print("\n-- user-confirmed RTH --")
    broker = ConfirmationBroker()
    loop = AgentLoop(
        vision=StubVisionEvaluator(),
        flight_controller=StubFlightController(),
        notifier=ConsoleNotifier(),
        confirmation_broker=broker,
        config=AgentConfig(rth_confirmation_timeout_s=2.0),
    )

    def approve_soon():
        time.sleep(0.2)
        pending = broker.pending_requests()
        if pending:
            broker.approve(pending[0].request_id)

    threading.Thread(target=approve_soon).start()
    assert loop.request_return_to_home(reason="user tapped RTH") == Action.RETURN_TO_HOME

    print("\n-- user-denied RTH --")

    def deny_soon():
        time.sleep(0.2)
        pending = broker.pending_requests()
        if pending:
            broker.deny(pending[0].request_id)

    threading.Thread(target=deny_soon).start()
    try:
        loop.request_return_to_home(reason="agent requested, but should be denied")
    except ConfirmationDenied:
        print("(denied as expected)")

    print("\n-- RTH confirmation timeout --")
    try:
        loop.request_return_to_home(reason="nobody answers")
    except ConfirmationTimeout:
        print("(timed out as expected)")


def run_twilio_notifier_examples():
    print("\n-- Twilio notifier (SMS on ACTION/CRITICAL only) --")
    stub_client = StubTwilioClient()
    notifier = TwilioNotifier(stub_client, from_number="+15550001111", to_number="+15550002222")

    notifier.notify("routine info, should not text", NotifyLevel.INFO)
    assert stub_client.sent == []

    notifier.notify("loitering", NotifyLevel.ACTION)
    notifier.notify("battery critical", NotifyLevel.CRITICAL)
    assert len(stub_client.sent) == 2

    print("\n-- SMS reply-to-confirm (FIFO on multiple pending requests) --")
    broker = ConfirmationBroker()
    operator_number = "+15550002222"

    older = broker.request(Action.RETURN_TO_HOME, reason="agent requested RTH")
    time.sleep(0.01)
    newer = broker.request(Action.RETURN_TO_HOME, reason="second RTH request")

    reply = handle_sms_reply(operator_number, "yes", broker, operator_number)
    assert reply == "return_to_home approved."
    assert broker.wait(older.request_id) is True  # agent consumes the approval, as request_return_to_home does
    remaining = broker.pending_requests()
    assert [req.request_id for req in remaining] == [newer.request_id]

    print("\n-- SMS reply ignored from unknown number --")
    reply = handle_sms_reply("+19995550000", "yes", broker, operator_number)
    assert reply == ""
    assert len(broker.pending_requests()) == 1

    handle_sms_reply(operator_number, "no", broker, operator_number)
    try:
        broker.wait(newer.request_id)
        assert False, "expected ConfirmationDenied"
    except ConfirmationDenied:
        print("(denied as expected)")

    print("\n-- SMS reply with no pending confirmation --")
    reply = handle_sms_reply(operator_number, "yes", broker, operator_number)
    assert reply == "No pending confirmation."


if __name__ == "__main__":
    run_autonomous_examples()
    run_battery_rth_example()
    run_user_rth_examples()
    run_twilio_notifier_examples()
