"""
Pydantic models for catalog.yml schema validation.

These models define the structure of the catalog file that tracks:
- Tool sources (Git repos, local folders, network drives)
- Toolboxes (Python Toolboxes that reference tools)
- Tool assignments (which tools are in which toolboxes)
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceType(str, Enum):
    """Type of tool source."""

    GIT = "git"
    LOCAL = "local"
    NETWORK = "network"


class CatalogSettings(BaseModel):
    """Global catalog settings."""

    model_config = ConfigDict(extra="forbid")

    # Workspace configuration
    workspace_path: Path | None = Field(
        default=None,
        description="Path to workspace directory (defaults to ./workspace if not specified)",
    )
    auto_create_workspace: bool = Field(
        default=True, description="Automatically create workspace directories if missing"
    )

    # ArcGIS Pro configuration
    arcgis_pro_path: Path | None = Field(
        default=None,
        description="Path to ArcGIS Pro installation (auto-detected if not specified)",
    )
    python_env: str | None = Field(
        default=None, description="Python environment name (e.g., 'arcgispro-py3')"
    )
    auto_sync: bool = Field(default=True, description="Automatically sync Git sources on startup")


class Source(BaseModel):
    """A tool source - where tools are discovered and loaded from."""

    model_config = ConfigDict(extra="forbid")

    # Required fields
    id: str = Field(
        ...,
        description="Unique identifier (slug format: lowercase, alphanumeric, hyphens)",
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
    )
    name: str = Field(..., description="Human-readable name", min_length=1)
    type: SourceType = Field(..., description="Source type")

    # Type-specific fields
    url: str | None = Field(default=None, description="Git repository URL (required for type=git)")
    branch: str | None = Field(default="main", description="Git branch name (for type=git)")
    path: Path | None = Field(
        default=None, description="Absolute path (required for type=local or type=network)"
    )

    # Management fields
    local_path: Path | None = Field(
        default=None, description="Local storage path (auto-generated for git sources)"
    )
    enabled: bool = Field(default=True, description="Whether to scan this source for tools")
    last_sync: datetime | None = Field(
        default=None, description="Last successful sync/scan timestamp"
    )

    # Metadata (auto-populated)
    discovered_tools: int = Field(default=0, description="Number of tools found in source")
    last_error: str | None = Field(default=None, description="Last error message (if any)")

    @model_validator(mode="after")
    def validate_source_requirements(self) -> "Source":
        """Validate type-specific requirements."""
        if self.type == SourceType.GIT and not self.url:
            raise ValueError("Git sources must have a 'url' field")

        if self.type in (SourceType.LOCAL, SourceType.NETWORK) and not self.path:
            raise ValueError(f"{self.type.value} sources must have a 'path' field")

        return self


class ToolReference(BaseModel):
    """Reference to a tool within a source, assigned to a toolbox."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="ID of the source containing the tool")
    tool_path: str = Field(
        ...,
        description="Relative path to tool folder within source (e.g., 'tools/buffer_analysis')",
    )
    enabled: bool = Field(
        default=True,
        description="Whether tool is enabled in this toolbox (allows hiding without deleting)",
    )
    alias: str | None = Field(
        default=None, description="Override tool name in this toolbox (optional)"
    )


class Toolbox(BaseModel):
    """A Python Toolbox (.pyt) that references tools from sources."""

    model_config = ConfigDict(extra="forbid")

    # Required fields
    id: str = Field(
        ...,
        description="Unique identifier (slug format: lowercase, alphanumeric, hyphens)",
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
    )
    name: str = Field(..., description="Human-readable name", min_length=1)
    path: Path = Field(..., description="Absolute path to .pyt file")

    # Optional fields
    description: str | None = Field(default=None, description="Toolbox description")
    tools: list[ToolReference] = Field(
        default_factory=list, description="Tools assigned to this toolbox"
    )

    # Metadata
    created: datetime | None = Field(default=None, description="Creation timestamp")
    modified: datetime | None = Field(default=None, description="Last modification timestamp")
    auto_regenerate: bool = Field(
        default=True, description="Auto-regenerate .pyt file when catalog changes"
    )

    @field_validator("path")
    @classmethod
    def validate_pyt_extension(cls, v: Path) -> Path:
        """Ensure toolbox path has .pyt extension."""
        if v.suffix != ".pyt":
            raise ValueError(f"Toolbox path must end with .pyt, got: {v.suffix}")
        return v


class Catalog(BaseModel):
    """Root catalog model - the complete catalog.yml structure."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., description="Catalog schema version", pattern=r"^\d+\.\d+$")
    settings: CatalogSettings | None = Field(default=None, description="Global catalog settings")
    sources: list[Source] = Field(
        default_factory=list, description="Tool sources (Git repos, local folders, etc.)"
    )
    toolboxes: list[Toolbox] = Field(
        default_factory=list, description="Python Toolboxes that reference tools"
    )

    @field_validator("sources")
    @classmethod
    def validate_unique_source_ids(cls, v: list[Source]) -> list[Source]:
        """Ensure all source IDs are unique."""
        ids = [source.id for source in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate source IDs found: {set(duplicates)}")
        return v

    @field_validator("toolboxes")
    @classmethod
    def validate_unique_toolbox_ids(cls, v: list[Toolbox]) -> list[Toolbox]:
        """Ensure all toolbox IDs are unique."""
        ids = [toolbox.id for toolbox in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate toolbox IDs found: {set(duplicates)}")
        return v

    def validate_tool_references(self) -> list[str]:
        """
        Validate that all tool references point to existing sources.

        Returns:
            List of warning messages for missing source references.
        """
        warnings = []
        source_ids = {source.id for source in self.sources}

        for toolbox in self.toolboxes:
            for tool_ref in toolbox.tools:
                if tool_ref.source_id not in source_ids:
                    warnings.append(
                        f"Toolbox '{toolbox.id}' references non-existent source '{tool_ref.source_id}' "
                        f"for tool '{tool_ref.tool_path}'"
                    )

        return warnings

    def get_source_by_id(self, source_id: str) -> Source | None:
        """Get a source by its ID."""
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    def get_toolbox_by_id(self, toolbox_id: str) -> Toolbox | None:
        """Get a toolbox by its ID."""
        for toolbox in self.toolboxes:
            if toolbox.id == toolbox_id:
                return toolbox
        return None

    def get_enabled_sources(self) -> list[Source]:
        """Get all enabled sources."""
        return [source for source in self.sources if source.enabled]

    def get_tools_for_toolbox(self, toolbox_id: str) -> list[ToolReference]:
        """Get all enabled tools for a specific toolbox."""
        toolbox = self.get_toolbox_by_id(toolbox_id)
        if not toolbox:
            return []
        return [tool for tool in toolbox.tools if tool.enabled]

    def get_workspace_path(self, base_path: Path | None = None) -> Path:
        """Get the workspace path, with fallback to default."""
        if self.settings and self.settings.workspace_path:
            return self.settings.workspace_path

        # Fallback to ./workspace relative to base_path or current directory
        if base_path:
            return base_path / "workspace"
        return Path.cwd() / "workspace"

    def get_toolbox_output_path(self, base_path: Path | None = None) -> Path:
        """Get the path where generated toolbox files should be stored."""
        workspace = self.get_workspace_path(base_path)
        return workspace / "toolboxes"

    def get_sources_path(self, base_path: Path | None = None) -> Path:
        """Get the path where source repositories should be stored."""
        workspace = self.get_workspace_path(base_path)
        return workspace / "sources"
