"""xarray-backed WorldState for v0.5+.

Replaces the lightweight dataclass WorldState with an xarray.Dataset
providing labeled dimensions (time, variable, region, ensemble_member)
and efficient array operations for multi-region, multi-variable state.

Usage:
    state = XarrayWorldState.from_config(n_timesteps=100)
    state.update(temp_anomaly=np.array([...]))
    df = state.to_dataframe()
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union

import numpy as np
import xarray as xr


class XarrayWorldState:
    """Shared simulation state backed by an xarray.Dataset.

    Default coordinates:
      - time:        integer timestep counter
      - variable:    named state variables (temp_anomaly, cumulative_emissions, ...)
      - region:      region index (scalar for global, multi for regional)
      - ensemble:    ensemble member index

    This class is the migration target for v0.5; the dataclass ``WorldState``
    will be deprecated in favor of this once all modules support array inputs.
    """

    _DEFAULT_VARIABLES = [
        "temp_anomaly",
        "cumulative_emissions",
        "total_population",
        "total_gdp",
        "avg_ag_productivity",
    ]

    def __init__(self, dataset: xr.Dataset):
        self._ds = dataset
        self._t = 0

    @classmethod
    def from_config(
        cls,
        n_timesteps: int = 1,
        n_regions: int = 1,
        n_ensemble: int = 1,
        initial_year: int = 2026,
        variables: Optional[List[str]] = None,
        init_values: Optional[Dict[str, float]] = None,
    ) -> XarrayWorldState:
        """Create an XarrayWorldState with given dimensions and initial values.

        Args:
            n_timesteps: Number of timesteps to pre-allocate.
            n_regions: Number of regions (1 = global).
            n_ensemble: Number of ensemble members.
            initial_year: Starting year (stored as scalar coord).
            variables: List of variable names.
            init_values: Dict of {variable: initial_value} overrides.
        """
        vars_list = variables or cls._DEFAULT_VARIABLES

        coord_time = np.arange(n_timesteps, dtype=int)
        coord_region = np.arange(n_regions, dtype=int)
        coord_ensemble = np.arange(n_ensemble, dtype=int)

        data_vars: Dict[str, Any] = {}
        for var in vars_list:
            data_vars[var] = xr.DataArray(
                data=np.full((n_timesteps, n_regions, n_ensemble), np.nan),
                dims=["time", "region", "ensemble"],
                coords={
                    "time": coord_time,
                    "region": coord_region,
                    "ensemble": coord_ensemble,
                },
                attrs={"units": "", "long_name": var},
            )

        ds = xr.Dataset(
            data_vars=data_vars,
            coords={
                "time": coord_time,
                "region": coord_region,
                "ensemble": coord_ensemble,
                "year": initial_year,
            },
            attrs={"description": "OpenGaia XarrayWorldState"},
        )

        init_values = init_values or {
            "temp_anomaly": 0.0,
            "cumulative_emissions": 0.0,
            "total_population": 1250.0,
            "total_gdp": 85000.0,
            "avg_ag_productivity": 1.0,
        }

        for var, val in init_values.items():
            if var in ds:
                ds[var].loc[{"time": 0}] = val

        obj = cls(ds)
        obj._t = 0
        return obj

    @property
    def t(self) -> int:
        return self._t

    @t.setter
    def t(self, value: int) -> None:
        self._t = value

    @property
    def year(self) -> int:
        return int(self._ds.coords["year"].values)

    @year.setter
    def year(self, value: int) -> None:
        self._ds.coords["year"] = value

    @property
    def dataset(self) -> xr.Dataset:
        return self._ds

    def update(
        self,
        data: Dict[str, Union[float, np.ndarray]],
        region: int = 0,
        ensemble: int = 0,
    ) -> None:
        """Set values at current timestep for one or more variables."""
        for var, val in data.items():
            if var in self._ds:
                self._ds[var].loc[{"time": self._t, "region": region, "ensemble": ensemble}] = val
            else:
                raise KeyError(f"Unknown variable: {var}")

    def get(self, var: str, region: int = 0, ensemble: int = 0) -> np.ndarray:
        """Get a variable timeseries for a given region and ensemble."""
        return np.asarray(self._ds[var].sel(region=region, ensemble=ensemble).values)

    def record(self, extra: Optional[Dict[str, Any]] = None) -> None:
        """Advance to next timestep (in-place)."""
        if self._t + 1 < self._ds.sizes["time"]:
            self._t += 1
            self._ds.coords["year"] = self.year + 1
            for var in self._ds.data_vars:
                self._ds[var].loc[{"time": self._t}] = self._ds[var].loc[{"time": self._t - 1}]

    def to_dataframe(self) -> Any:
        """Flatten to a pandas DataFrame for export."""
        return self._ds.to_dataframe()

    def to_dict(self) -> Dict[str, Any]:
        """Return current state values as a flat dict."""
        return {
            str(var): float(self._ds[str(var)].isel(time=self._t).mean().values)
            for var in self._ds.data_vars
        }

    def __repr__(self) -> str:
        return f"XarrayWorldState(t={self._t}, year={self.year}, vars={list(self._ds.data_vars)})"
