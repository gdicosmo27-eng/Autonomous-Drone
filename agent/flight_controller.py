from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# This file implements the commands that will be sent to the flight
# controller software. The drone runs on INAV software

# Class to keep track of battery state
@dataclass(frozen=True)
class BatteryState:
    voltage: float
    percent: float

# Implementation of commands to INAV software
class FlightController(ABC):
    @abstractmethod
    def loiter(self) -> None:
        ...
    
    @abstractmethod
    def resume_mission(self) -> None:
        ...
    
    @abstractmethod
    def return_to_home(self) -> None:
        ...

    @abstractmethod
    def get_battery_state(self) -> BatteryState:
        ...

class StubFlightController(FlightController):
    """Placeholder until the INAV/MSP serial link is implemented. Logs the
    command instead of sending it to the flight controller."""

    def __init__(self, battery_state: Optional[BatteryState] = None):
        self._battery_state = battery_state or BatteryState(voltage=16.8, percent=100.0)

    def loiter(self) -> None:
        print("[flight_controller] LOITER")

    def resume_mission(self) -> None:
        print("[flight_controller] RESUME_MISSION")

    def return_to_home(self) -> None:
        print("[flight_controller] RETURN_TO_HOME")

    def get_battery_state(self) -> BatteryState:
        return self._battery_state

    def set_battery_state(self, battery_state: BatteryState) -> None:
        self._battery_state = battery_state
