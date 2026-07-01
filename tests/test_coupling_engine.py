from opengaia.core.coupling_engine import (
    WorldState,
    CouplingEngine,
    toy_climate_step,
    toy_socio_step,
)


class TestWorldState:
    def test_initial_state(self):
        state = WorldState()
        assert state.t == 0
        assert state.year == 2026
        assert state.temp_anomaly == 0.0
        assert state.total_population > 0

    def test_record(self):
        state = WorldState()
        state.record()
        assert len(state.history) == 1
        assert state.history[0]["year"] == 2026

    def test_record_with_extra(self):
        state = WorldState()
        state.record({"test_key": "test_value"})
        assert state.history[0]["test_key"] == "test_value"


class TestCouplingEngine:
    def test_register_and_run(self):
        engine = CouplingEngine()
        engine.register_module("climate", toy_climate_step, order=0)
        engine.register_module("socio", toy_socio_step, order=1)
        state = WorldState()
        engine.run(state, steps=10)
        assert state.t == 10
        assert state.year == 2036
        assert len(state.history) == 10

    def test_step_order(self):
        engine = CouplingEngine()
        engine.register_module("b", lambda s, dt: None, order=1)
        engine.register_module("a", lambda s, dt: None, order=0)
        assert engine.order == ["a", "b"]

    def test_climate_step_modifies_state(self):
        state = WorldState()
        initial_temp = state.temp_anomaly
        toy_climate_step(state, 1.0)
        assert state.temp_anomaly != initial_temp

    def test_socio_step_modifies_state(self):
        state = WorldState()
        initial_pop = state.total_population
        toy_socio_step(state, 1.0)
        assert state.total_population != initial_pop
