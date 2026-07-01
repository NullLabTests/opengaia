"""Adapters for interoperability with external Earth digital twin systems.

Reference implementations for coupling OpenGaia with:
- NVIDIA Earth-2 / Earth2Studio (AI-accelerated climate models)
- AllenAI ACE (climate emulator)
- EU Destination Earth outputs
- NASA Earth System Digital Twins outputs

Each adapter translates between external data schemas and OpenGaia's WorldState,
enabling the coupling engine to run with real high-fidelity backends.
"""
