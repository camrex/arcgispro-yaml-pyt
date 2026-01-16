"""
Catalog service for managing catalog.yml files.

Provides high-level operations for:
- Loading and saving catalogs
- Managing sources (add, remove, update)
- Managing toolboxes (add, remove, update)
- Managing tool assignments
- Validation and error checking
"""

import shutil
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.catalog.models import (
    Catalog,
    CatalogSettings,
    Source,
    SourceType,
    Toolbox,
    ToolReference,
)
from src.catalog.workspace import WorkspaceService


class CatalogError(Exception):
    """Base exception for catalog operations."""

    pass


class CatalogNotFoundError(CatalogError):
    """Catalog file not found."""

    pass


class CatalogValidationError(CatalogError):
    """Catalog validation failed."""

    pass


class CatalogService:
    """Service for managing catalog.yml files."""

    DEFAULT_VERSION = "1.0"

    def __init__(self, catalog_path: Path | None = None, workspace_path: Path | None = None):
        """
        Initialize catalog service.

        Args:
            catalog_path: Path to catalog.yml. If None, uses workspace default
            workspace_path: Path to workspace directory. If None, uses default
        """
        self.workspace_service = WorkspaceService()

        # Initialize workspace
        if workspace_path:
            self.workspace_path = workspace_path
        else:
            self.workspace_path = self.workspace_service.get_default_workspace_path()

        # Ensure workspace exists
        self.workspace_service.initialize_workspace(self.workspace_path)

        # Set catalog path
        if catalog_path:
            self.catalog_path = Path(catalog_path)
        else:
            self.catalog_path = self.workspace_service.get_default_catalog_path(self.workspace_path)

        self._catalog: Catalog | None = None

    @property
    def workspace(self) -> Path:
        """Get the workspace path."""
        return self.workspace_path

    def load(self) -> Catalog:
        """
        Load catalog from file.

        Returns:
            Catalog: Loaded and validated catalog

        Raises:
            CatalogNotFoundError: If catalog file doesn't exist
            CatalogValidationError: If catalog fails validation
        """
        if not self.catalog_path.exists():
            raise CatalogNotFoundError(f"Catalog not found: {self.catalog_path}")

        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self._catalog = Catalog(**data)
            return self._catalog

        except ValidationError as e:
            raise CatalogValidationError(f"Catalog validation failed: {e}") from e
        except yaml.YAMLError as e:
            raise CatalogValidationError(f"Invalid YAML: {e}") from e

    def save(self, catalog: Catalog | None = None, backup: bool = True) -> None:
        """
        Save catalog to file.

        Args:
            catalog: Catalog to save. If None, saves current loaded catalog
            backup: Whether to create backup before saving (default: True)

        Raises:
            CatalogError: If no catalog to save
        """
        if catalog is None:
            catalog = self._catalog

        if catalog is None:
            raise CatalogError("No catalog to save")

        # Update catalog settings with current workspace path if not set
        if not catalog.settings:
            catalog.settings = CatalogSettings()

        if not catalog.settings.workspace_path:
            catalog.settings.workspace_path = self.workspace_path

        # Create backup if file exists
        if backup and self.catalog_path.exists():
            self._create_backup()

        # Ensure parent directory exists
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save (use mode="json" to serialize enums and Paths)
        data = catalog.model_dump(mode="json", exclude_none=True)

        # Convert Path objects to strings for YAML
        if "settings" in data and "workspace_path" in data["settings"]:
            data["settings"]["workspace_path"] = str(data["settings"]["workspace_path"])

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        self._catalog = catalog

    def create_new(
        self, settings: CatalogSettings | None = None, overwrite: bool = False
    ) -> Catalog:
        """
        Create a new empty catalog.

        Args:
            settings: Optional catalog settings
            overwrite: Whether to overwrite existing catalog (default: False)

        Returns:
            Catalog: New empty catalog

        Raises:
            CatalogError: If catalog exists and overwrite=False
        """
        if self.catalog_path.exists() and not overwrite:
            raise CatalogError(
                f"Catalog already exists: {self.catalog_path}. Use overwrite=True to replace."
            )

        catalog = Catalog(version=self.DEFAULT_VERSION, settings=settings)
        self.save(catalog, backup=overwrite)
        return catalog

    def get_or_create(self) -> Catalog:
        """
        Get existing catalog or create new one if it doesn't exist.

        Returns:
            Catalog: Loaded or newly created catalog
        """
        try:
            return self.load()
        except CatalogNotFoundError:
            return self.create_new()

    # Source Management

    def add_source(
        self,
        id: str,
        name: str,
        type: SourceType,
        url: str | None = None,
        path: Path | None = None,
        local_path: Path | None = None,
        branch: str | None = "main",
        enabled: bool = True,
    ) -> Source:
        """
        Add a new source to the catalog.

        Args:
            id: Unique source identifier
            name: Human-readable name
            type: Source type (git, local, network)
            url: Git repository URL (required for git sources)
            path: Local/network path (required for local/network sources)
            local_path: Local storage path for git sources (auto-generated if not provided)
            branch: Git branch (default: main)
            enabled: Whether source is enabled (default: True)

        Returns:
            Source: The created source

        Raises:
            CatalogError: If source ID already exists or validation fails
        """
        catalog = self.get_or_create()

        # Check for duplicate ID
        if catalog.get_source_by_id(id):
            raise CatalogError(f"Source with id '{id}' already exists")

        # Create source
        source = Source(
            id=id,
            name=name,
            type=type,
            url=url,
            path=path,
            local_path=local_path,
            branch=branch,
            enabled=enabled,
        )

        catalog.sources.append(source)
        self.save(catalog)
        return source

    def remove_source(self, source_id: str, force: bool = False) -> None:
        """
        Remove a source from the catalog.

        Args:
            source_id: ID of source to remove
            force: If True, remove even if referenced by toolboxes (default: False)

        Raises:
            CatalogError: If source not found or still referenced
        """
        catalog = self.get_or_create()

        source = catalog.get_source_by_id(source_id)
        if not source:
            raise CatalogError(f"Source '{source_id}' not found")

        # Check if source is referenced by any toolbox
        if not force:
            for toolbox in catalog.toolboxes:
                for tool in toolbox.tools:
                    if tool.source_id == source_id:
                        raise CatalogError(
                            f"Source '{source_id}' is referenced by toolbox '{toolbox.id}'. "
                            "Remove tool assignments first or use force=True."
                        )

        catalog.sources.remove(source)
        self.save(catalog)

    def update_source(self, source_id: str, **updates) -> Source:
        """
        Update source properties.

        Args:
            source_id: ID of source to update
            **updates: Fields to update (name, enabled, last_sync, etc.)

        Returns:
            Source: Updated source

        Raises:
            CatalogError: If source not found
        """
        catalog = self.get_or_create()

        source = catalog.get_source_by_id(source_id)
        if not source:
            raise CatalogError(f"Source '{source_id}' not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)

        self.save(catalog)
        return source

    def get_source(self, source_id: str) -> Source | None:
        """Get source by ID."""
        catalog = self.get_or_create()
        return catalog.get_source_by_id(source_id)

    def list_sources(self, enabled_only: bool = False) -> list[Source]:
        """
        List all sources.

        Args:
            enabled_only: If True, only return enabled sources

        Returns:
            list[Source]: List of sources
        """
        catalog = self.get_or_create()
        if enabled_only:
            return catalog.get_enabled_sources()
        return catalog.sources

    # Toolbox Management

    def add_toolbox(
        self,
        id: str,
        name: str,
        path: Path,
        description: str | None = None,
        auto_regenerate: bool = True,
    ) -> Toolbox:
        """
        Add a new toolbox to the catalog.

        Args:
            id: Unique toolbox identifier
            name: Human-readable name
            path: Path to .pyt file
            description: Optional description
            auto_regenerate: Auto-regenerate .pyt on changes (default: True)

        Returns:
            Toolbox: The created toolbox

        Raises:
            CatalogError: If toolbox ID already exists or validation fails
        """
        catalog = self.get_or_create()

        # Check for duplicate ID
        if catalog.get_toolbox_by_id(id):
            raise CatalogError(f"Toolbox with id '{id}' already exists")

        # Create toolbox
        toolbox = Toolbox(
            id=id,
            name=name,
            path=path,
            description=description,
            created=datetime.now(),
            modified=datetime.now(),
            auto_regenerate=auto_regenerate,
        )

        catalog.toolboxes.append(toolbox)
        self.save(catalog)
        return toolbox

    def remove_toolbox(self, toolbox_id: str) -> None:
        """
        Remove a toolbox from the catalog.

        Args:
            toolbox_id: ID of toolbox to remove

        Raises:
            CatalogError: If toolbox not found
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        catalog.toolboxes.remove(toolbox)
        self.save(catalog)

    def update_toolbox(self, toolbox_id: str, **updates) -> Toolbox:
        """
        Update toolbox properties.

        Args:
            toolbox_id: ID of toolbox to update
            **updates: Fields to update (name, description, etc.)

        Returns:
            Toolbox: Updated toolbox

        Raises:
            CatalogError: If toolbox not found
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(toolbox, key):
                setattr(toolbox, key, value)

        # Update modified timestamp
        toolbox.modified = datetime.now()

        self.save(catalog)
        return toolbox

    def get_toolbox(self, toolbox_id: str) -> Toolbox | None:
        """Get toolbox by ID."""
        catalog = self.get_or_create()
        return catalog.get_toolbox_by_id(toolbox_id)

    def list_toolboxes(self) -> list[Toolbox]:
        """List all toolboxes."""
        catalog = self.get_or_create()
        return catalog.toolboxes

    # Tool Assignment Management

    def add_tool_to_toolbox(
        self,
        toolbox_id: str,
        source_id: str,
        tool_path: str,
        enabled: bool = True,
        alias: str | None = None,
    ) -> ToolReference:
        """
        Add a tool to a toolbox.

        Args:
            toolbox_id: ID of toolbox
            source_id: ID of source containing the tool
            tool_path: Relative path to tool within source
            enabled: Whether tool is enabled (default: True)
            alias: Optional tool alias

        Returns:
            ToolReference: The created tool reference

        Raises:
            CatalogError: If toolbox or source not found, or tool already exists
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        source = catalog.get_source_by_id(source_id)
        if not source:
            raise CatalogError(f"Source '{source_id}' not found")

        # Check if tool already exists in toolbox
        for existing in toolbox.tools:
            if existing.source_id == source_id and existing.tool_path == tool_path:
                raise CatalogError(
                    f"Tool '{tool_path}' from source '{source_id}' already in toolbox '{toolbox_id}'"
                )

        # Create tool reference
        tool_ref = ToolReference(
            source_id=source_id, tool_path=tool_path, enabled=enabled, alias=alias
        )

        toolbox.tools.append(tool_ref)
        toolbox.modified = datetime.now()

        self.save(catalog)
        return tool_ref

    def remove_tool_from_toolbox(self, toolbox_id: str, source_id: str, tool_path: str) -> None:
        """
        Remove a tool from a toolbox.

        Args:
            toolbox_id: ID of toolbox
            source_id: ID of source
            tool_path: Tool path within source

        Raises:
            CatalogError: If toolbox or tool not found
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        # Find and remove tool
        for tool_ref in toolbox.tools:
            if tool_ref.source_id == source_id and tool_ref.tool_path == tool_path:
                toolbox.tools.remove(tool_ref)
                toolbox.modified = datetime.now()
                self.save(catalog)
                return

        raise CatalogError(
            f"Tool '{tool_path}' from source '{source_id}' not found in toolbox '{toolbox_id}'"
        )

    def update_tool_in_toolbox(
        self, toolbox_id: str, source_id: str, tool_path: str, **updates
    ) -> ToolReference:
        """
        Update tool properties in a toolbox.

        Args:
            toolbox_id: ID of toolbox
            source_id: ID of source
            tool_path: Tool path within source
            **updates: Fields to update (enabled, alias)

        Returns:
            ToolReference: Updated tool reference

        Raises:
            CatalogError: If toolbox or tool not found
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        # Find and update tool
        for tool_ref in toolbox.tools:
            if tool_ref.source_id == source_id and tool_ref.tool_path == tool_path:
                for key, value in updates.items():
                    if hasattr(tool_ref, key):
                        setattr(tool_ref, key, value)

                toolbox.modified = datetime.now()
                self.save(catalog)
                return tool_ref

        raise CatalogError(
            f"Tool '{tool_path}' from source '{source_id}' not found in toolbox '{toolbox_id}'"
        )

    def list_tools_in_toolbox(
        self, toolbox_id: str, enabled_only: bool = False
    ) -> list[ToolReference]:
        """
        List tools in a toolbox.

        Args:
            toolbox_id: ID of toolbox
            enabled_only: If True, only return enabled tools

        Returns:
            list[ToolReference]: List of tool references

        Raises:
            CatalogError: If toolbox not found
        """
        catalog = self.get_or_create()

        toolbox = catalog.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            raise CatalogError(f"Toolbox '{toolbox_id}' not found")

        if enabled_only:
            return [tool for tool in toolbox.tools if tool.enabled]
        return toolbox.tools

    # Validation

    def validate(self) -> list[str]:
        """
        Validate catalog and return warnings.

        Returns:
            list[str]: List of warning messages (empty if no issues)
        """
        catalog = self.get_or_create()
        return catalog.validate_tool_references()

    # Utility Methods

    def _create_backup(self) -> Path:
        """Create a backup of the current catalog file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.catalog_path.with_suffix(f".{timestamp}.yml.bak")
        shutil.copy2(self.catalog_path, backup_path)
        return backup_path

    @property
    def catalog(self) -> Catalog | None:
        """Get currently loaded catalog (may be None)."""
        return self._catalog

    def exists(self) -> bool:
        """Check if catalog file exists."""
        return self.catalog_path.exists()
