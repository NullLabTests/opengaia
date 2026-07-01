#!/usr/bin/env python
"""
OpenGaia MVP Demo: Minimal Coupled Planetary Simulation

This demonstrates the core coupling concept with a toy model:
- Simple energy-balance climate (temperature responds to emissions + feedback)
- Agricultural productivity affected by temperature anomaly
- Heterogeneous agents (regions) that adapt, innovate, or migrate based on conditions
- Economy and population update with feedback to emissions
- Basic Monte Carlo mode for uncertainty

This is intentionally simplified for v0.1. Key limitations that real modules will replace:
- Climate: Toy EBM → AllenAI ACE or NVIDIA Earth2Studio (see adapters/)
- Agents: Simple per-region dynamics → heterogeneous agent-based model (see socio_economic/)
- Data: Toy calibration → public datasets (UN, World Bank, Our World in Data)
- Validation: No historical backtesting → eval/ validation harness

Run:
    python -m examples.mvp_demo
    python -m examples.mvp_demo --monte-carlo 50 --years 30
"""

import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from pathlib import Path


# Simple WorldState for MVP (in real version this lives in core/)
class WorldState:
    """Minimal shared state for the MVP demo.

    In full OpenGaia this is backed by xarray.Dataset with proper coordinates
    (time, region, variable, ensemble_member) and serialization to Zarr/NetCDF.
    """

    def __init__(self, years: int = 50, n_regions: int = 5, seed: int = 42):
        np.random.seed(seed)
        self.years = years
        self.n_regions = n_regions
        self.t = 0  # current year index

        # Climate state
        self.temp_anomaly = 0.0  # °C above pre-industrial
        self.cumulative_emissions = 0.0  # GtCO2e

        # Socio-economic state (per region)
        # TODO: Replace with socio_economic Agent/Region classes
        self.population = np.array([500.0, 300.0, 200.0, 150.0, 100.0])  # millions, toy
        self.gdp_per_capita = np.array([5.0, 15.0, 25.0, 40.0, 60.0])  # kUSD, toy
        self.ag_productivity = np.ones(n_regions) * 1.0  # relative to baseline
        self.innovation_rate = np.array([0.01, 0.015, 0.02, 0.025, 0.03])  # per year

        # History for analysis
        self.history: List[Dict] = []

    def record(self, extra: Dict = None):
        record = {
            "year": 2026 + self.t,
            "temp_anomaly": self.temp_anomaly,
            "cumulative_emissions": self.cumulative_emissions,
            "total_population": self.population.sum(),
            "total_gdp": (self.population * self.gdp_per_capita).sum(),
            "avg_ag_productivity": self.ag_productivity.mean(),
        }
        if extra:
            record.update(extra)
        self.history.append(record)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.history)


def step_climate(state: WorldState, emissions_this_year: float, sensitivity: float = 0.8):
    """Very simple energy balance + carbon cycle toy model.

    This is a placeholder. Real implementation will delegate to:
    - AllenAI ACE (ai2cm/ace) for fast atmospheric emulation, OR
    - NVIDIA Earth2Studio pipelines (FourCastNet, CorrDiff), OR
    - Hybrid ESM combining physics with ML surrogates

    The interface is the same: given emissions, update temperature.
    """
    # Emissions add to cumulative stock and drive warming
    state.cumulative_emissions += emissions_this_year

    # Transient climate response (very rough approximation)
    # Real ECS is ~3°C per doubling CO2 (~600 GtC cumulative). Here we use 0.002 °C/GtCO2e.
    equilibrium_warming = state.cumulative_emissions * 0.002

    # Simple thermal inertia: temperature relaxes toward equilibrium with noise
    # Real climate models resolve ocean heat uptake, radiative forcing, feedbacks.
    state.temp_anomaly += (equilibrium_warming - state.temp_anomaly) * 0.15 + np.random.normal(
        0, 0.02
    )

    # Toy negative feedback from tech/policy (placeholder)
    # Real models represent this via endogenous mitigation, CDR, and adaptation.
    if state.temp_anomaly > 2.0:
        state.temp_anomaly -= 0.01  # weak geoengineering-like response for demo


