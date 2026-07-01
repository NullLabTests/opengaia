"""Technology and innovation dynamics for OpenGaia.

Endogenous R&D progress, technology adoption curves, scientific discovery
feedback loops, and explicit modeling of AI capability trajectories.
"""

from .tech_diffusion import TechDiffusionModel, Technology
from .ai_capability import AICapabilityModel
from .rd_investment import RDInvestmentModel

__all__ = ["TechDiffusionModel", "Technology", "AICapabilityModel", "RDInvestmentModel"]
