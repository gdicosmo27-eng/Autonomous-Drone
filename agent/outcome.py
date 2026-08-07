from enum import Enum

# This file defines the possible outcomes of evaluating a frame.

class Outcome(str, Enum):
    ALERT_SENT = "alert_sent"              # target detected, threshold met, notified operator
    SUPPRESSED_COOLDOWN = "suppressed_cooldown"  # target detected, but still within cooldown window
    NOT_DETECTED = "not_detected"          # target not detected (or below confidence threshold)
