import threading
import time
import uuid
from dataclasses import dataclass, field

from .actions import Action

# This file implements the confirmation request sequence with Twilio

@dataclass
class ConfirmationRequest:
    action: Action
    reason: str
    request_id: str = field(default_factory = lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory = time.time)

# The user has a time window in which to respond to a request
# before it times out
class ConfirmationTimeout(Exception):
    pass

# Handles a user denial of a request
class ConfirmationDenied(Exception):
    pass

class ConfirmationBroker:

    def __init__(self):
        self._lock = threading.Lock()
        self._pending: dict[str, ConfirmationRequest] = {}
        self._events: dict[str, threading.Event] = {}
        self._results: dict[str, bool] = {}

    # Build and manage the request
    def request(self, action: Action, reason: str, timeout_s: float = 60.0) -> ConfirmationRequest:
        req = ConfirmationRequest(action = action, reason = reason)
        event = threading.Event()
        with self._lock:
            self._pending[req.request_id] = req
            self._events[req.request_id] = event
        return req
    
    # Agent calls wait to block the request for 60s while the user responds
    def wait(self, request_id: str, timeout_s: float = 60.0) -> bool:
        event = self._events[request_id]
        approved = event.wait(timeout = timeout_s)
        with self._lock:
            self._pending.pop(request_id, None)
            self._events.pop(request_id, None)
            result = self._results.pop(request_id, None)
        if not approved:
            raise ConfirmationTimeout(f"confirmation {request_id} timed out")
        if not result:
            raise ConfirmationDenied(f"confirmation {request_id} was denied")
        return True

    # Call resolve to approve
    def approve(self, request_id: str) -> None:
        self._resolve(request_id, True)

    # Call resolve to deny
    def deny(self, request_id: str) -> None:
        self._resolve(request_id, False)

    # Set the threading event
    def _resolve(self, request_id: str, approved: bool) -> None:
        with self._lock:
            event = self._events.get(request_id)
            if event is None:
                return
            self._results[request_id] = approved
        event.set()

    # Return an array of all pending ConfirmationRequests
    def pending_requests(self) -> list[ConfirmationRequest]:
        with self._lock:
            return list(self._pending.values())