from dataclasses import dataclass
from typing import Any, Optional

from .actions import Action
from .confirmation import ConfirmationBroker, ConfirmationDenied, ConfirmationTimeout
from .flight_controller import FlightController
from .notifier import NotifyLevel, Notifier
from .vision import DetectionResult, VisionEvaluator

# This file implements the agent's reasoning loop

# Set agent parameters
@dataclass
class AgentConfig:
    loiter_confidence: float = 0.7
    uncertain_confidence: float = 0.35
    max_uncertain_streak: int = 3
    battery_rth_percent: float = 20.0
    rth_confirmation_timeout_s: float = 30.0

class AgentLoop:

    def __init__(
        self,
        vision: VisionEvaluator,
        flight_controller: FlightController,
        notifier: Notifier,
        confirmation_broker: ConfirmationBroker,
        config: Optional[AgentConfig] = None
    ):
        self.vision = vision
        self.flight_controller = flight_controller
        self.notifier = notifier
        self.confirmation_broker = confirmation_broker
        self.config = config or AgentConfig()
        self.uncertain_streak = 0

    # Process each frame
    def process_frame(self, frame: Any) -> Action:
        # Battery check
        battery = self.flight_controller.get_battery_state()
        if battery.percent <= self.config.battery_rth_percent:
            return self.trigger_battery_rth(battery.percent)
        
        result = self.vision.evaluate(frame)
        return self._decide(result)
    
    # Decide what to do after dectection
    def _decide(self, result: DetectionResult) -> Action:
        # Trigger LOITER
        if result.detected and result.confidence >= self.config.loiter_confidence:
            self.uncertain_streak = 0
            self.flight_controller.loiter()
            self.notifier.notify(
                f"Vehicle detected (confidence={result.confidence:.2f}, label = {result.label!r}) - loitering",
                NotifyLevel.ACTION,
            )
            return Action.LOITER

        # Trigger CAPTURE_FRAMES
        if self.config.uncertain_confidence <= result.confidence < self.config.loiter_confidence:
            self.uncertain_streak += 1
            if self.uncertain_streak >= self.config.max_uncertain_streak:
                self.uncertain_streak = 0
                self.flight_controller.resume_mission()
                self.notifier.notify(
                    "Uncertain detection past retry limit — continuing mission.",
                    NotifyLevel.INFO,
                )
                return Action.CONTINUE_MISSION
            self.notifier.notify(
                f"Uncertain detection (confidence={result.confidence:.2f}) — capturing more frames.",
                NotifyLevel.INFO,
            )
            return Action.CAPTURE_FRAMES

        self.uncertain_streak = 0
        self.flight_controller.resume_mission()
        return Action.CONTINUE_MISSION

    # Trigger BATTERY_RTH
    def trigger_battery_rth(self, percent: float) -> Action:
        req = self.confirmation_broker.request(
            Action.BATTERY_RTH, reason=f"Battery at {percent:.0f}%"
        )
        self.flight_controller.return_to_home()
        self.confirmation_broker.approve(req.request_id) # Just logs, doesn't wait
        self.notifier.notify(
            f"Battery at {percent:.0f}% - auto-triggering return to home",
            NotifyLevel.CRITICAL,
        )
        return Action.BATTERY_RTH

    # Agent or user requested return to home, not safety critical
    def request_return_to_home(self, reason: str) -> Action:
        req = self.confirmation_broker.request(
            Action.RETURN_TO_HOME,
            reason = reason,
            timeout_s = self.config.rth_confirmation_timeout_s,
        )
        self.notifier.notify(
            f"RTH requested ({reason}) - awaiting confirmation [{req.request_id}]",
            NotifyLevel.ACTION
        )
        try:
            self.confirmation_broker.wait(
                req.request_id, timeout_s = self.config.rth_confirmation_timeout_s
            )
        except (ConfirmationTimeout, ConfirmationDenied) as exc:
            self.notifier.notify(f"RTH not executed: {exc}", NotifyLevel.INFO)
            raise

        self.flight_controller.return_to_home()
        self.notifier.notify("RTH confirmed and executed.", NotifyLevel.ACTION)
        return Action.RETURN_TO_HOME
