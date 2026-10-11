"""
Serialization utilities for Sentinel OS.
"""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, TextIO

from sentinel.storage.exceptions import StorageSerializationError


class Serializer[StreamT: TextIO | BinaryIO](ABC):
    """
    Base serializer interface.
    """

    @abstractmethod
    def dump(
        self,
        value: Any,
        stream: StreamT,
    ) -> None:
        """
        Serialize an object.
        """
        raise NotImplementedError

    @abstractmethod
    def load(
        self,
        stream: StreamT,
    ) -> Any:
        """
        Deserialize an object.
        """
        raise NotImplementedError


class JsonSerializer(Serializer[TextIO]):
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


class PickleSerializer(Serializer[BinaryIO]):
    """
    Serialize and deserialize Python objects using pickle.

    SECURITY WARNING:
        Pickle deserialization can execute arbitrary code. Never load data
        from untrusted, user-controlled, or otherwise unverified sources.
        Only deserialize data whose origin and integrity you trust.

    Prefer JsonSerializer for ordinary data whenever possible.
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
            return pickle.load(stream)  # nosec B301
        except Exception as exc:
            raise StorageSerializationError(
                str(exc)
            ) from exc