"""Buffer Analysis Tool.

Creates buffer polygons around input features at a specified distance.
Supports multiple distance units and optional output dissolution.
"""

from .execute import execute_buffer

__all__ = ["execute_buffer"]
