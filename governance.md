# OpenGaia Project Governance

## Vision

OpenGaia is an open-source, modular, community-driven digital twin of the Earth system. Our governance model is designed to foster broad participation while maintaining coherent technical direction and responsible stewardship.

## Principles

1. **Open participation** — Anyone may contribute, subject to our Code of Conduct.
2. **Technical meritocracy** — Decisions are guided by technical soundness and project vision, not by affiliation or seniority.
3. **Transparency** — Discussions, decisions, and roadmap are publicly accessible.
4. **Responsible stewardship** — We prioritize safety, ethics, and societal benefit.
5. **Modular independence** — Modules may have separate maintainers; the core coupling layer is jointly stewarded.

## Roles

### Contributor
Anyone who submits a pull request, files an issue, or participates in discussions.

### Maintainer
A contributor with commit access, responsible for reviewing PRs, triaging issues, and upholding quality standards in their area. Maintainers are added by consensus of existing maintainers.

### Core Maintainer
A maintainer with oversight of the coupling engine, architecture, and cross-cutting concerns. Core maintainers collectively decide the project roadmap and release schedule.

### Benevolent Dictator (Interim)
During the pre-alpha and alpha phases (v0.x), a single project lead has final authority on design decisions. This role will transition to a maintainer council at v1.0.

## Decision-Making

- **Day-to-day**: PRs are merged after one maintainer approval (with reasonable wait time for input).
- **Design changes**: Architecture decisions use Request-for-Comment (RFC) issues with a minimum 7-day comment period.
- **Contentious decisions**: Escalated to core maintainers; majority vote wins.
- **Governance amendments**: Require 2/3 supermajority of all maintainers.

## Module Stewardship

Each module directory may have its own maintainer(s). Modules must:
- Maintain interoperability with the coupling engine.
- Follow the project's coding standards and testing requirements.
- Not introduce dependencies that conflict with the core project.

## Release Process

- Versioning follows SemVer (major.minor.patch).
- Pre-alpha (v0.x): releases are ad-hoc, triggered when significant features land.
- Alpha (v1.0-alpha): scheduled releases every 3 months.
- Stable (v1.0+): scheduled releases with LTS support.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the practical guide to contributing code, documentation, or data.

## Code of Conduct

All contributors must abide by the project's Code of Conduct (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).

---

This governance document itself is subject to amendment by the process described above.
