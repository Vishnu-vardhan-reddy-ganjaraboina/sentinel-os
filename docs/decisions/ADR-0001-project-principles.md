# ADR-0001

## Title

Sentinel is an Intelligent Operating System

## Status

Accepted

## Decision

Sentinel shall be developed as an operating system architecture rather than a chatbot architecture.

AI providers are replaceable services.

The Kernel is the central runtime.

Communication occurs through events.

Modules remain loosely coupled.

## Consequences

Future features must integrate through services and events.

No component may directly depend on a specific AI provider.

The system remains extensible for future hardware and software integrations.