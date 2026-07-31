
from sentinel.kernel.event import Event
from sentinel.kernel.event_bus import EventBus


def test_publish():

    bus = EventBus()

    received = []

    def handler(event: Event):
        received.append(event)

    bus.subscribe("Started", handler)

    event = Event(
        name="Started",
        source="Logger",
    )

    bus.publish(event)

    assert received == [event]


def test_multiple_handlers():

    bus = EventBus()

    count = 0

    def a(event):
        nonlocal count
        count += 1

    def b(event):
        nonlocal count
        count += 1

    bus.subscribe("Started", a)
    bus.subscribe("Started", b)

    bus.publish(
        Event(
            name="Started",
            source="Logger",
        )
    )

    assert count == 2


def test_unsubscribe():

    bus = EventBus()

    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("Started", handler)
    bus.unsubscribe("Started", handler)

    bus.publish(
        Event(
            name="Started",
            source="Logger",
        )
    )

    assert received == []


def test_handler_failure():

    bus = EventBus()

    called = False

    def bad(event):
        raise RuntimeError

    def good(event):
        nonlocal called
        called = True

    bus.subscribe("Started", bad)
    bus.subscribe("Started", good)

    bus.publish(
        Event(
            name="Started",
            source="Logger",
        )
    )

    assert called