# Writing an OpenGaia Module

This tutorial walks through creating a new module that plugs into the CouplingEngine.

## Overview

A module in OpenGaia is any Python callable with the signature:

```python
def my_step(state: WorldState, dt: float) -> None:
    """Read from *state*, compute updates, write back to *state*."""
```

The coupling engine calls registered modules in order every timestep. Modules communicate *only* through the shared `WorldState` — no direct calls between modules.

## Tutorial: A Simple Renewable Energy Module

Let's build a module that models renewable energy adoption as a function of GDP and climate policy.

### 1. Create the file

Place your module at `opengaia/tech_innovation/renewables.py`:

```python
"""Renewable energy adoption module for OpenGaia."""

from __future__ import annotations
from opengaia.core.coupling_engine import WorldState


# Module-level parameters (tunable via config later)
_ADOPTION_RATE = 0.08    # base annual adoption growth
_MAX_SHARE = 0.95        # max fraction of energy from renewables
_POLICY_SENSITIVITY = 0.3


def renewables_step(state: WorldState, dt: float = 1.0) -> None:
    """Update renewable energy share based on GDP and policy.

    Expects ``state.metadata`` to contain:
      - ``policy_strength`` (float, 0–1): how aggressive climate policy is.
    """
    gdp = state.total_gdp
    policy = state.metadata.get("policy_strength", 0.0)

    current_share = state.metadata.get("renewable_share", 0.1)
    growth = _ADOPTION_RATE * (1 + policy * _POLICY_SENSITIVITY) * dt
    new_share = min(_MAX_SHARE, current_share + growth * (1 - current_share))

    state.metadata["renewable_share"] = new_share
    # Reduce emissions proportionally to renewable share
    state.cumulative_emissions *= max(0.05, 1.0 - new_share * 0.3 * dt)
```

### 2. Register it with the engine

```python
from opengaia.core.coupling_engine import CouplingEngine, WorldState
from opengaia.tech_innovation.renewables import renewables_step

engine = CouplingEngine()
engine.register_module("climate", toy_climate_step, order=0)
engine.register_module("renewables", renewables_step, order=1)
engine.register_module("socio", toy_socio_step, order=2)

state = WorldState()
state.metadata["policy_strength"] = 0.7
engine.run(state, steps=30)
print(state.metadata.get("renewable_share"))
```

### 3. Test it

```python
# tests/test_renewables.py
from opengaia.core.coupling_engine import WorldState
from opengaia.tech_innovation.renewables import renewables_step

def test_renewables_increases_share():
    state = WorldState(total_gdp=100000)
    state.metadata["policy_strength"] = 0.5
    for _ in range(10):
        renewables_step(state, dt=1.0)
    share = state.metadata.get("renewable_share", 0.0)
    assert share > 0.1, f"Expected share > 0.1, got {share}"
```

### 4. Add to a scenario YAML

```yaml
name: "Renewable Energy Scenario"
climate:
  backend: "toy"
  initial_year: 2026
  end_year: 2060
tech_innovation:
  renewable_adoption_rate: 0.08
  policy_sensitivity: 0.3
```

Then modify ``build_engine`` in ``scenario_runner.py`` to read ``tech_innovation`` config and register your new step function.

## Interface Contract

| Aspect | Requirement |
|--------|-------------|
| Signature | `fn(state: WorldState, dt: float) -> None` |
| Side effects | Modify ``state`` in-place only |
| State reading | Read any field; never write fields owned by other modules without coordination |
| Determinism | Output must depend only on ``state`` + ``dt`` + module's own config |

## Tips

- **Keep it stateless**: Store configuration in the module, not in global variables.
- **Use metadata for module-specific fields**: Avoid adding fields to `WorldState` for every new module.
- **Test with the toy backend**: Your module should work regardless of which climate backend is active.
- **Add uncertainty**: If your module has known unknowns, add random variation that can be controlled by seed.

## Next Steps

- Look at existing modules in `opengaia/socio_economic/` and `opengaia/tech_innovation/` for real examples.
- Read `docs/architecture.md` for the full coupling design.
- Submit your module as a PR — we'd love to have it!