def step_socio_economic(state: WorldState, policy_strength: float = 0.5):
    """
    Agents (regions) respond to temperature and economic conditions.

    This is a toy model. Real implementation swaps in the socio_economic module:
    - Agents with heterogeneous values, risk preferences, and decision rules
    - Calibrated to UN/World Bank demographics, economic accounts, innovation metrics
    - Markets, institutions, conflict dynamics, migration with behavioral grounding
    - Bidirectional feedback: societal states affect (and are affected by) climate

    Key dynamics illustrated here (simplified):
    - Higher temperature anomaly reduces agricultural productivity (convex damage)
    - Agents invest in adaptation/innovation proportional to policy strength
    - Migration flows from damaged poor regions to richer regions
    - Economic growth is penalized by climate damage
    - Emissions intensity declines with innovation over time
    """
    temp = state.temp_anomaly

    # Temperature damage function (convex, toy)
    # Real damage functions are highly uncertain — this is illustrative.
    # Literature range: Burke et al. (2015) ~quadratic, Kalkuhl & Wenz (2020) ~asymmetric.
    damage = np.clip(0.02 * temp**2 + 0.01 * temp, 0, 0.8)
    state.ag_productivity = np.clip(state.ag_productivity * (1 - damage * 0.3), 0.3, 1.5)

    new_gdp = np.zeros_like(state.gdp_per_capita)
    new_pop = np.zeros_like(state.population)
    emissions = 0.0

    for i in range(state.n_regions):
        # Economic output affected by agricultural productivity + baseline
        base_output = state.gdp_per_capita[i] * state.population[i]
        ag_effect = state.ag_productivity[i]
        output = base_output * (0.7 + 0.3 * ag_effect)

        # Agents "decide": invest fraction of output in innovation/adaptation
        # Real agents would have heterogeneous risk preferences and time horizons.
        invest_frac = 0.05 + 0.1 * policy_strength + np.random.uniform(-0.02, 0.02)
        innovation_boost = state.innovation_rate[i] * invest_frac * 10
        state.innovation_rate[i] = min(
            state.innovation_rate[i] * 1.01 + innovation_boost * 0.1, 0.08
        )

        # Simple migration: poor damaged regions lose population, richer regions gain
        # Real migration modeling (migration.py) includes economic, environmental, network effects.
        if state.ag_productivity[i] < 0.7 and state.gdp_per_capita[i] < 20:
            migrate = state.population[i] * 0.02 * (1 - state.ag_productivity[i])
            state.population[i] -= migrate
            # Adjacent richer region absorbs partial flow
            if i < state.n_regions - 1:
                state.population[i + 1] += migrate * 0.6

        # Update GDP/capita with growth + innovation - damage
        growth = 0.015 + state.innovation_rate[i] - damage * 0.5
        new_gdp[i] = state.gdp_per_capita[i] * (1 + growth)

        # Population dynamics (simplified, affected by environmental conditions)
        # Real demographics module includes age structure, fertility, mortality, urbanization.
        fertility = max(0.008, 0.015 - 0.002 * state.gdp_per_capita[i] / 10)
        mortality = 0.008 + damage * 0.01
        new_pop[i] = state.population[i] * (1 + fertility - mortality)

        # Emissions from economic activity (declining intensity with innovation)
        # Real models track energy mix, efficiency improvements, carbon pricing.
        intensity = max(0.3, 1.0 - state.innovation_rate[i] * 20)
        emissions += output * intensity * 0.0005

    state.gdp_per_capita = new_gdp
    state.population = np.maximum(new_pop, 10.0)  # minimum population floor
    return emissions


def run_simulation(
    years: int = 30,
    n_regions: int = 5,
    policy_strength: float = 0.6,
    monte_carlo: int = 1,
    seed: int = 42,
) -> Tuple[pd.DataFrame, Dict]:
    """Run one or more coupled simulations with Monte Carlo uncertainty.

    Each Monte Carlo run uses a different random seed and produces
    one trajectory. The combined results show uncertainty band evolution.
    """
    results = []
    final_stats = {"temp_final": [], "gdp_total_final": [], "pop_total_final": []}

    for mc in range(monte_carlo):
        state = WorldState(years=years, n_regions=n_regions, seed=seed + mc)
        state.record({"run": mc, "phase": "initial"})

        for t in range(years):
            state.t = t
            # Policy ramps over time, simulating increasing ambition
            current_policy = min(1.0, policy_strength + t * 0.01)

            # Socio-economic step happens first (emissions are output of economic activity)
            emissions = step_socio_economic(state, policy_strength=current_policy)

            # Climate step responds to this year's emissions
            step_climate(state, emissions_this_year=emissions)

            state.record({"run": mc, "phase": "step", "policy": current_policy})

        df = state.to_dataframe()
        df["run"] = mc
        results.append(df)

        final_stats["temp_final"].append(state.temp_anomaly)
        final_stats["gdp_total_final"].append((state.population * state.gdp_per_capita).sum())
        final_stats["pop_total_final"].append(state.population.sum())

    combined = pd.concat(results, ignore_index=True)

    summary = {
        "mean_final_temp": float(np.mean(final_stats["temp_final"])),
        "std_final_temp": float(np.std(final_stats["temp_final"])),
        "mean_final_gdp": float(np.mean(final_stats["gdp_total_final"])),
        "mean_final_pop": float(np.mean(final_stats["pop_total_final"])),
        "n_runs": monte_carlo,
    }

    return combined, summary


