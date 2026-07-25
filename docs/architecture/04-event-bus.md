# Event Bus

## Purpose

The Event Bus is the communication backbone of Sentinel OS.

Services never communicate directly unless absolutely required.

Instead they publish and subscribe to events.

---

## Benefits

- Loose coupling
- Easier testing
- Better scalability
- Easy plugin development
- Distributed execution

---

## Event Structure

Every event contains:

- Event ID
- Event Name
- Timestamp
- Source
- Priority
- Payload
- Correlation ID

---

## Example

Voice Service

publishes

SpeechRecognized

↓

Brain

subscribes

↓

Brain publishes

IntentDetected

↓

Planner subscribes

↓

Planner publishes

PlanCreated

↓

Automation subscribes

↓

Automation publishes

TaskCompleted

---

## Event Categories

System Events

Service Events

Security Events

Device Events

AI Events

Memory Events

Workflow Events

User Events