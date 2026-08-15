"""
Sentinel OS application entry point.
"""

from __future__ import annotations

from sentinel.application import Application


def main() -> None:
    """
    Start Sentinel OS.
    """
    application = Application()
    application.start()


if __name__ == "__main__":
    main()