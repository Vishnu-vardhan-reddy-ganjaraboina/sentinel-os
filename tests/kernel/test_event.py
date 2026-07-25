import pytest

from sentinel.kernel.event import Event


def test_create_event():

    event = Event(
        name="Started",
        source="Logger",
    )

    assert event.name == "Started"
    assert event.source == "Logger"


def test_empty_name():

    with pytest.raises(ValueError):
        Event(
            name="",
            source="Logger",
        )


def test_empty_source():

    with pytest.raises(ValueError):
        Event(
            name="Started",
            source="",
        )


def test_payload():

    event = Event(
        name="Started",
        source="Logger",
        payload={"id": 1},
    )

    assert event.payload["id"] == 1