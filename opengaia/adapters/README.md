# OpenGaia Adapters — Interoperability Layer

This directory contains adapter modules that bridge OpenGaia's internal
WorldState with external Earth system digital twins and modeling frameworks.

## Purpose

OpenGaia does not replace existing high-fidelity Earth system models.
Instead, it provides the **integrative meta-layer** — coupling socio-economic
agents, technology dynamics, and AI safety sandboxing with physical Earth
states. The adapters here make that integration concrete.

## Available Adapters

| Adapter | Status | Description |
|---------|--------|-------------|
| Earth2Studio | Stub (v0.2) | NVIDIA Earth-2 AI-accelerated climate emulators — `Earth2StudioAdapter` |

## Integration Patterns

See `docs/architecture.md#interoperability-with-external-digital-twins` for
the three levels of coupling (offline ingestion, loose online, tight module).

## Contributing an Adapter

1. Create a subdirectory `adapters/<name>/` with a clear `README.md` describing
   the external system and the supported coupling level.
2. Implement the `BaseAdapter` interface (see docs).
3. Include test fixtures using synthetic data so integration can be validated
   without access to the external system.
4. Open a pull request with documentation of the coupling design.

For questions about adapter design, open a GitHub Discussion.
