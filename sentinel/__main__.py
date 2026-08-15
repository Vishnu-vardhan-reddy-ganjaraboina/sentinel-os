"""
Sentinel OS application entry point.
"""

from __future__ import annotations

from sentinel.kernel.bootstrap import Bootstrap


def main() -> None:
    """
    Start Sentinel OS.
    """
    bootstrap = Bootstrap()
    bootstrap.start()


if __name__ == "__main__":
    main()