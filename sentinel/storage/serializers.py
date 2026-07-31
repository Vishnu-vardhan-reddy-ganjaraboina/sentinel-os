"""
Serialization utilities for Sentinel OS.
"""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, TextIO

from sentinel.storage.exceptions import (
    StorageSerializationError,
)


class Serializer(ABC):
    """
    Base serializer interface.
    """

    @abstractmethod
    def dump(
        self,
        value: Any,
        stream: TextIO | BinaryIO,
    ) -> None:
        """
        Serialize an object.
        """
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
        stream: TextIO | BinaryIO,
    ) -> Any:
        """
        Deserialize an object.
        """
        raise NotImplementedError
class JsonSerializer(Serializer):
    """
    JSON serializer.
    """

    def dump(
        self,
        value: Any,
        stream: TextIO,
    ) -> None:
        try:
            json.dump(
                value,
                stream,
                indent=4,
            )
        except Exception as exc:
            raise StorageSerializationError(
                str(exc)
            ) from exc

    def load(
        self,
        stream: TextIO,
    ) -> Any:
        try:
            return json.load(stream)
        except Exception as exc:
            raise StorageSerializationError(
                str(exc)
            ) from exc

class PickleSerializer(Serializer):
    """
    Binary pickle serializer.

    Only use for trusted internal data.
    """

    def dump(
        self,
        value: Any,
        stream: BinaryIO,
    ) -> None:
        try:
            pickle.dump(
                value,
                stream,
            )
        except Exception as exc:
            raise StorageSerializationError(
                str(exc)
            ) from exc

    def load(
        self,
        stream: BinaryIO,
    ) -> Any:
        try:
            return pickle.load(stream)
        except Exception as exc:
            raise StorageSerializationError(
                str(exc)
            ) from exc