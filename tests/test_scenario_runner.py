import copy

import yaml

from opengaia.core.scenario_runner import (
    ScenarioConfig,
    ScenarioResult,
    build_engine,
    build_state,
    run_scenario,
    _resolve_backend,
)
from opengaia.core.coupling_engine import WorldState, CouplingEngine, toy_climate_step


def _make_config(**overrides):
    """Deep-copy the base sample config so tests never mutate shared state."""
    base = {
        "name": "Test Scenario",
        "description": "A test scenario for unit tests",
        "climate": {
            "backend": "toy",
            "ssp_scenario": "SSP2-4.5",
            "initial_year": 2026,
            "end_year": 2036,
        },
        "socio_economic": {
            "n_regions": 3,
        },
    }
    return _deep_merge(base, overrides)


def _deep_merge(base: dict, overrides: dict) -> dict:
    result = copy.deepcopy(base)
    for k, v in overrides.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k].update(v)
        else:
            result[k] = v
    return result


SAMPLE_CONFIG = _make_config()


def test_scenario_config_loads(tmp_path):
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(SAMPLE_CONFIG, f)
    sc = ScenarioConfig(config_path)
    assert sc.name == "Test Scenario"
    assert sc.climate_backend == "toy"
    assert sc.initial_year == 2026
    assert sc.end_year == 2036
    assert sc.years == 10


class TestScenarioConfigValidation:
    def test_missing_name_raises(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"climate": {"backend": "toy", "initial_year": 2026, "end_year": 2030}}, f)
        import pytest
        with pytest.raises(ValueError, match="required config key"):
            ScenarioConfig(config_path)

    def test_missing_climate_raises(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"name": "Test"}, f)
        import pytest
        with pytest.raises(ValueError, match="required config key"):
            ScenarioConfig(config_path)

    def test_invalid_year_order_raises(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        data = _make_config(climate={"initial_year": 2050, "end_year": 2030})
        with open(config_path, "w") as f:
            yaml.dump(data, f)
        import pytest
        with pytest.raises(ValueError, match="initial_year"):
            ScenarioConfig(config_path)

    def test_invalid_climate_type_raises(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        data = _make_config(climate=["not", "a", "dict"])
        with open(config_path, "w") as f:
            yaml.dump(data, f)
        import pytest
        with pytest.raises(ValueError, match="mapping"):
            ScenarioConfig(config_path)

    def test_non_mapping_top_level_raises(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        with open(config_path, "w") as f:
            yaml.dump(["just", "a", "list"], f)
        import pytest
        with pytest.raises(ValueError):
            ScenarioConfig(config_path)


def test_build_engine_from_config(tmp_path):
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(SAMPLE_CONFIG, f)
    sc = ScenarioConfig(config_path)
    engine = build_engine(sc)
    assert isinstance(engine, CouplingEngine)
    assert "climate" in engine.modules
    assert "socio" in engine.modules


def test_build_state_from_config(tmp_path):
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(SAMPLE_CONFIG, f)
    sc = ScenarioConfig(config_path)
    state = build_state(sc)
    assert isinstance(state, WorldState)
    assert state.year == 2026


class TestScenarioResult:
    def test_dataclass_fields(self):
        result = ScenarioResult(
            scenario="test", n_runs=3, years=30, initial_year=2026,
            final_year=2056, final_temp_anomaly=2.5, final_temps=[2.4, 2.5, 2.6],
        )
        assert result.scenario == "test"
        assert result.n_runs == 3
        assert result.final_temp_anomaly == 2.5

    def test_summary_property(self):
        result = ScenarioResult(
            scenario="test", n_runs=1, years=10, initial_year=2026,
            final_year=2036, final_temp_anomaly=1.23, final_temps=[1.23],
        )
        s = result.summary
        assert s["scenario"] == "test"
        assert s["final_temp_anomaly"] == 1.23
        assert "output_dir" in s


class TestRunScenario:
    def test_basic_run(self, tmp_path):
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)
        sc = ScenarioConfig(config_path)
        result = run_scenario(sc, output_dir=tmp_path, seed=42)
        assert isinstance(result, ScenarioResult)
        assert result.scenario == "Test Scenario"
        assert result.n_runs == 1
        assert isinstance(result.final_temp_anomaly, float)
        assert (tmp_path / "summary.json").exists()

    def test_monte_carlo(self, tmp_path):
        config = _make_config(monte_carlo={"runs": 3, "seeds": [42], "variables": {}})
        config_path = tmp_path / "mc_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        sc = ScenarioConfig(config_path)
        result = run_scenario(sc, output_dir=tmp_path, seed=42)
        assert result.n_runs == 3
        assert len(result.final_temps) == 3

    def test_saves_csv(self, tmp_path):
        config = _make_config(output={"save_csv": True})
        config_path = tmp_path / "csv_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        sc = ScenarioConfig(config_path)
        run_scenario(sc, output_dir=tmp_path, seed=42)
        csv_files = list(tmp_path.glob("csv_config*.csv"))
        assert len(csv_files) >= 1


class TestResolveBackend:
    def test_toy_backend(self):
        fn = _resolve_backend("toy")
        assert fn == toy_climate_step

    def test_unknown_backend_falls_back_to_toy(self):
        fn = _resolve_backend("nonexistent_backend_xyz")
        assert fn == toy_climate_step


def test_sandbox_engine_integration(tmp_path):
    """Safety sandbox step receives dict, not WorldState — verify it runs end-to-end."""
    config_data = _make_config(
        safety_sandbox={
            "enabled": True,
            "agent_capabilities": [0.5],
            "agent_motivations": ["cooperation"],
        },
    )
    config_path = tmp_path / "sb_config.yaml"
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    config = ScenarioConfig(config_path)
    engine = build_engine(config)
    state = WorldState(year=2026)
    engine.run(state, steps=5)
    assert state.t == 5
    assert isinstance(state.history, list)
    assert len(state.history) == 5  # 5 steps, each records
