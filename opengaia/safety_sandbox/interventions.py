from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Callable
from .sandbox import SafetySandbox


@dataclass
class Intervention:
    """A policy intervention that modifies sandbox dynamics."""

    name: str
    description: str
    effect_fn: Callable[[SafetySandbox], None]
    cost: float = 0.0
    effectiveness: float = 0.5
    applied: bool = False

    def apply(self, sandbox: SafetySandbox) -> None:
        self.effect_fn(sandbox)
        self.applied = True


@dataclass
class InterventionRegistry:
    """Registry of predefined interventions."""

    interventions: Dict[str, Intervention] = field(default_factory=dict)

    def __post_init__(self):
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            Intervention(
                name="capability_limiting",
                description="Limit maximum capability of inserted agents",
                effect_fn=lambda s: [
                    setattr(a, "capability_level", min(a.capability_level, 0.5))
                    for a in s.agents.values()
                ],
                cost=0.2,
                effectiveness=0.7,
            )
        )
        self.register(
            Intervention(
                name="alignment_training",
                description="Apply alignment pressure to all agents",
                effect_fn=lambda s: [
                    setattr(a, "alignment_score", min(1.0, a.alignment_score + 0.05))
                    for a in s.agents.values()
                ],
                cost=0.3,
                effectiveness=0.5,
            )
        )
        self.register(
            Intervention(
                name="transparency_mandate",
                description="Force agents to expose their decision logic",
                effect_fn=lambda s: [
                    setattr(a, "deception_capability", max(0.0, a.deception_capability - 0.1))
                    for a in s.agents.values()
                ],
                cost=0.1,
                effectiveness=0.4,
            )
        )
        self.register(
            Intervention(
                name="resource_rationing",
                description="Limit resource access for all agents",
                effect_fn=lambda s: [
                    setattr(a, "resource_access", min(a.resource_access, 0.3))
                    for a in s.agents.values()
                ],
                cost=0.15,
                effectiveness=0.6,
            )
        )
        self.register(
            Intervention(
                name="kill_switch",
                description="Immediately deactivate all agents",
                effect_fn=lambda s: s.agents.clear(),
                cost=0.0,
                effectiveness=1.0,
            )
        )

    def register(self, intervention: Intervention) -> None:
        self.interventions[intervention.name] = intervention

    def get(self, name: str) -> Intervention:
        if name not in self.interventions:
            raise KeyError(
                f"Intervention '{name}' not found. Available: {list(self.interventions.keys())}"
            )
        return self.interventions[name]
