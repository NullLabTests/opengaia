"""
OpenGaia: Open-source planetary-scale simulator for foresight and decision support.

This package provides the core framework for coupling Earth system models,
socio-economic agent-based simulations, technology dynamics, and safety research
in a modular, extensible way.

See README.md and docs/ for vision, architecture, and getting started.
"""

__version__ = "0.2.1"

from .core.coupling_engine import WorldState, CouplingEngine
from .core.coupling_engine import toy_climate_step, toy_socio_step
from .core.xarray_state import XarrayWorldState
from .adapters.earth2studio import Earth2StudioAdapter

__all__ = [
    "WorldState",
    "CouplingEngine",
    "toy_climate_step",
    "toy_socio_step",
    "XarrayWorldState",
    "Earth2StudioAdapter",
]
