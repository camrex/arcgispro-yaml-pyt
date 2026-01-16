"""Metadata Loader Tool (System Tool).

Utility tool to load and apply documentation metadata from YAML files
to tool XML metadata files. Run after updating documentation in YAML
configuration files to regenerate the .pyt.xml metadata files.
"""

from .execute import execute_metadata_loader

__all__ = ["execute_metadata_loader"]
