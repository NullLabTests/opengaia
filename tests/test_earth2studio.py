import numpy as np
from opengaia.adapters.earth2studio import Earth2StudioAdapter
from opengaia.core.coupling_engine import WorldState


class TestEarth2StudioAdapterInit:
    def test_stub_init(self):
        adapter = Earth2StudioAdapter(model_name="e2s_dlwp")
        assert adapter.model_name == "e2s_dlwp"
        assert adapter._loaded is True
        assert adapter._earth2studio_available is False

    def test_earth2studio_not_available_raises(self):
        try:
            Earth2StudioAdapter(earth2studio_available=True)
            assert False, "Expected ImportError"
        except ImportError:
            pass


class TestEarth2StudioAdapterStep:
    def test_stub_step_updates_state(self):
        adapter = Earth2StudioAdapter()
        state = WorldState()
        initial_temp = state.temp_anomaly
        adapter.step(state, dt=1.0)
        assert state.temp_anomaly != initial_temp

    def test_stub_step_multiple_timesteps(self):
        adapter = Earth2StudioAdapter()
        state = WorldState(cumulative_emissions=100.0)
        for _ in range(5):
            adapter.step(state, dt=1.0)
        assert state.temp_anomaly != 0.0


class TestEarth2StudioAdapterConversion:
    def test_state_to_worldstate_with_temp(self):
        adapter = Earth2StudioAdapter()
        state_dict = {
            "2m_temperature": np.full((1, 1, 721, 1440), 290.0),
        }
        state = adapter.state_to_worldstate(state_dict, year=2026)
        assert state.year == 2026
        expected_anomaly = 290.0 - 273.15 - 14.5  # 2.35
        assert abs(state.temp_anomaly - expected_anomaly) < 0.01

    def test_state_to_worldstate_without_temp(self):
        adapter = Earth2StudioAdapter()
        state_dict: dict = {}
        state = adapter.state_to_worldstate(state_dict, year=2026)
        assert state.year == 2026

    def test_worldstate_to_state_returns_dict(self):
        adapter = Earth2StudioAdapter()
        state = WorldState(temp_anomaly=2.0)
        result = adapter.worldstate_to_state(state)
        assert "2m_temperature" in result
        assert result["2m_temperature"].shape == (1, 1, 721, 1440)

    def test_get_diagnostics(self):
        adapter = Earth2StudioAdapter()
        diag = adapter.get_diagnostics()
        assert diag["model"] == "e2s_dlwp"
        assert diag["backend"] == "stub"
