## constants.py

Contains immutable platform-wide constants.

This module must never contain:

- Configuration
- Runtime state
- Business logic
- Environment-specific values

Every constant defined here should be safe to import anywhere
within Sentinel OS.