from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np


@dataclass
class AICapabilityModel:
    """Models AI capability progress, deployment, and governance interactions.

    Tracks capability index, compute investment, research velocity,
    alignment level, and governance regime effects.
    """

    capability_index: float = 0.2
    compute_investment: float = 1.0
    research_velocity: float = 0.3
    alignment_level: float = 0.3
    deployment_breadth: float = 0.1
    governance_effectiveness: float = 0.3
    # History for analysis
    history: List[Dict] = field(default_factory=list)

    def step(
        self,
        global_rd: float,
        governance: float = 0.3,
        safety_investment: float = 0.01,
        dt: float = 1.0,
    ) -> Dict[str, float]:
        self.governance_effectiveness = 0.5 * self.governance_effectiveness + 0.5 * governance
        compute_growth = 0.2 * (1.0 + global_rd * 2) - self.governance_effectiveness * 0.05
        self.compute_investment *= 1.0 + compute_growth * dt
        capability_growth = (
            0.1
            + 0.05 * np.log(1.0 + self.compute_investment)
            - 0.02 * self.governance_effectiveness
        )
        self.capability_index = min(1.0, self.capability_index + capability_growth * dt)
        self.research_velocity = min(1.0, self.research_velocity + 0.02 * global_rd * dt)
        align_growth = safety_investment * 0.5 - self.capability_index * 0.02 * (
            1.0 - self.governance_effectiveness
        )
        self.alignment_level = np.clip(self.alignment_level + align_growth * dt, 0.01, 1.0)
        self.deployment_breadth = min(
            1.0, self.deployment_breadth + self.capability_index * 0.05 * dt
        )
        self.history.append(
            {
                "capability": self.capability_index,
                "alignment": self.alignment_level,
                "compute": self.compute_investment,
                "governance": self.governance_effectiveness,
            }
        )
        return {
            "capability_growth": capability_growth,
            "alignment_change": align_growth,
            "compute_growth": compute_growth,
        }
