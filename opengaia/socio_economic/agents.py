from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np
from enum import Enum


class AgentType(Enum):
    SUBSISTENCE = "subsistence"
    WORKER = "worker"
    ENTREPRENEUR = "entrepreneur"
    INVESTOR = "investor"
    POLICYMAKER = "policymaker"


@dataclass
class Agent:
    """Individual agent with heterogeneous attributes and decision-making."""

    agent_id: int
    region_id: int
    agent_type: AgentType = AgentType.WORKER
    age: float = 30.0
    education: float = 0.5
    wealth: float = 10.0
    income: float = 5.0
    time_preference: float = 0.05
    risk_aversion: float = 0.5
    adaptability: float = 0.3
    social_connections: List[int] = field(default_factory=list)
    innovation_adoption: float = 0.0

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        income_change = np.random.normal(0.01 * self.education, 0.02)
        self.income *= 1.0 + income_change * dt
        savings = self.income * (1.0 - self.time_preference) * 0.1 * dt
        self.wealth += savings
        self.age += dt
        if self.innovation_adoption > 0:
            diffusion = self.adaptability * (1.0 - self.innovation_adoption)
            self.innovation_adoption += diffusion * 0.05 * dt
        return {"income_change": income_change, "savings": savings}

    def decide_migration(self, origin_conditions: float, dest_conditions: float) -> float:
        if origin_conditions < 0.5 and dest_conditions > 0.6:
            push = (0.5 - origin_conditions) * self.adaptability
            pull = (dest_conditions - 0.6) * (1.0 - self.risk_aversion)
            return min(1.0, max(0.0, push + pull - 0.2))
        return 0.0


@dataclass
class Region:
    """A geographic/administrative region with population and economy."""

    region_id: int
    name: str = ""
    population: float = 1.0
    gdp_per_capita: float = 10.0
    gini: float = 0.4
    human_capital: float = 0.5
    infrastructure: float = 0.5
    governance: float = 0.5
    environmental_quality: float = 1.0
    agents: List[Agent] = field(default_factory=list)
    tech_adoption: Dict[str, float] = field(default_factory=dict)

    @property
    def total_gdp(self) -> float:
        return self.population * self.gdp_per_capita

    def step_economy(self, dt: float = 1.0) -> Dict[str, float]:
        damage = max(0.0, 1.0 - self.environmental_quality)
        growth_base = 0.015 * self.human_capital * self.governance
        growth_penalty = damage * 0.03
        growth = max(-0.05, growth_base - growth_penalty + np.random.normal(0, 0.005))
        self.gdp_per_capita *= 1.0 + growth * dt
        self.infrastructure = min(1.0, self.infrastructure + 0.002 * self.governance * dt)
        self.human_capital = min(1.0, self.human_capital + 0.001 * self.gdp_per_capita / 50 * dt)
        self.gini = np.clip(
            self.gini + 0.001 * damage * dt - 0.0005 * self.governance * dt, 0.2, 0.9
        )
        return {"growth": growth, "damage": damage}

    def generate_agents(self, n: int = 100) -> None:
        types = [
            AgentType.SUBSISTENCE,
            AgentType.WORKER,
            AgentType.ENTREPRENEUR,
            AgentType.INVESTOR,
        ]
        probs = [0.2, 0.5, 0.2, 0.1]
        for i in range(n):
            agent = Agent(
                agent_id=i,
                region_id=self.region_id,
                agent_type=np.random.choice(types, p=probs),
                age=np.random.uniform(18, 80),
                education=float(np.clip(np.random.normal(self.human_capital, 0.15), 0, 1)),
                wealth=np.random.lognormal(mean=np.log(self.gdp_per_capita), sigma=self.gini),
                income=np.random.lognormal(
                    mean=np.log(self.gdp_per_capita * 0.1), sigma=self.gini * 0.5
                ),
                risk_aversion=np.random.uniform(0.1, 0.9),
                adaptability=np.random.uniform(0.1, 0.8),
            )
            agent.education = min(1.0, max(0.0, agent.education))
            self.agents.append(agent)


class WorldEconomy:
    """Container for multiple regions and global economic dynamics."""

    def __init__(self):
        self.regions: Dict[int, Region] = {}
        self.trade_network: np.ndarray = np.array([])
        self.global_gdp: float = 0.0
        self.global_inequality: float = 0.0

    def add_region(self, region: Region) -> None:
        self.regions[region.region_id] = region
        n = len(self.regions)
        if n > 1:
            new_size = (n, n)
            new_net = np.random.uniform(0.01, 0.3, new_size)
            new_net = (new_net + new_net.T) / 2
            np.fill_diagonal(new_net, 1.0)
            self.trade_network = new_net

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        for region in self.regions.values():
            region.step_economy(dt)
            for agent in region.agents[:5]:
                agent.step(dt)
        gdps = [r.total_gdp for r in self.regions.values()]
        self.global_gdp = sum(gdps) if gdps else 0.0
        if gdps:
            weights = [r.population for r in self.regions.values()]
            total_pop = sum(weights)
            if total_pop > 0:
                weighted_gdps = [g * w / total_pop for g, w in zip(gdps, weights)]
                mean_gdp = sum(weighted_gdps)
                variance = sum(w / total_pop * (g - mean_gdp) ** 2 for g, w in zip(gdps, weights))
                self.global_inequality = min(1.0, np.sqrt(variance) / (mean_gdp + 1e-6))
        emissions = sum(
            r.total_gdp * 0.0003 * max(0.2, 1.0 - r.tech_adoption.get("clean_energy", 0))
            for r in self.regions.values()
        )
        return {"emissions": emissions, "global_gdp": self.global_gdp}
