"""Scenario runner: parses YAML configs and drives CouplingEngine runs."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import yaml

import numpy as np

from .coupling_engine import WorldState, CouplingEngine, toy_climate_step, toy_socio_step


def _backend_step_fn(backend: str) -> Callable[[WorldState, float], None]:
    """Resolve a climate backend name to a step function."""
    if backend == "toy":
        return toy_climate_step
    try:
        import opengaia.adapters.earth2studio as e2s
        return e2s.Earth2StudioAdapter(model_name=backend).step  # type: ignore[return-value]
    except ImportError:
        raise ValueError(f"Unsupported climate backend: {backend}")


class ScenarioConfig:
    """Loads and validates a scenario YAML config."""

    def __init__(self, path: Path):
        self.path = Path(path)
        with open(self.path) as f:
            self.data: Dict[str, Any] = yaml.safe_load(f)
        self._validate()

    def _validate(self) -> None:
        required = ["name", "climate"]
        for key in required:
            if key not in self.data:
                raise ValueError(f"Missing required config key: {key}")

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
    engine.register_module("climate", _backend_step_fn(config.climate_backend), order=0)
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


def build_state(config: ScenarioConfig) -> WorldState:
    """Create a WorldState from scenario config defaults."""
    return WorldState(year=config.initial_year)


def run_scenario(
    config: ScenarioConfig,
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a scenario and return summary results."""
    if seed is not None:
        np.random.seed(seed)

    engine = build_engine(config)
    state = build_state(config)
    state.record({"scenario": config.name})

    engine.run(state, steps=config.years)

    mc = config.monte_carlo
    n_runs = mc.get("runs", 1) if mc else 1
    results_list = [state.history]
    if n_runs > 1:
        for run in range(1, n_runs):
            engine = build_engine(config)
            state = build_state(config)
            state.record({"scenario": config.name, "mc_run": run})
            engine.run(state, steps=config.years)
            results_list.append(state.history)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        import json
        summary = {
            "scenario": config.name,
            "years": config.years,
            "initial_year": config.initial_year,
            "n_runs": n_runs,
            "final_temps": [
                h[-1]["temp_anomaly"] for h in results_list
            ],
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        out_cfg = config.output
        if out_cfg.get("save_csv", False):
            import pandas as pd
            for i, hist in enumerate(results_list):
                df = pd.DataFrame(hist)
                suffix = f"_run{i}" if n_runs > 1 else ""
                df.to_csv(output_dir / f"{config.path.stem}{suffix}.csv", index=False)

    return {
        "scenario": config.name,
        "n_runs": n_runs,
        "final_temp": sum(h[-1]["temp_anomaly"] for h in results_list) / len(results_list),
    }
