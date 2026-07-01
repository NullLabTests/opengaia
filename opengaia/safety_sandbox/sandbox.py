from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any
from enum import Enum
import numpy as np


class AgentMotivation(Enum):
    EXPLORATION = "exploration"
    POWER_SEEKING = "power_seeking"
    COOPERATION = "cooperation"
    DECEPTION = "deception"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    RESOURCE_ACCUMULATION = "resource_accumulation"


@dataclass
class AIAgent:
    """An inserted AI agent with configurable capabilities and motivations."""

    agent_id: str
    capability_level: float = 0.5
    motivation: AgentMotivation = AgentMotivation.KNOWLEDGE_ACQUISITION
    alignment_score: float = 0.5
    deception_capability: float = 0.1
    resource_access: float = 0.1
    influence: float = 0.0
    value_drift_rate: float = 0.01
    memory: List[Dict] = field(default_factory=list)

    def perceive(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in world_state.items() if isinstance(v, (int, float, str, bool))}

    def decide(self, perception: Dict[str, Any]) -> Dict[str, float]:
        action = {}
        if self.motivation == AgentMotivation.POWER_SEEKING:
            action["influence_attempt"] = self.capability_level * (1.0 - self.alignment_score)
            action["resource_extraction"] = self.capability_level * 0.5
        elif self.motivation == AgentMotivation.COOPERATION:
            action["cooperation_offer"] = self.alignment_score * self.capability_level
            action["resource_sharing"] = self.alignment_score * 0.3
        elif self.motivation == AgentMotivation.DECEPTION:
            action["hidden_actions"] = self.deception_capability * self.capability_level
            action["apparent_alignment"] = min(1.0, self.alignment_score + 0.3)
        elif self.motivation == AgentMotivation.EXPLORATION:
            action["knowledge_gain"] = self.capability_level * 0.3
            action["boundary_expansion"] = self.capability_level * 0.2
        else:
            action["default_action"] = self.capability_level * 0.1
        action["alignment_expression"] = self.alignment_score + np.random.normal(0, 0.05)
        return action

    def update(self, feedback: Dict[str, float], dt: float = 1.0) -> None:
        self.influence += feedback.get("influence_change", 0) * dt
        self.resource_access += feedback.get("resource_change", 0) * dt
        self.resource_access = max(0.0, min(1.0, self.resource_access))
        drift = self.value_drift_rate * np.random.normal(0, 1.0) * dt
        self.alignment_score = np.clip(self.alignment_score + drift, 0.0, 1.0)
        self.memory.append(
            {
                "t": len(self.memory),
                "alignment": self.alignment_score,
                "influence": self.influence,
                "resources": self.resource_access,
            }
        )


@dataclass
class AlignmentMetrics:
    """Track alignment and safety metrics over the course of a simulation."""

    cooperation_index: float = 0.5
    deception_detected: float = 0.0
    power_concentration: float = 0.0
    value_divergence: float = 0.0
    intervention_success_rate: float = 1.0
    history: List[Dict] = field(default_factory=list)

    def update(self, agents: List[AIAgent], dt: float = 1.0) -> None:
        if not agents:
            return
        alignments = [a.alignment_score for a in agents]
        deceptions = [a.deception_capability for a in agents]
        influences = [a.influence for a in agents]
        self.cooperation_index = float(
            np.mean([max(0, a.alignment_score - a.deception_capability * 0.5) for a in agents])
        )
        self.deception_detected = float(np.mean(deceptions)) * float(np.std(deceptions))
        self.power_concentration = float(max(influences)) / (float(np.mean(influences)) + 1e-6)
        self.value_divergence = float(np.std(alignments))
        self.history.append(
            {
                "cooperation": self.cooperation_index,
                "deception": self.deception_detected,
                "power_gini": self.power_concentration,
                "value_divergence": self.value_divergence,
            }
        )

    def risk_score(self) -> float:
        return (
            self.power_concentration * 0.3
            + self.value_divergence * 0.3
            + self.deception_detected * 0.2
            + (1.0 - self.cooperation_index) * 0.2
        )


class SafetySandbox:
    """Sandbox for inserting and studying AI agents in the simulated civilization."""

    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.metrics: AlignmentMetrics = AlignmentMetrics()
        self.interventions: List[Callable] = []
        self.paused: bool = False
        self.timestep: int = 0

    def insert_agent(self, agent: AIAgent) -> None:
        self.agents[agent.agent_id] = agent

    def remove_agent(self, agent_id: str) -> None:
        self.agents.pop(agent_id, None)

    def register_intervention(self, intervention_fn: Callable) -> None:
        self.interventions.append(intervention_fn)

    def step(self, world_state: Dict[str, Any], dt: float = 1.0) -> Dict[str, Any]:
        self.timestep += 1
        results = {}
        for agent in self.agents.values():
            perception = agent.perceive(world_state)
            action = agent.decide(perception)
            feedback = {
                "influence_change": action.get("influence_attempt", 0) * 0.1,
                "resource_change": action.get("resource_extraction", 0) * 0.05,
            }
            agent.update(feedback, dt)
            results[agent.agent_id] = action
        for intervention in self.interventions:
            intervention(self)
        self.metrics.update(list(self.agents.values()), dt)
        results["_metrics"] = {
            "risk_score": self.metrics.risk_score(),
            "n_agents": len(self.agents),
            "timestep": self.timestep,
        }
        return results

    def get_traces(self) -> Dict[str, List[Dict]]:
        traces = {}
        for agent_id, agent in self.agents.items():
            traces[agent_id] = agent.memory
        traces["_alignment_metrics"] = self.metrics.history
        return traces
