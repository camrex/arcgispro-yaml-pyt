"""Clip Features Tool.

Extracts input features that overlap the clip features boundary.
Similar to cookie-cutter or spatial intersection operation.
"""

from .execute import execute_clip

__all__ = ["execute_clip"]
