# Dependency Resolver

Services never choose startup order.

Each service declares dependencies.

Example

Brain

depends on

Memory

AI Engine

Logger

The Dependency Resolver builds a dependency graph.

The Kernel starts services using topological ordering.

Circular dependencies are rejected.