def plot_results(df: pd.DataFrame, summary: Dict, out_dir: Path = Path("artifacts")):
    """Generate 2x2 panel of key metrics over time.

    Each run is a separate trace. Monte Carlo runs show uncertainty spread.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    runs = df["run"].unique()
    n_runs = len(runs)

    # Temperature
    for run in runs:
        run_df = df[df["run"] == run]
        axes[0, 0].plot(
            run_df["year"],
            run_df["temp_anomaly"],
            alpha=0.6,
            label=f"Run {run}" if n_runs < 5 else None,
        )
    axes[0, 0].axhline(y=1.5, color="orange", linestyle="--", alpha=0.5, label="Paris 1.5°C")
    axes[0, 0].axhline(y=2.0, color="red", linestyle="--", alpha=0.5, label="Paris 2.0°C")
    axes[0, 0].set_title("Temperature Anomaly (°C)")
    axes[0, 0].set_ylabel("°C above pre-industrial")
    axes[0, 0].grid(True, alpha=0.3)
    if n_runs < 5:
        axes[0, 0].legend()

    # Total GDP
    for run in runs:
        run_df = df[df["run"] == run]
        axes[0, 1].plot(run_df["year"], run_df["total_gdp"] / 1000, alpha=0.6)
    axes[0, 1].set_title("Total GDP (trillion USD, toy units)")
    axes[0, 1].set_ylabel("Trillion $")
    axes[0, 1].grid(True, alpha=0.3)

    # Population
    for run in runs:
        run_df = df[df["run"] == run]
        axes[1, 0].plot(run_df["year"], run_df["total_population"], alpha=0.6)
    axes[1, 0].set_title("Total Population (millions, toy)")
    axes[1, 0].set_ylabel("Millions")
    axes[1, 0].grid(True, alpha=0.3)

    # Agricultural productivity
    for run in runs:
        run_df = df[df["run"] == run]
        axes[1, 1].plot(run_df["year"], run_df["avg_ag_productivity"], alpha=0.6)
    axes[1, 1].set_title("Average Agricultural Productivity (relative)")
    axes[1, 1].set_ylabel("Index (1.0 = baseline)")
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle(
        f"OpenGaia MVP Demo — {n_runs} run(s) | "
        f"Final temp: {summary['mean_final_temp']:.2f}±{summary['std_final_temp']:.2f}°C",
        fontsize=14,
    )
    plt.tight_layout()
    plt.savefig(out_dir / "mvp_demo_results.png", dpi=150, bbox_inches="tight")
    print(f"Plot saved to {out_dir / 'mvp_demo_results.png'}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenGaia MVP Coupled Simulation Demo — toy model for illustration"
    )
    parser.add_argument("--years", type=int, default=30, help="Simulation length in years")
    parser.add_argument("--monte-carlo", type=int, default=3, help="Number of Monte Carlo runs")
    parser.add_argument("--policy", type=float, default=0.6, help="Policy strength (0-1)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-plot", action="store_true", help="Skip matplotlib output")
    args = parser.parse_args()

    print("=" * 56)
    print("  OpenGaia MVP Demo — Coupled Planetary Simulation")
    print("  Toy model for illustration. Real modules replace each component.")
    print("=" * 56)
    print(f"  Runs:      {args.monte_carlo}")
    print(f"  Years:     {args.years}")
    print(f"  Policy:    {args.policy}")
    print(f"  Seed:      {args.seed}")
    print("-" * 56)

    df, summary = run_simulation(
        years=args.years,
        monte_carlo=args.monte_carlo,
        policy_strength=args.policy,
        seed=args.seed,
    )

    print("\n  Simulation Summary")
    print("-" * 56)
    print(
        f"  Final temperature anomaly:  {summary['mean_final_temp']:.2f} ± {summary['std_final_temp']:.2f} °C"
    )
    print(
        f"  Final total GDP (toy):      {summary['mean_final_gdp'] / 1000:.1f} trillion USD units"
    )
    print(f"  Final total population:     {summary['mean_final_pop']:.0f} million")
    print(f"  Monte Carlo runs:           {summary['n_runs']}")
    print("-" * 56)
    print("  Note: These are toy values. Real modules will replace")
    print("  the dynamics with calibrated, validated components.")
    print("=" * 56)

    if not args.no_plot:
        plot_results(df, summary)

    # Save data
    out_path = Path("artifacts/mvp_demo_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"  Detailed results → {out_path}")
    print("  Demo complete. Run 'opengaia demo socio' for the agent-based model.")


if __name__ == "__main__":
    main()
