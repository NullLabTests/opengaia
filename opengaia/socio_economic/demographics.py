from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Demographics:
    """Population dynamics with age structure, fertility, mortality."""

    total_population: float = 8000.0
    fertility_rate: float = 2.3
    mortality_rate: float = 0.008
    life_expectancy: float = 72.0
    urbanization: float = 0.55
    dependency_ratio: float = 0.5
    education_index: float = 0.6

    def step(self, gdp_per_capita: float, temp_anomaly: float, dt: float = 1.0) -> float:
        damage = min(0.8, 0.02 * temp_anomaly**2)
        income_effect = max(0.5, min(3.0, 4.0 / (1.0 + gdp_per_capita / 30)))
        self.fertility_rate = income_effect * (1.0 + damage * 0.05 - self.education_index * 0.3)
        self.mortality_rate = 0.008 + damage * 0.01 - min(0.005, self.life_expectancy * 0.0001)
        self.mortality_rate = max(0.004, min(0.05, self.mortality_rate))
        births = self.total_population * self.fertility_rate / 80 * dt
        deaths = self.total_population * self.mortality_rate * dt
        self.total_population += births - deaths
        self.total_population = max(100.0, self.total_population)
        self.urbanization = min(0.95, self.urbanization + 0.002 * (1.0 + gdp_per_capita / 100) * dt)
        self.life_expectancy += (78.0 - self.life_expectancy) * 0.005 * dt - damage * 0.5 * dt
        return births - deaths
