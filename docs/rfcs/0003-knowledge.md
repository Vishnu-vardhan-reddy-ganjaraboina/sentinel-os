# RFC-0003: Knowledge Subsystem

| Field | Value |
|--------|-------|
| RFC | 0003 |
| Title | Knowledge Subsystem |
| Status | Accepted |
| Author | Sentinel Engineering |
| Created | 2026-07-26 |
| Target Version | v0.3.0 |

---

# 1. Abstract

The Knowledge subsystem is responsible for representing, organizing,
maintaining, and retrieving everything Sentinel OS knows.

Unlike the Storage subsystem, which stores bytes, the Knowledge subsystem
stores structured knowledge and relationships between entities.

Knowledge is the foundation upon which the Brain performs reasoning,
planning, learning, and decision making.

---

# 2. Motivation

Modern AI assistants frequently mix:

- storage
- memory
- context
- reasoning

inside a single component.

This leads to tightly coupled systems that become difficult to extend.

Sentinel separates these responsibilities into independent subsystems.

Storage persists information.

Knowledge manages information.

Brain reasons over information.

This separation improves maintainability, scalability, testing, and future
extensibility.

---

# 3. Goals

The Knowledge subsystem SHALL:

- Represent every entity known to Sentinel.
- Maintain entity relationships.
- Support efficient lookup.
- Support indexing.
- Support versioning.
- Support lifecycle management.
- Support future semantic search.
- Remain independent of any AI model.

---

# 4. Non Goals

The Knowledge subsystem SHALL NOT:

- Call LLM APIs.
- Perform reasoning.
- Generate prompts.
- Execute automations.
- Manage storage engines.
- Access hardware directly.

---

# 5. Responsibilities

Knowledge is responsible for:

- Creating records
- Updating records
- Removing records
- Searching records
- Indexing records
- Managing relationships
- Publishing knowledge events

---

# 6. Architecture

Application

↓

Brain

↓

Knowledge Service

↓

Knowledge Manager

↓

Stores

↓

Storage Manager

↓

SQLite / Filesystem

---

# 7. Knowledge Model

Every piece of information SHALL be represented by a KnowledgeRecord.

Examples include:

- User
- Device
- File
- Folder
- Application
- Plugin
- Network
- Task
- Email
- Project
- Calendar
- AI Model

No specialized UserRecord or DeviceRecord classes shall exist unless there
is a compelling architectural reason.

---

# 8. Relationships

Knowledge records may be connected using typed relationships.

Examples:

User

OWNS

Laptop

Laptop

RUNS

VS Code

VS Code

CONTAINS

Sentinel Project

Relationships enable graph traversal and future reasoning capabilities.

---

# 9. Knowledge Lifecycle

Knowledge progresses through states.

Created

↓

Active

↓

Archived

↓

Deleted

Expired records MAY transition automatically according to policies.

---

# 10. Stores

Knowledge SHALL be separated into three logical stores.

Session Store

Knowledge valid only during runtime.

Working Store

Frequently accessed operational knowledge.

Long-Term Store

Persistent knowledge.

---

# 11. Events

Knowledge SHALL publish events.

Examples:

KnowledgeCreated

KnowledgeUpdated

KnowledgeArchived

KnowledgeDeleted

KnowledgeExpired

Other subsystems SHOULD subscribe through the EventBus.

---

# 12. Thread Safety

Knowledge Manager SHALL be thread-safe.

Stores MAY use locking internally.

---

# 13. Extensibility

Future versions MAY include:

Vector indexes

Graph traversal

Knowledge ranking

Confidence scoring

Temporal reasoning

Semantic search

Distributed synchronization

---

# 14. Alternatives Considered

Alternative 1

Traditional Memory Manager.

Rejected because it encourages treating knowledge as key-value pairs.

Alternative 2

Direct SQLite access.

Rejected because it tightly couples reasoning to persistence.

Alternative 3

Knowledge Graph only.

Rejected because a graph alone does not address lifecycle,
storage abstraction, or operational concerns.

---

# 15. Decision

Sentinel SHALL introduce a dedicated Knowledge subsystem positioned between
Storage and Brain.

Knowledge SHALL become the canonical source of information used by all
higher-level subsystems.

---

# 16. Future RFCs

RFC-0004 Brain

RFC-0005 Skills

RFC-0006 Communication

RFC-0007 Automation

RFC-0008 Devices

RFC-0009 Security

RFC-0010 AI Integration