"""
Core Coupling Engine for OpenGaia.

This module defines the shared WorldState and the orchestration layer
that allows physics_bio, socio_economic, tech_innovation, and safety_sandbox
modules to interact in a coherent, timestepped simulation.

Design goals for v0.1+:
- Simple, inspectable shared state (xarray-based in full version)
- Clear module interfaces (step(state, dt) -> updates)
- Support for both tight coupling and looser message-passing / latent interfaces
- Easy swapping of backends (toy -> ACE/Earth2Studio -> full ESM)

In the MVP we use a lightweight Python dataclass + dict history.
Real implementation will use xarray.Dataset for rich labeled multi-dimensional state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List, Optional
import numpy as np


@dataclass
class WorldState:
    """
    Shared state container for a simulation run.

    In production this will be backed by xarray.Dataset with proper
    coordinates (time, region, variable, ensemble_member, etc.) and
    history tracking for replay / branching.
    """

    t: int = 0  # current timestep
    year: int = 2026
    temp_anomaly: float = 0.0
    cumulative_emissions: float = 0.0
    # Socio-economic aggregates (scalars for MVP; arrays/regions later)
    total_population: float = 1250.0  # millions, toy
    total_gdp: float = 85000.0  # billion USD, toy
    avg_ag_productivity: float = 1.0
    # Extensible metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, extra: Optional[Dict[str, Any]] = None):
        rec = {
            "t": self.t,
            "year": self.year,
            "temp_anomaly": self.temp_anomaly,
            "cumulative_emissions": self.cumulative_emissions,
            "total_population": self.total_population,
            "total_gdp": self.total_gdp,
            "avg_ag_productivity": self.avg_ag_productivity,
        }
        if extra:
            rec.update(extra)
        self.history.append(rec)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "history"}


class CouplingEngine:
    """
    Orchestrates timestepping across registered modules.

    Modules register a `step` callable: def step(state: WorldState, dt: float) -> None
    The engine calls them in defined order each timestep and manages
    basic consistency / logging.
    """

    def __init__(self):
        self.modules: Dict[str, Callable[[WorldState, float], None]] = {}
        self.order: List[str] = []  # execution order

    def register_module(
        self, name: str, step_fn: Callable[[WorldState, float], None], order: Optional[int] = None
    ):
        self.modules[name] = step_fn
        if order is not None:
            # simplistic insertion; real version uses dependency graph
            self.order.insert(order, name)
        else:
            self.order.append(name)

    def step(self, state: WorldState, dt: float = 1.0):
        for name in self.order:
            if name in self.modules:
                self.modules[name](state, dt)
        state.t += 1
        state.year += 1
        state.record({"stepped_by": self.order})

    def run(self, state: WorldState, steps: int, dt: float = 1.0):
        for _ in range(steps):
            self.step(state, dt)
        return state


# Example toy module registration (used by MVP demo)
def toy_climate_step(state: WorldState, dt: float):
    # Extremely simplified
    emissions = max(0, (state.total_gdp / 100000) * (1.0 - 0.3 * (state.t / 50)))
    state.cumulative_emissions += emissions * dt
    equilibrium = state.cumulative_emissions * 0.0018
    state.temp_anomaly += (equilibrium - state.temp_anomaly) * 0.12 * dt + np.random.normal(
        0, 0.015
    )


def toy_socio_step(state: WorldState, dt: float):
    temp = state.temp_anomaly
    damage = min(0.6, 0.025 * temp**2)
    state.avg_ag_productivity = max(0.4, state.avg_ag_productivity * (1 - damage * 0.4))
    gdp_growth = 0.018 - damage * 0.6
    state.total_gdp *= 1 + gdp_growth * dt
    pop_growth = 0.006 - damage * 0.2
    state.total_population *= 1 + pop_growth * dt


if __name__ == "__main__":
    # Quick self-test
    engine = CouplingEngine()
    engine.register_module("climate", toy_climate_step, order=0)
    engine.register_module("socio", toy_socio_step, order=1)

    state = WorldState()
    state.record()
    engine.run(state, steps=20)
    print("CouplingEngine self-test complete.")
    print(f"Final temp anomaly: {state.temp_anomaly:.2f}°C")
    print(f"History length: {len(state.history)}")
