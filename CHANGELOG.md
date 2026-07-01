# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-07-01

### Added
- **Socio-Economic Module** (`opengaia/socio_economic/`): Heterogeneous agents with
  types (subsistence, worker, entrepreneur, investor), multi-region WorldEconomy,
  demographics with fertility/mortality/urbanization dynamics, and an
  inter-region migration model driven by economic, environmental, and conflict factors.
- **Technology & Innovation Module** (`opengaia/tech_innovation/`): S-curve technology
  adoption with learning rates, AI capability and alignment trajectory modeling,
  R&D investment with knowledge accumulation and diminishing returns.
- **Safety Sandbox** (`opengaia/safety_sandbox/`): AI agent insertion framework with
  configurable motivations (cooperation, power-seeking, deception, exploration),
  alignment metrics tracking (risk score, deception detection, power concentration),
  and 5 built-in policy interventions (capability limiting, alignment training,
  transparency mandate, resource rationing, kill switch).
- **Test suite** (`tests/`): 38 pytest tests covering all implemented modules.
- **CLI demos**: `opengaia demo socio`, `opengaia demo tech`, `opengaia demo safety`.
- **CLI command**: `opengaia modules` to list module status.
- **Documentation**: Architecture doc updated with v0.2 module status and key features.

### Fixed
- `opengaia/__init__.py`: Removed broken import from `.examples.mvp_demo`.
- `pyproject.toml`: Added `dev` optional-dependencies, corrected script entry point.

### Changed
- Version bumped from 0.1.0 to 0.2.0.

## [0.1.0] — 2026-Q3 (Seed)

### Added
- Core coupling engine with WorldState and ordered module orchestration
- MVP demo: toy coupled climate + socio-economic simulation with Monte Carlo
- Project skeleton: README, CONTRIBUTING, CODE_OF_CONDUCT, LICENSE (Apache 2.0)
- Package structure: pyproject.toml, CLI (typer + rich), docs (architecture, roadmap)
- Physics/Bio stub: ClimateEmulator interface placeholder for ACE/Earth2Studio
- Getting-started docs and contribution guide
