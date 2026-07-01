# OpenGaia Architecture (v0.1+)

This document describes the high-level technical architecture and module interfaces. It will evolve rapidly as the project matures.

## Core Principles

1. **Modularity First**: Every major domain (physics, socio-economics, tech, safety) is a first-class module with a narrow, well-documented interface to the coupling layer.
2. **Shared WorldState**: Single source of truth for the current state of the simulated planet. Rich, versioned, and queryable.
3. **Hybrid Coupling**: Support both tight timestep coupling and looser / latent-space interfaces so modules can evolve independently.
4. **Validation & Uncertainty Native**: Every output and every coupling step carries provenance and uncertainty metadata.
5. **Swappability**: Toy implementations → production open models (ACE, Earth2Studio, etc.) with minimal code changes for users.
6. **Open by Default**: Code, model weights (where possible), data schemas, and validation artifacts are public.

## WorldState

In v0.1 we use a lightweight Python dataclass (`core/coupling_engine.py`).

**Future (v0.3+)**: Backed by `xarray.Dataset` with:
- Dimensions: `time`, `region` (or lat/lon grid), `ensemble_member`, `variable`
- Coordinates + rich metadata
- History as a separate or appended dataset for branching / what-if analysis
- Serialization to Zarr / NetCDF for large runs

Key variables (illustrative):
- Climate: `temp_anomaly`, `precipitation`, `extreme_indices`, `carbon_fluxes`
- Socio: `population`, `gdp`, `inequality_gini`, `migration_flows`, `conflict_risk`
- Tech: `ai_capability_index`, `tech_adoption_rates`, `rd_investment`
- Derived / policy: `policy_levers`, `intervention_costs`

## Coupling Engine

`core/coupling_engine.py` provides `CouplingEngine` which:
- Maintains ordered list of registered modules
- Calls `module.step(state, dt)` in sequence each timestep
- Handles basic logging and state recording
- (Future) dependency graph resolution, parallel execution of independent modules, checkpointing, ensemble management

Modules are responsible for reading what they need from `state` and writing updates back. The engine does **not** enforce physics or economic consistency — that is the responsibility of well-designed modules + validation layer.

## Module Interfaces (Contract)

Every module should implement (at minimum):

```python
def step(state: WorldState, dt: float) -> None:
    """Advance this module's state variables by dt years."""

def get_diagnostics(state: WorldState) -> Dict[str, Any]:
    """Return current diagnostics, uncertainty estimates, provenance."""
```

Optional but recommended:
- `initialize(state, config)`
- `validate_historical(state, historical_data)`
- `run_ensemble(...)`

## Data Layer

`data/` will contain:
- Catalog of open datasets (intake catalog or simple YAML + download scripts)
- Synthetic population / agent generators calibrated to public aggregates
- Preprocessing pipelines (xarray + dask)
- Versioned snapshots for reproducibility

## Safety Sandbox

Special module (`safety_sandbox/`) that can:
- Pause normal timestepping
- Inject one or more advanced AI agents (or swarms) with defined capabilities/goals
- Let them interact with the simulated economy, institutions, and humans
- Log rich traces for alignment analysis (deception, collusion, power-seeking, value drift, etc.)
- Resume or branch the simulation

This is intended as a primary research tool for empirical AGI safety work.

## Visualization & Query Layer

`ui_viz/` will provide:
- Interactive dashboard (Gradio / Streamlit / custom)
- Globe / map views (pyvista, folium, or cesium via web)
- Natural language → scenario parser (initially simple templates, later LLM-assisted)
- Monte Carlo result browsers with uncertainty visualization
- Exportable audit reports (PDF/Markdown + data)

## Scaling & Deployment

- Laptop / single GPU: Toy + small ensemble runs
- Cluster / cloud: Full ACE/Earth2Studio + thousands of agents via Ray or Dask
- Future: Decentralized compute contributions (inspired by other open science projects)

## Interoperability with External Digital Twins

OpenGaia is designed from the ground up to couple with, ingest from, and build upon existing Earth digital twin efforts rather than compete with them. This section documents the planned integration patterns.

### Integration Strategy

The coupling engine and module interfaces support three levels of interoperability:

#### Level 1: Output Ingestion (Offline Coupling)

External systems produce outputs (e.g., climate fields from DestinE, NASA ESDT, or Earth2Studio) which OpenGaia ingests as pre-computed forcing data. This is the simplest pattern:

