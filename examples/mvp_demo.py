#!/usr/bin/env python
"""
OpenGaia MVP Demo: Minimal Coupled Planetary Simulation

This demonstrates the core coupling concept with a toy model:
- Simple energy-balance climate (temperature responds to emissions + feedback)
- Agricultural productivity affected by temperature anomaly
- Heterogeneous agents (regions) that adapt, innovate, or migrate based on conditions
- Economy and population update with feedback to emissions
- Basic Monte Carlo mode for uncertainty

This is intentionally simplified for v0.1. Real versions will swap in
ACE/Earth2Studio for climate and more sophisticated grounded ABM for socio-economics.

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
    def __init__(self, years: int = 50, n_regions: int = 5, seed: int = 42):
        np.random.seed(seed)
        self.years = years
        self.n_regions = n_regions
        self.t = 0  # current year index

        # Climate state
        self.temp_anomaly = 0.0  # °C above pre-industrial
        self.cumulative_emissions = 0.0  # GtCO2e

        # Socio-economic state (per region)
        self.population = np.array([500.0, 300.0, 200.0, 150.0, 100.0])  # millions, toy
        self.gdp_per_capita = np.array([5.0, 15.0, 25.0, 40.0, 60.0])    # kUSD, toy
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
    """Very simple energy balance + carbon cycle toy model."""
    # Emissions add to cumulative and drive warming
    state.cumulative_emissions += emissions_this_year
    # Transient climate response (very rough)
    equilibrium_warming = state.cumulative_emissions * 0.002  # crude GtCO2e to °C
    # Inertia + feedback (positive for demo)
    state.temp_anomaly += (equilibrium_warming - state.temp_anomaly) * 0.15 + np.random.normal(0, 0.02)
    # Simple negative feedback from tech/policy (placeholder)
    if state.temp_anomaly > 2.0:
        state.temp_anomaly -= 0.01  # weak geoengineering-like response for demo


def step_socio_economic(state: WorldState, policy_strength: float = 0.5):
    """
    Agents (regions) respond to temperature and economic conditions.
    - Higher temp anomaly reduces ag productivity (non-linear)
    - Agents invest in adaptation/innovation or migrate
    - Affects emissions (economic activity) and future productivity
    """
    temp = state.temp_anomaly
    # Temperature damage function (convex, toy)
    damage = np.clip(0.02 * temp**2 + 0.01 * temp, 0, 0.8)
    state.ag_productivity = np.clip(state.ag_productivity * (1 - damage * 0.3), 0.3, 1.5)

    new_gdp = np.zeros_like(state.gdp_per_capita)
    new_pop = np.zeros_like(state.population)
    emissions = 0.0

    for i in range(state.n_regions):
        # Economic output affected by ag + baseline
        base_output = state.gdp_per_capita[i] * state.population[i]
        ag_effect = state.ag_productivity[i]
        output = base_output * (0.7 + 0.3 * ag_effect)

        # Agents "decide": invest fraction in innovation/adaptation
        invest_frac = 0.05 + 0.1 * policy_strength + np.random.uniform(-0.02, 0.02)
        innovation_boost = state.innovation_rate[i] * invest_frac * 10
        state.innovation_rate[i] = min(state.innovation_rate[i] * 1.01 + innovation_boost * 0.1, 0.08)

        # Simple migration: poor regions lose pop if damaged, rich gain (toy)
        if state.ag_productivity[i] < 0.7 and state.gdp_per_capita[i] < 20:
            migrate = state.population[i] * 0.02 * (1 - state.ag_productivity[i])
            state.population[i] -= migrate
            # Rich regions gain a bit
            if i < state.n_regions - 1:
                state.population[i+1] += migrate * 0.6

        # Update GDP/capita with growth + innovation - damage
        growth = 0.015 + state.innovation_rate[i] - damage * 0.5
        new_gdp[i] = state.gdp_per_capita[i] * (1 + growth)

        # Population dynamics (simplified, affected by conditions)
        fertility = max(0.008, 0.015 - 0.002 * state.gdp_per_capita[i] / 10)
        mortality = 0.008 + damage * 0.01
        new_pop[i] = state.population[i] * (1 + fertility - mortality)

        # Emissions from economic activity (declining intensity with innovation)
        intensity = max(0.3, 1.0 - state.innovation_rate[i] * 20)
        emissions += output * intensity * 0.0005  # crude scaling

    state.gdp_per_capita = new_gdp
    state.population = np.maximum(new_pop, 10.0)  # floor
    return emissions  # total emissions this step


def run_simulation(years: int = 30, n_regions: int = 5, policy_strength: float = 0.6,
                   monte_carlo: int = 1, seed: int = 42) -> Tuple[pd.DataFrame, Dict]:
    """Run one or more coupled simulations."""
    results = []
    final_stats = {"temp_final": [], "gdp_total_final": [], "pop_total_final": []}

    for mc in range(monte_carlo):
        state = WorldState(years=years, n_regions=n_regions, seed=seed + mc)
        state.record({"run": mc, "phase": "initial"})

        for t in range(years):
            state.t = t
            # Policy can increase over time (demo of ramping action)
            current_policy = min(1.0, policy_strength + t * 0.01)

            emissions = step_socio_economic(state, policy_strength=current_policy)
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
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Temperature
    for run in df["run"].unique():
        run_df = df[df["run"] == run]
        axes[0, 0].plot(run_df["year"], run_df["temp_anomaly"], alpha=0.6, label=f"Run {run}" if len(df["run"].unique()) < 5 else None)
    axes[0, 0].set_title("Temperature Anomaly (°C)")
    axes[0, 0].set_ylabel("°C above baseline")
    axes[0, 0].grid(True, alpha=0.3)
    if len(df["run"].unique()) < 5:
        axes[0, 0].legend()

    # Total GDP
    for run in df["run"].unique():
        run_df = df[df["run"] == run]
        axes[0, 1].plot(run_df["year"], run_df["total_gdp"] / 1000, alpha=0.6)
    axes[0, 1].set_title("Total GDP (trillion USD, toy units)")
    axes[0, 1].set_ylabel("Trillion $")
    axes[0, 1].grid(True, alpha=0.3)

    # Population
    for run in df["run"].unique():
        run_df = df[df["run"] == run]
        axes[1, 0].plot(run_df["year"], run_df["total_population"], alpha=0.6)
    axes[1, 0].set_title("Total Population (millions, toy)")
    axes[1, 0].set_ylabel("Millions")
    axes[1, 0].grid(True, alpha=0.3)

    # Ag productivity
    for run in df["run"].unique():
        run_df = df[df["run"] == run]
        axes[1, 1].plot(run_df["year"], run_df["avg_ag_productivity"], alpha=0.6)
    axes[1, 1].set_title("Average Agricultural Productivity (relative)")
    axes[1, 1].set_ylabel("Index (1.0 = baseline)")
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle(f"OpenGaia MVP Demo — {summary['n_runs']} run(s) | Final temp: {summary['mean_final_temp']:.2f}±{summary['std_final_temp']:.2f}°C", fontsize=14)
    plt.tight_layout()
    plt.savefig(out_dir / "mvp_demo_results.png", dpi=150, bbox_inches="tight")
    print(f"Plot saved to {out_dir / 'mvp_demo_results.png'}")


def main():
    parser = argparse.ArgumentParser(description="OpenGaia MVP Coupled Simulation Demo")
    parser.add_argument("--years", type=int, default=30, help="Simulation length in years")
    parser.add_argument("--monte-carlo", type=int, default=3, help="Number of Monte Carlo runs")
    parser.add_argument("--policy", type=float, default=0.6, help="Policy strength (0-1)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting")
    args = parser.parse_args()

    print("=== OpenGaia MVP Demo ===")
    print(f"Running {args.monte_carlo} simulation(s) for {args.years} years with policy={args.policy}...")

    df, summary = run_simulation(
        years=args.years,
        monte_carlo=args.monte_carlo,
        policy_strength=args.policy,
        seed=args.seed
    )

    print("\n--- Summary ---")
    print(f"Final temperature anomaly: {summary['mean_final_temp']:.2f} ± {summary['std_final_temp']:.2f} °C")
    print(f"Final total GDP (toy): {summary['mean_final_gdp'] / 1000:.1f} trillion USD units")
    print(f"Final total population (toy): {summary['mean_final_pop']:.0f} million")

    if not args.no_plot:
        plot_results(df, summary)

    # Save data
    out_path = Path("artifacts/mvp_demo_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nDetailed results saved to {out_path}")
    print("Demo complete. This is the seed — real modules will replace the toy dynamics.")


if __name__ == "__main__":
    main()