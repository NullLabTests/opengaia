"""Socio-economic agent-based modeling module for OpenGaia.

Heterogeneous agents with realistic demographics, economic behavior,
social networks, migration, and institutional dynamics.
"""

from .agents import Agent, Region, WorldEconomy
from .demographics import Demographics
from .migration import MigrationModel

__all__ = ["Agent", "Region", "WorldEconomy", "Demographics", "MigrationModel"]
