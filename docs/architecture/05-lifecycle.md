# Lifecycle Manager

The Lifecycle Manager controls the state of every service.

## States

Created

↓

Registered

↓

Initializing

↓

Starting

↓

Running

↓

Stopping

↓

Stopped

↓

Failed

---

## Responsibilities

- Start services
- Stop services
- Restart failed services
- Notify Health Monitor
- Publish lifecycle events