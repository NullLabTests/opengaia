from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Region


@dataclass
class MigrationModel:
    """Inter-region migration driven by economic, environmental, and conflict factors."""

    rates: Dict[str, float] = field(
        default_factory=lambda: {
            "economic_weight": 0.4,
            "environmental_weight": 0.3,
            "conflict_weight": 0.2,
            "network_weight": 0.1,
            "base_rate": 0.005,
            "max_rate": 0.15,
        }
    )

    def compute_flows(self, regions: Dict[int, "Region"], temp_anomaly: float) -> List[tuple]:
        flows = []
        region_ids = list(regions.keys())
        for src_id in region_ids:
            src = regions[src_id]
            env_stress = max(0.0, temp_anomaly * 0.1 - src.environmental_quality * 0.05)
            for dst_id in region_ids:
                if src_id == dst_id:
                    continue
                dst = regions[dst_id]
                econ_diff = (dst.gdp_per_capita - src.gdp_per_capita) / (dst.gdp_per_capita + 1)
                env_diff = dst.environmental_quality - src.environmental_quality
                push = (1.0 - src.governance) * 0.1 + env_stress
                pull = max(
                    0,
                    econ_diff * self.rates["economic_weight"]
                    + env_diff * self.rates["environmental_weight"],
                )
                flow_rate = self.rates["base_rate"] + push + pull
                flow_rate = min(self.rates["max_rate"], max(0.0, flow_rate))
                migrants = src.population * flow_rate
                if migrants > 1.0:
                    flows.append((src_id, dst_id, migrants))
        return flows

    def apply_flows(self, regions: Dict[int, "Region"], flows: List[tuple]) -> Dict[int, float]:
        net_changes = {rid: 0.0 for rid in regions}
        for src_id, dst_id, migrants in flows:
            net_changes[src_id] -= migrants
            net_changes[dst_id] += migrants
        for rid, change in net_changes.items():
            regions[rid].population = max(10.0, regions[rid].population + change)
        return net_changes
