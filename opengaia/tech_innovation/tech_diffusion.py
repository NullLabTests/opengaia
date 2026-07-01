from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import numpy as np


@dataclass
class Technology:
    """A technology with S-curve adoption dynamics."""

    name: str
    adoption_rate: float = 0.01
    max_penetration: float = 1.0
    current_penetration: float = 0.001
    growth_rate: float = 0.1
    efficiency: float = 0.3
    learning_rate: float = 0.05

    def step(self, rd_investment: float, adaptability: float = 0.5, dt: float = 1.0) -> float:
        remaining = self.max_penetration - self.current_penetration
        if remaining < 1e-6:
            return 0.0
        base_diffusion = self.growth_rate * self.current_penetration * remaining
        rd_boost = rd_investment * self.learning_rate * (1.0 - self.current_penetration)
        adaptability_factor = 0.5 + adaptability * 0.5
        delta = (base_diffusion + rd_boost) * adaptability_factor * dt
        self.current_penetration = min(self.max_penetration, self.current_penetration + delta)
        self.efficiency = min(1.0, self.efficiency + self.learning_rate * rd_investment * dt)
        return delta


@dataclass
class TechDiffusionModel:
    """Manages multiple technologies and their diffusion across regions."""

    technologies: Dict[str, Technology] = field(default_factory=dict)
    global_rd: float = 0.02
    spillover_rate: float = 0.1

    def register(self, tech: Technology) -> None:
        self.technologies[tech.name] = tech

    def step(self, regional_rd: Dict[int, float] = None, dt: float = 1.0) -> Dict[str, float]:
        deltas = {}
        for name, tech in self.technologies.items():
            rd = self.global_rd
            if regional_rd:
                rd += np.mean(list(regional_rd.values())) * self.spillover_rate
            delta = tech.step(rd_investment=rd, dt=dt)
            deltas[name] = delta
        return deltas

    def get_adoption_vector(self) -> Dict[str, float]:
        return {name: tech.current_penetration for name, tech in self.technologies.items()}
