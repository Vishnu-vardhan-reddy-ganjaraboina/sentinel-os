"""
Public filesystem storage API for Sentinel OS.
"""

from sentinel.storage.backends.filesystem import FilesystemBackend


class FilesystemStorage(FilesystemBackend):
    """
    Backward-compatible public name for FilesystemBackend.
    """
