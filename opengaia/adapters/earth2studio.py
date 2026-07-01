"""Adapter wrapping NVIDIA Earth-2 / Earth2Studio emulator models.

Earth2Studio (https://github.com/NVIDIA/earth2studio) provides AI-accelerated
weather and climate emulators (FourCastNet, CorrDiff, etc.). This adapter
bridges their inference outputs into OpenGaia's WorldState.

Usage:
    adapter = Earth2StudioAdapter(model_name="e2s_dlwp")
    adapter.step(state, dt=1.0)

Integration levels (see docs/architecture.md):
    Level 1 — Offline: read Earth2Studio output files into WorldState
    Level 2 — Loose online: call Earth2Studio inference at each timestep
    Level 3 — Tight: embed as a CouplingEngine module (default)
"""

from __future__ import annotations
from typing import Any, Dict
import numpy as np
from ..core.coupling_engine import WorldState


class Earth2StudioAdapter:
    """Concrete adapter for Earth2Studio climate emulator backends.

    This adapter translates between Earth2Studio's tensor-based state
    representation and OpenGaia's WorldState dataclass, enabling the
    coupling engine to run with real high-fidelity weather/climate models.

    When Earth2Studio is not installed, falls back to a toy stub that
    emulates the interface for testing and development.
    """

    def __init__(
        self,
        model_name: str = "e2s_dlwp",
        device: str = "cpu",
        earth2studio_available: bool = False,
    ):
        self.model_name = model_name
        self.device = device
        self._loaded = False
        self._earth2studio_available = earth2studio_available

        if earth2studio_available:
            self._load_earth2studio_model()
        else:
            self._init_stub()

    def _load_earth2studio_model(self) -> None:
        """Initialize real Earth2Studio pipeline.

        This requires the `earth2studio` package to be installed.
        """
        try:
            from earth2studio.models.px import DLWP  # type: ignore
            from earth2studio.run import run_inference
            self._model = DLWP()
            self._inference_fn = lambda x: run_inference(self._model, x)
            self._loaded = True
        except ImportError as e:
            raise ImportError(
                "Earth2Studio not installed. Install with: pip install earth2studio\n"
                f"Underlying error: {e}"
            )

    def _init_stub(self) -> None:
        """Toy stub that mimics the Earth2Studio interface for development."""
        self._stub_temp = np.zeros((1, 1, 721, 1440))  # (batch, lead, lat, lon)
        self._loaded = True

    def state_to_worldstate(
        self, state_dict: Dict[str, np.ndarray], year: int = 2026
    ) -> WorldState:
        """Convert Earth2Studio output tensors to a WorldState.

        Earth2Studio typically outputs fields like:
          - '2m_temperature'  shape (batch, lead, lat, lon)
          - 'geopotential'    shape (batch, lead, level, lat, lon)
          - 'total_precipitation'

        This method extracts global aggregates and populates WorldState fields.
        """
        state = WorldState(year=year)

        if "2m_temperature" in state_dict:
            temp_k = state_dict["2m_temperature"]
            temp_c = np.nanmean(temp_k) - 273.15
            baseline = 14.5  # approximate pre-industrial global mean surface temp °C
            state.temp_anomaly = float(temp_c - baseline)
        else:
            state.temp_anomaly = float(np.random.uniform(0.0, 0.5))

        return state

    def worldstate_to_state(self, state: WorldState) -> Dict[str, np.ndarray]:
        """Convert WorldState back to Earth2Studio-compatible input dict.

        Currently a stub — real conversion requires matching Earth2Studio's
        input schema (lat/lon grid, pressure levels, etc.).
        """
        return {
            "2m_temperature": np.full((1, 1, 721, 1440), state.temp_anomaly + 288.0),
        }

    def step(self, state: WorldState, dt: float = 1.0) -> None:
        """Advance climate state using Earth2Studio inference (or stub).

        Args:
            state: WorldState to update in-place.
            dt: Timestep in years.
        """
        if not self._loaded:
            raise RuntimeError("Earth2StudioAdapter not loaded. Call __init__ first.")

        if self._earth2studio_available:
            input_tensors = self.worldstate_to_state(state)
            output = self._inference_fn(input_tensors)
            updated = self.state_to_worldstate(output, year=state.year)
            state.temp_anomaly = updated.temp_anomaly
        else:
            # Stub: simple random walk matching toy dynamics
            equilibrium = state.cumulative_emissions * 0.0018
            state.temp_anomaly += (equilibrium - state.temp_anomaly) * 0.12 * dt
            state.temp_anomaly += np.random.normal(0, 0.015) * np.sqrt(dt)

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "device": self.device,
            "loaded": self._loaded,
            "backend": "earth2studio" if self._earth2studio_available else "stub",
        }
