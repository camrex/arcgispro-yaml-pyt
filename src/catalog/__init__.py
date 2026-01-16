"""
Catalog management system for YAML-based ArcGIS Pro tools.

This package provides functionality for managing tool collections:
- Organizing tools from multiple sources (Git, local, network)
- Creating and managing toolboxes
- Assigning tools to toolboxes
- Validating catalog configurations
- Discovering tools from sources
- Generating .pyt files from toolboxes

The catalog system is separate from the framework runtime - it's a developer/admin
tool for managing which tools go where, while the framework loads and executes them.
"""

from .discovery import (
    DiscoveredTool,
    DiscoveredToolbox,
    DiscoveryError,
    DiscoveryService,
    GitError,
)
from .generator import (
    GeneratorError,
    GeneratorService,
    ResolvedTool,
    ToolLoadError,
    ToolNotFoundError,
)
from .models import (
    Catalog,
    CatalogSettings,
    Source,
    SourceType,
    Toolbox,
    ToolReference,
)
from .service import (
    CatalogError,
    CatalogNotFoundError,
    CatalogService,
    CatalogValidationError,
)

__all__ = [
    # Schema models
    "Catalog",
    "CatalogSettings",
    "Source",
    "SourceType",
    "ToolReference",
    "Toolbox",
    # Service
    "CatalogService",
    # Discovery
    "DiscoveryService",
    "DiscoveredTool",
    "DiscoveredToolbox",
    # Generator
    "GeneratorService",
    "ResolvedTool",
    # Exceptions
    "CatalogError",
    "CatalogNotFoundError",
    "CatalogValidationError",
    "DiscoveryError",
    "GeneratorError",
    "GitError",
    "ToolLoadError",
    "ToolNotFoundError",
]
