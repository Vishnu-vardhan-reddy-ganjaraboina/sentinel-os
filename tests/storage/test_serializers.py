from io import BytesIO, StringIO

import pytest

from sentinel.storage.exceptions import (
    StorageSerializationError,
)
from sentinel.storage.serializers import (
    JsonSerializer,
    PickleSerializer,
)


def test_json_round_trip():
    serializer = JsonSerializer()

    stream = StringIO()

    data = {
        "name": "Sentinel",
        "version": 1,
    }

    serializer.dump(data, stream)

    stream.seek(0)

    assert serializer.load(stream) == data


def test_pickle_round_trip():
    serializer = PickleSerializer()

    stream = BytesIO()

    data = [1, 2, 3]

    serializer.dump(data, stream)

    stream.seek(0)

    assert serializer.load(stream) == data


def test_invalid_json():
    serializer = JsonSerializer()

    stream = StringIO("{invalid json}")

    with pytest.raises(StorageSerializationError):
        serializer.load(stream)


def test_invalid_pickle():
    serializer = PickleSerializer()

    stream = BytesIO(b"not a pickle")

    with pytest.raises(StorageSerializationError):
        serializer.load(stream)