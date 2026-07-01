from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RDInvestmentModel:
    """R&D investment dynamics with diminishing returns and spillovers."""

    global_rd_gdp_fraction: float = 0.02
    private_share: float = 0.6
    public_share: float = 0.4
    productivity_elasticity: float = 0.3
    cumulative_knowledge: float = 1.0
    depreciation_rate: float = 0.02
    sector_allocation: Dict[str, float] = field(
        default_factory=lambda: {
            "climate": 0.1,
            "health": 0.15,
            "energy": 0.15,
            "digital": 0.25,
            "materials": 0.1,
            "other": 0.25,
        }
    )

    def step(self, global_gdp: float, governance: float = 0.5, dt: float = 1.0) -> Dict[str, float]:
        rd_spending = global_gdp * self.global_rd_gdp_fraction * dt
        gov_efficiency = governance * self.public_share + self.private_share
        effective_rd = rd_spending * gov_efficiency
        knowledge_growth = (
            effective_rd**self.productivity_elasticity * self.cumulative_knowledge**0.5
        )
        knowledge_growth *= 0.001
        self.cumulative_knowledge = (
            self.cumulative_knowledge * (1.0 - self.depreciation_rate * dt) + knowledge_growth
        )
        productivity_boost = knowledge_growth / (self.cumulative_knowledge + 1e-6)
        return {
            "rd_spending": rd_spending,
            "effective_rd": effective_rd,
            "knowledge_growth": knowledge_growth,
            "productivity_boost": productivity_boost,
            "cumulative_knowledge": self.cumulative_knowledge,
        }
