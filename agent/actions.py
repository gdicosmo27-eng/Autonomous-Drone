from enum import Enum

# This file defines the set of actions the agent is allowed
# to perform and whether it can perform them with/without
# user input

# Class defining all the actions the agent can execute
class Action(str, Enum):
    LOITER = "loiter"
    CONTINUE_MISSION = "continue_mission"
    CAPTURE_FRAMES = "capture_frames"
    NOTIFY_USER = "notify_user"
    RETURN_TO_HOME = "return_to_home"
    BATTERY_RTH = "battery_rth"

# The set of actions that the agent is allowed
# to carry out completely autonomously
AUTONOMOUS_ACTIONS = frozenset(
    {
    Action.LOITER,
    Action.CONTINUE_MISSION,
    Action.CAPTURE_FRAMES,
    Action.NOTIFY_USER
    }
)

# The set of actions that require user confirmation
CONFIRM_REQUIRED_ACTIONS = frozenset(
    {
        Action.RETURN_TO_HOME,
        Action.BATTERY_RTH
    }
)

# BATTERY_RTH is set to "fail open" because the drone must 
# return home on low battery if the user fails to respond 
FAIL_OPEN_ACTIONS = frozenset(
    {
        Action.BATTERY_RTH
    }
)