```
External System → NetCDF/Zarr files → OpenGaia Data Adapter → WorldState
```

The adapter transforms external data schemas into OpenGaia's WorldState coordinates (time, region, variable). This enables "what-if" analysis using real high-fidelity outputs without requiring OpenGaia to run a climate model.

#### Level 2: Loose Online Coupling

OpenGaia runs in parallel with an external twin, exchanging data at configurable intervals:

```
OpenGaia (socio-economics + coupling) ←→ External Twin (physics)
         ↓                                      ↑
    WorldState  ──periodic sync──→  Adapter → External API
```

The adapter handles unit conversion, regridding, and temporal interpolation. This pattern matches how operational centers couple atmosphere, ocean, and land models in modern ESMs.

#### Level 3: Tight Coupling (Native Module)

An external system is wrapped as an OpenGaia `step(state, dt)` module. This is the target pattern for Earth2Studio integration:

```python
from opengaia.adapters.earth2studio import Earth2StudioModule
engine.register_module("climate", Earth2StudioModule( model="e2s", device="cuda" ), order=0)
```

### Adapter Architecture

The `adapters/` directory will contain reference implementations:

| Adapter | Status | Description |
|---------|--------|-------------|
| `earth2studio` | Planned | Wrap NVIDIA Earth2Studio pipelines as OpenGaia modules |
| `ace_climate` | Planned | Wrap AllenAI ACE climate emulator |
| `destine` | Exploratory | Ingest DestinE output datasets |
| `nasa_esdt` | Exploratory | Interface with NASA ESDT outputs |

Each adapter implements a common `BaseAdapter` interface providing:
- `load(config)`: Initialize from config or checkpoint
- `to_worldstate(data)`: Transform external data → WorldState fields
- `from_worldstate(state)`: Extract boundary conditions for external system
- `step(state, dt)`: When used as a live module

### Design Principles

1. **Minimal coupling surface**: Adapters translate between external schemas and WorldState, keeping integration complexity bounded.
2. **Versioned interfaces**: External data schemas and OpenGaia WorldState both evolve; adapters document compatibility.
3. **Testing with synthetic data**: Each adapter ships with lightweight test fixtures so integration can be validated without access to the external system.
4. **Community contributions welcome**: Adapters for new external systems can be contributed independently of the core engine.

## Next Architectural Milestones

## Current Module Status (v0.2)

| Module | Status | Description |
|--------|--------|-------------|
| `core/` | **Implemented** | Coupling engine with WorldState, ordered module orchestration |
| `physics_bio/` | **Stub** (toy backend) | Climate enulator interface; placeholder for ACE/Earth2Studio |
| `socio_economic/` | **Implemented** | Heterogeneous agents, regions, demographics, migration, WorldEconomy |
| `tech_innovation/` | **Implemented** | S-curve tech diffusion, AI capability model, R&D investment |
| `safety_sandbox/` | **Implemented** | AI agent insertion, alignment metrics, policy interventions |
| `data/` | Empty stub | Data ingestion, synthetic generators |
| `eval/` | Empty stub | Validation, benchmarks, UQ |
| `ui_viz/` | Empty stub | Interactive dashboard, NL interface |

## Key New Features in v0.2

### Socio-Economic Agent Module
- `Agent` class with heterogeneous attributes (risk aversion, adaptability, education)
- `Region` class with economic dynamics, inequality, and agent population
- `WorldEconomy` container with trade networks and global aggregation
- `Demographics` with fertility, mortality, and urbanization dynamics
- `MigrationModel` driven by economic, environmental, and conflict factors

### Technology & Innovation Module
- `Technology` with S-curve adoption dynamics and learning rates
- `TechDiffusionModel` for multi-technology diffusion with spillovers
- `AICapabilityModel` tracking capability, alignment, compute, and governance
- `RDInvestmentModel` with knowledge accumulation and diminishing returns

### Safety Sandbox
- `AIAgent` with configurable motivations (cooperation, power-seeking, deception, etc.)
- `SafetySandbox` for agent insertion, step, and trace collection
- `AlignmentMetrics` tracking risk score, deception, power concentration
- `InterventionRegistry` with 5 built-in policy interventions

- v0.2: Real xarray WorldState + first ACE integration
- v0.5: Dependency-aware coupling + full ensemble support
- v1.0: Production safety sandbox + NL query interface + published validation benchmarks

See `roadmap.md` for timeline and `governance.md` for decision process around major changes.