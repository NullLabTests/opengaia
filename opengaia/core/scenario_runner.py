"""Scenario runner: parses YAML configs and drives CouplingEngine runs."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import yaml

import numpy as np

from .coupling_engine import WorldState, CouplingEngine, toy_climate_step, toy_socio_step
from .xarray_state import XarrayWorldState


SCHEMA = {
    "name": str,
    "description": str,
    "climate": {
        "backend": str,
        "ssp_scenario": str,
        "initial_year": int,
        "end_year": int,
    },
    "socio_economic": dict,
    "safety_sandbox": dict,
    "output": dict,
    "monte_carlo": dict,
}


def _validate_schema(data: dict, schema: dict, path: str = "") -> None:
    """Recursively validate YAML config keys and types against schema."""
    for key, expected_type in schema.items():
        full_path = f"{path}.{key}" if path else key
        if key not in data:
            continue  # optional keys are allowed
        val = data[key]
        if isinstance(expected_type, dict):
            if not isinstance(val, dict):
                raise ValueError(
                    f"'{full_path}' should be a mapping (got {type(val).__name__})"
                )
            _validate_schema(val, expected_type, full_path)
        elif expected_type is dict:
            if not isinstance(val, dict):
                raise ValueError(
                    f"'{full_path}' should be a mapping (got {type(val).__name__})"
                )
        else:
            if not isinstance(val, expected_type):
                raise ValueError(
                    f"'{full_path}' should be {expected_type.__name__} "
                    f"(got {type(val).__name__})"
                )


_KNOWN_BACKENDS: Dict[str, str] = {}  # backend name -> adapter module


def _resolve_backend(
    backend: str,
) -> Callable[[WorldState, float], None]:
    """Resolve climate backend name -> step function with fallback chain.

    Tries registered adapter packages in priority order.  If *backend* is not
    recognised by any adapter, falls back to the toy step and emits a warning.
    """
    if backend == "toy":
        return toy_climate_step

    adapters: List[Callable[[], Optional[Callable[[WorldState, float], None]]]] = []

    def _try_earth2studio() -> Optional[Callable[[WorldState, float], None]]:
        try:
            from opengaia.adapters.earth2studio import Earth2StudioAdapter

            adapter = Earth2StudioAdapter(model_name=backend)
            diag = adapter.get_diagnostics()
            if diag["backend"] == "stub":
                return None  # earth2studio not installed, cannot verify
            return adapter.step  # type: ignore[return-value]
        except ImportError:
            return None

    adapters.append(_try_earth2studio)

    for factory in adapters:
        fn = factory()
        if fn is not None:
            return fn

    import warnings

    warnings.warn(
        f"Climate backend '{backend}' not available — falling back to 'toy'. "
        f"Install the required adapter package (e.g. earth2studio) to use this backend.",
        stacklevel=2,
    )
    return toy_climate_step


@dataclass
class ScenarioResult:
    """Typed result from a scenario run."""

    scenario: str
    n_runs: int
    years: int
    initial_year: int
    final_year: int
    final_temp_anomaly: float
    final_temps: List[float] = field(default_factory=list)
    output_dir: Optional[Path] = None

    @property
    def summary(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario,
            "n_runs": self.n_runs,
            "years": self.years,
            "initial_year": self.initial_year,
            "final_year": self.final_year,
            "final_temp_anomaly": round(self.final_temp_anomaly, 4),
            "final_temps": [round(t, 4) for t in self.final_temps],
            "output_dir": str(self.output_dir) if self.output_dir else None,
        }


class ScenarioConfig:
    """Loads, validates, and exposes a scenario YAML config."""

    def __init__(self, path: Path):
        self.path = Path(path)
        with open(self.path) as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raise ValueError(
                f"Expected a YAML mapping at top level (got {type(raw).__name__})"
            )
        self.data: Dict[str, Any] = raw
        self._validate()

    def _validate(self) -> None:
        _validate_schema(self.data, SCHEMA)
        required = ["name", "climate"]
        for key in required:
            if key not in self.data:
                raise ValueError(f"Missing required config key: '{key}'")
        climate = self.data.get("climate", {})
        if climate.get("initial_year", 2026) >= climate.get("end_year", 2100):
            raise ValueError(
                f"climate.initial_year ({climate.get('initial_year')}) must be "
                f"< climate.end_year ({climate.get('end_year')})"
            )

    @property
    def name(self) -> str:
        return str(self.data.get("name", "Unnamed Scenario"))

    @property
    def description(self) -> str:
        return str(self.data.get("description", ""))

    @property
    def climate_backend(self) -> str:
        return str(self.data.get("climate", {}).get("backend", "toy"))

    @property
    def initial_year(self) -> int:
        return int(self.data.get("climate", {}).get("initial_year", 2026))

    @property
    def end_year(self) -> int:
        return int(self.data.get("climate", {}).get("end_year", 2100))

    @property
    def years(self) -> int:
        return self.end_year - self.initial_year

    @property
    def socio_economic(self) -> Dict[str, Any]:
        val = self.data.get("socio_economic", {})
        return val if isinstance(val, dict) else {}

    @property
    def safety_sandbox(self) -> Dict[str, Any]:
        val = self.data.get("safety_sandbox", {})
        return val if isinstance(val, dict) else {}

    @property
    def output(self) -> Dict[str, Any]:
        val = self.data.get("output", {})
        return val if isinstance(val, dict) else {}

    @property
    def monte_carlo(self) -> Dict[str, Any]:
        val = self.data.get("monte_carlo", {})
        return val if isinstance(val, dict) else {}


def build_engine(config: ScenarioConfig) -> CouplingEngine:
    """Construct and register modules described by the config."""
    engine = CouplingEngine()
    engine.register_module("climate", _resolve_backend(config.climate_backend), order=0)
    engine.register_module("socio", toy_socio_step, order=1)

    sc = config.safety_sandbox
    if sc.get("enabled", False):
        from opengaia.safety_sandbox.sandbox import SafetySandbox, AIAgent, AgentMotivation

        sandbox = SafetySandbox()
        capabilities = sc.get("agent_capabilities", [0.5])
        motivations = sc.get("agent_motivations", ["cooperation"])
        mot_map = {
            "cooperation": AgentMotivation.COOPERATION,
            "power_seeking": AgentMotivation.POWER_SEEKING,
            "deception": AgentMotivation.DECEPTION,
        }
        for i, cap in enumerate(capabilities):
            for m_str in motivations:
                mot = mot_map.get(m_str, AgentMotivation.COOPERATION)
                sandbox.insert_agent(
                    AIAgent(
                        agent_id=f"agent_{i}_{m_str}",
                        capability_level=float(cap),
                        motivation=mot,
                        alignment_score=1.0 - float(cap) * 0.3,
                    )
                )
        engine.register_module("safety_sandbox", sandbox.step, order=2)  # type: ignore[arg-type]

    return engine


def build_state(
    config: ScenarioConfig,
    use_xarray: bool = False,
    n_regions: int = 1,
    n_ensemble: int = 1,
) -> Union[WorldState, XarrayWorldState]:
    """Create a WorldState from scenario config defaults.

    When *use_xarray* is True, returns an :class:`XarrayWorldState` instead
    of the lightweight dataclass.  The coupling engine's toy module step
    functions expect the dataclass interface, so xarray mode is best used
    with xarray-aware modules (coming in v0.5+).
    """
    if use_xarray:
        from .xarray_state import XarrayWorldState

        return XarrayWorldState.from_config(
            n_timesteps=config.years + 1,
            n_regions=n_regions,
            n_ensemble=n_ensemble,
            initial_year=config.initial_year,
        )
    return WorldState(year=config.initial_year)


def run_scenario(
    config: ScenarioConfig,
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None,
    use_xarray: bool = False,
) -> ScenarioResult:
    """Execute a scenario and return a typed result.

    Parameters
    ----------
    config:
        Parsed scenario configuration.
    output_dir:
        If set, write summary JSON and optional CSV files here.
    seed:
        Random seed for reproducibility.
    use_xarray:
        If True, use :class:`XarrayWorldState` instead of the dataclass.
    """
    if seed is not None:
        np.random.seed(seed)

    engine = build_engine(config)
    state = build_state(config, use_xarray=use_xarray)
    state.record({"scenario": config.name})

    engine.run(state, steps=config.years)  # type: ignore[arg-type]

    mc = config.monte_carlo
    n_runs = mc.get("runs", 1) if mc else 1
    histories: List[Any] = [state.history]  # type: ignore[union-attr]
    if n_runs > 1:
        for run in range(1, n_runs):
            engine = build_engine(config)
            state = build_state(config, use_xarray=use_xarray)
            state.record({"scenario": config.name, "mc_run": run})
            engine.run(state, steps=config.years)  # type: ignore[arg-type]
            histories.append(state.history)  # type: ignore[union-attr]

    final_temps = [h[-1]["temp_anomaly"] for h in histories]

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        import json

        summary = {
            "scenario": config.name,
            "years": config.years,
            "initial_year": config.initial_year,
            "n_runs": n_runs,
            "final_temps": final_temps,
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        out_cfg = config.output
        if out_cfg.get("save_csv", False):
            import pandas as pd

            for i, hist in enumerate(histories):
                df = pd.DataFrame(hist)
                suffix = f"_run{i}" if n_runs > 1 else ""
                df.to_csv(output_dir / f"{config.path.stem}{suffix}.csv", index=False)

    return ScenarioResult(
        scenario=config.name,
        n_runs=n_runs,
        years=config.years,
        initial_year=config.initial_year,
        final_year=config.initial_year + config.years,
        final_temp_anomaly=sum(final_temps) / len(final_temps),
        final_temps=final_temps,
        output_dir=output_dir,
    )
