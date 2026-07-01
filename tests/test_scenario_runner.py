import yaml

from opengaia.core.scenario_runner import ScenarioConfig, build_engine, build_state, run_scenario
from opengaia.core.coupling_engine import WorldState, CouplingEngine


SAMPLE_CONFIG = {
    "name": "Test Scenario",
    "description": "A test scenario for unit tests",
    "climate": {
        "backend": "toy",
        "initial_year": 2026,
        "end_year": 2036,
    },
    "socio_economic": {
        "n_regions": 3,
    },
}


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


def test_scenario_config_validates(tmp_path):
    config_path = tmp_path / "bad_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"description": "no name or climate"}, f)
    try:
        ScenarioConfig(config_path)
        assert False, "Expected ValueError"
    except ValueError:
        pass


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


def test_run_scenario(tmp_path):
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(SAMPLE_CONFIG, f)
    sc = ScenarioConfig(config_path)
    result = run_scenario(sc, output_dir=tmp_path, seed=42)
    assert result["scenario"] == "Test Scenario"
    assert result["n_runs"] == 1
    assert isinstance(result["final_temp"], float)
    assert (tmp_path / "summary.json").exists()


def test_run_scenario_monte_carlo(tmp_path):
    config = dict(SAMPLE_CONFIG)
    config["monte_carlo"] = {"runs": 3, "seeds": [42], "variables": {}}
    config_path = tmp_path / "mc_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    sc = ScenarioConfig(config_path)
    result = run_scenario(sc, output_dir=tmp_path, seed=42)
    assert result["n_runs"] == 3


def test_run_scenario_saves_csv(tmp_path):
    config = dict(SAMPLE_CONFIG)
    config["output"] = {"save_csv": True}
    config_path = tmp_path / "csv_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    sc = ScenarioConfig(config_path)
    run_scenario(sc, output_dir=tmp_path, seed=42)
    csv_files = list(tmp_path.glob("csv_config*.csv"))
    assert len(csv_files) >= 1
