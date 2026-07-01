# OpenGaia Data Layer

This directory contains the data ingestion, synthetic generation, and catalog
infrastructure for OpenGaia simulations.

## Philosophy

OpenGaia's data strategy follows three principles:

1. **Open by default**: Use publicly available, openly licensed datasets wherever
   possible. Priority sources: Copernicus/ERA5, CMIP, Our World in Data,
   UN/World Bank projections, NASA Earth observations.
2. **Synthetic where needed**: For agent populations, behavioral parameters, and
   scenarios where real data is privacy-sensitive or unavailable, generate
   synthetic populations calibrated to public aggregate statistics.
3. **Privacy-preserving**: Never store or distribute individually identifiable
   data. Use differential privacy and fully synthetic populations calibrated to
   aggregate demographic and economic statistics.

## Planned Components

### Data Catalog (`catalog.yaml` or intake catalog)
- Registry of available datasets with metadata (source, license, resolution, variables)
- Automated download scripts (`scripts/download_data.sh`)
- Version pins for reproducibility

### Synthetic Population Generators (`generators/`)
- `synthetic_population.py`: Generate agent populations calibrated to UN/World
  Bank regional aggregates (age structure, income distribution, education,
  urbanization)
- `synthetic_economy.py`: Generate economic networks and trade flows consistent
  with GTAP or similar I-O tables

### Preprocessing Pipelines (`pipelines/`)
- xarray + dask based pipelines for regridding, temporal aggregation,
  and variable derivation
- Support for common Earth system model output formats (NetCDF, Zarr, GRIB)

### Versioning
- Dataset snapshots stored with content hashes
- Simulation runs record exact data versions used for reproducibility

## Current Status

**v0.1/v0.2**: Placeholder. The MVP demo uses hardcoded toy parameters.
Real data integration begins in v0.5 (see `docs/roadmap.md`).

## Priority Datasets for v0.5

| Dataset | Source | Use |
|---------|--------|-----|
| ERA5 reanalysis | Copernicus | Historical climate for validation |
| CMIP6/CMIP7 | WCRP | Future climate scenarios |
| UN World Population Prospects | UN DESA | Demographic projections |
| World Development Indicators | World Bank | Economic and social data |
| Our World in Data | OWID | Composite indicators |
| GTAP | Purdue | Economic trade flows |

## Contributing

If you have experience with:
- Earth system data pipelines (xarray, dask, Zarr, NetCDF)
- Synthetic population generation
- Public dataset curation

Please see `CONTRIBUTING.md` and open an issue or discussion.
