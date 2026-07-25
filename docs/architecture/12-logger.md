# Logger

## Purpose

Provides a centralized logging service for Sentinel OS.

## Features

- Console logging
- File logging
- Shared logger instance
- Timestamped messages
- Configurable log level

## Usage

```python
from sentinel.infrastructure.logger import logger

logger.info("Kernel started")