"""
Workspace management service for handling configurable workspace directories.

This service manages workspace initialization, validation, and configuration
to support flexible workspace locations for different projects and users.
"""

import shutil
from pathlib import Path

from src.catalog.models import Catalog, CatalogSettings


class WorkspaceError(Exception):
    """Base exception for workspace operations."""


class WorkspaceService:
    """Service for managing workspace directories and initialization."""

    def __init__(self, base_path: Path | None = None):
        """
        Initialize workspace service.

        Args:
            base_path: Base path for resolving relative workspace paths
        """
        self.base_path = base_path or Path.cwd()

    def get_default_workspace_path(self) -> Path:
        """Get the default workspace path."""
        return self.base_path / "workspace"

    def initialize_workspace(self, workspace_path: Path | None = None) -> Path:
        """
        Initialize workspace directory structure.

        Args:
            workspace_path: Custom workspace path, or None for default

        Returns:
            Path to the initialized workspace

        Raises:
            WorkspaceError: If workspace cannot be created
        """
        if workspace_path is None:
            workspace_path = self.get_default_workspace_path()

        try:
            # Create main workspace directory
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            subdirs = ["sources", "toolboxes", "catalogs"]
            for subdir in subdirs:
                (workspace_path / subdir).mkdir(exist_ok=True)

            # Create default catalog if it doesn't exist
            default_catalog_path = workspace_path / "catalogs" / "default.yml"
            if not default_catalog_path.exists():
                self._create_default_catalog(default_catalog_path)

            return workspace_path

        except Exception as e:
            raise WorkspaceError(f"Failed to initialize workspace at {workspace_path}: {e}")

    def validate_workspace(self, workspace_path: Path) -> list[str]:
        """
        Validate workspace directory structure.

        Args:
            workspace_path: Path to workspace to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        if not workspace_path.exists():
            issues.append(f"Workspace directory does not exist: {workspace_path}")
            return issues

        if not workspace_path.is_dir():
            issues.append(f"Workspace path is not a directory: {workspace_path}")
            return issues

        # Check for required subdirectories
        required_dirs = ["sources", "toolboxes", "catalogs"]
        for required_dir in required_dirs:
            dir_path = workspace_path / required_dir
            if not dir_path.exists():
                issues.append(f"Missing required directory: {required_dir}")
            elif not dir_path.is_dir():
                issues.append(f"Path exists but is not a directory: {required_dir}")

        # Check for default catalog
        default_catalog = workspace_path / "catalogs" / "default.yml"
        if not default_catalog.exists():
            issues.append("Missing default catalog file: catalogs/default.yml")

        return issues

    def migrate_current_structure(self, workspace_path: Path) -> None:
        """
        Migrate current examples structure to workspace structure.

        Args:
            workspace_path: Target workspace path
        """
        # Initialize workspace if needed
        self.initialize_workspace(workspace_path)

        # Move examples/sources to workspace/sources if exists
        examples_sources = self.base_path / "examples" / "sources"
        if examples_sources.exists():
            target_sources = workspace_path / "sources"

            # Copy each source directory
            for source_dir in examples_sources.iterdir():
                if source_dir.is_dir():
                    target_dir = target_sources / source_dir.name
                    if not target_dir.exists():
                        shutil.copytree(source_dir, target_dir)

        # Copy demo catalog to workspace/catalogs if exists
        demo_catalog = self.base_path / "examples" / "demo_catalog.yml"
        if demo_catalog.exists():
            target_catalog = workspace_path / "catalogs" / "demo.yml"
            if not target_catalog.exists():
                shutil.copy2(demo_catalog, target_catalog)

    def _create_default_catalog(self, catalog_path: Path) -> None:
        """Create a default catalog file."""
        default_catalog = Catalog(
            version="1.0",
            settings=CatalogSettings(
                workspace_path=catalog_path.parent.parent,
                auto_create_workspace=True,
                auto_sync=True,
            ),
            sources=[],
            toolboxes=[],
        )

        # Write catalog to file
        import yaml

        with open(catalog_path, "w") as f:
            # Convert to dict for YAML serialization
            catalog_dict = default_catalog.model_dump(mode="json", exclude_none=True)

            # Convert Path objects to strings for YAML
            if "settings" in catalog_dict and "workspace_path" in catalog_dict["settings"]:
                catalog_dict["settings"]["workspace_path"] = str(
                    catalog_dict["settings"]["workspace_path"]
                )

            yaml.dump(catalog_dict, f, default_flow_style=False, sort_keys=False)

    def get_catalog_paths(self, workspace_path: Path) -> list[Path]:
        """Get all catalog files in the workspace."""
        catalogs_dir = workspace_path / "catalogs"
        if not catalogs_dir.exists():
            return []

        return list(catalogs_dir.glob("*.yml"))

    def get_default_catalog_path(self, workspace_path: Path) -> Path:
        """Get the default catalog path for the workspace."""
        return workspace_path / "catalogs" / "default.yml"
