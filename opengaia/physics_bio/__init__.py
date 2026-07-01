"""Physics, biology, and ecology modules for OpenGaia.

Primary goal: Provide high-fidelity yet fast Earth system components
that can be tightly coupled to socio-economic and technology layers.

Recommended backends (swap-in):
- AllenAI ACE (ai2cm/ace) for fast atmospheric emulation
- NVIDIA Earth2Studio models for high-resolution weather/climate
- HybridESM techniques for physics-ML hybrids
- Simple process models or emulators for carbon cycle, ecosystems, etc.
"""

from .climate_emulator import ClimateEmulator  # placeholder

__all__ = ["ClimateEmulator"]
