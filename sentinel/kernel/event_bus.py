"""
Thread-safe publish/subscribe event bus for Sentinel OS.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock

from sentinel.kernel.event import Event

EventHandler = Callable[[Event], None]


class EventBus:
    """
    Thread-safe synchronous event bus.

    Events are delivered immediately to every subscribed handler.
    """

    __slots__ = (
        "_subscribers",
        "_lock",
    )

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe a handler to an event.
        """
        with self._lock:
            handlers = self._subscribers[event_name]

            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        """
        Remove a subscription.
        """
        with self._lock:
            handlers = self._subscribers.get(event_name)

            if handlers is None:
                return

            try:
                handlers.remove(handler)
            except ValueError:
                return

            if not handlers:
                del self._subscribers[event_name]

    def publish(
        self,
        event: Event,
    ) -> None:
        """
        Publish an event to all subscribers.

        One failing subscriber does not prevent others
        from receiving the event.
        """
        with self._lock:
            handlers = tuple(
                self._subscribers.get(event.name, ())
            )

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Future Logger service will record this.
                continue

    def clear(self) -> None:
        """
        Remove all subscriptions.
        """
        with self._lock:
            self._subscribers.clear()

    def subscriber_count(
        self,
        event_name: str,
    ) -> int:
        """
        Return number of subscribers.
        """
        with self._lock:
            return len(
                self._subscribers.get(event_name, ())
            )

    @property
    def published_events(self) -> tuple[str, ...]:
        """
        Return all event names with subscribers.
        """
        with self._lock:
            return tuple(self._subscribers.keys())

    def __len__(self) -> int:
        """
        Number of event types registered.
        """
        with self._lock:
            return len(self._subscribers)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(event_types={len(self)})"
        )