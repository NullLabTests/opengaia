from opengaia.core.xarray_state import XarrayWorldState


class TestXarrayWorldStateInit:
    def test_from_config_defaults(self):
        state = XarrayWorldState.from_config(n_timesteps=10)
        assert state.t == 0
        assert state.year == 2026
        assert state.dataset.sizes["time"] == 10
        assert state.dataset.sizes["region"] == 1
        assert state.dataset.sizes["ensemble"] == 1

    def test_from_config_custom_dims(self):
        state = XarrayWorldState.from_config(
            n_timesteps=50, n_regions=5, n_ensemble=3, initial_year=2030
        )
        assert state.year == 2030
        assert state.dataset.sizes["region"] == 5
        assert state.dataset.sizes["ensemble"] == 3

    def test_from_config_init_values(self):
        state = XarrayWorldState.from_config(
            n_timesteps=5,
            init_values={"temp_anomaly": 1.5, "total_gdp": 90000.0},
        )
        val = state.dataset["temp_anomaly"].isel(time=0, region=0, ensemble=0).item()
        assert abs(val - 1.5) < 0.01
        val = state.dataset["total_gdp"].isel(time=0, region=0, ensemble=0).item()
        assert abs(val - 90000.0) < 0.01


class TestXarrayWorldStateUpdate:
    def test_update_single_variable(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        state.update({"temp_anomaly": 2.5})
        stored = state.dataset["temp_anomaly"].isel(time=0, region=0, ensemble=0).item()
        assert abs(stored - 2.5) < 0.01

    def test_update_multiple_variables(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        state.update({"temp_anomaly": 1.0, "total_gdp": 90000.0})
        val = state.dataset["temp_anomaly"].isel(time=0, region=0, ensemble=0).item()
        assert abs(val - 1.0) < 0.01
        val = state.dataset["total_gdp"].isel(time=0, region=0, ensemble=0).item()
        assert abs(val - 90000.0) < 0.01

    def test_update_unknown_variable_raises(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        try:
            state.update({"unknown_var": 0.0})
            assert False, "Expected KeyError"
        except KeyError:
            pass


class TestXarrayWorldStateRecord:
    def test_record_advances_time(self):
        state = XarrayWorldState.from_config(n_timesteps=10)
        state.update({"temp_anomaly": 0.5})
        state.record()
        assert state.t == 1
        assert state.year == 2027

    def test_record_copies_previous_values(self):
        state = XarrayWorldState.from_config(n_timesteps=10)
        state.update({"temp_anomaly": 2.0})
        state.record()
        val_at_t1 = state.dataset["temp_anomaly"].isel(time=1, region=0, ensemble=0).item()
        assert abs(val_at_t1 - 2.0) < 0.01


class TestXarrayWorldStateGet:
    def test_get_timeseries(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        state.update({"temp_anomaly": 1.0})
        state.record()
        state.update({"temp_anomaly": 2.0})
        series = state.get("temp_anomaly")
        assert len(series) == 5

    def test_to_dataframe(self):
        state = XarrayWorldState.from_config(n_timesteps=3, n_regions=2)
        df = state.to_dataframe()
        assert len(df) == 3 * 2  # timesteps * regions

    def test_to_dict(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        state.update({"temp_anomaly": 1.5, "total_gdp": 90000.0})
        d = state.to_dict()
        assert "temp_anomaly" in d
        assert "total_gdp" in d

    def test_repr(self):
        state = XarrayWorldState.from_config(n_timesteps=5)
        r = repr(state)
        assert "XarrayWorldState" in r
        assert "t=0" in r
