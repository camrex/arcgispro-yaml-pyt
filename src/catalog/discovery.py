"""
Tool discovery service for scanning sources and finding tools.

This service discovers tools and toolboxes from various sources:
- Local directories
- Git repositories
- Network paths

It validates discovered tools and updates the catalog with findings.
"""

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.catalog.models import Source, SourceType
from src.catalog.service import CatalogService
from src.framework.config import ToolboxConfig, ToolConfig


class DiscoveryError(Exception):
    """Base exception for discovery errors."""


class GitError(DiscoveryError):
    """Error during git operations."""


class DiscoveredTool:
    """Represents a discovered tool with its metadata."""

    def __init__(
        self,
        tool_id: str,
        name: str,
        path: Path,
        config: ToolConfig,
        source_id: str,
    ):
        self.tool_id = tool_id
        self.name = name
        self.path = path
        self.config = config
        self.source_id = source_id

    def __repr__(self) -> str:
        return f"DiscoveredTool(id={self.tool_id}, name={self.name})"


class DiscoveredToolbox:
    """Represents a discovered toolbox with its metadata."""

    def __init__(
        self,
        toolbox_id: str,
        name: str,
        path: Path,
        config: ToolboxConfig,
        source_id: str,
    ):
        self.toolbox_id = toolbox_id
        self.name = name
        self.path = path
        self.config = config
        self.source_id = source_id

    def __repr__(self) -> str:
        return f"DiscoveredToolbox(id={self.toolbox_id}, name={self.name})"


class DiscoveryService:
    """Service for discovering tools from various sources."""

    def __init__(self, catalog_service: CatalogService):
        """
        Initialize discovery service.

        Args:
            catalog_service: CatalogService instance for catalog operations
        """
        self.catalog_service = catalog_service

    def scan_source(self, source_id: str) -> tuple[list[DiscoveredTool], list[DiscoveredToolbox]]:
        """
        Scan a specific source for tools and toolboxes.

        Args:
            source_id: ID of source to scan

        Returns:
            Tuple of (discovered_tools, discovered_toolboxes)

        Raises:
            DiscoveryError: If source not found or scan fails
        """
        catalog = self.catalog_service.load()
        source = catalog.get_source_by_id(source_id)

        if source is None:
            raise DiscoveryError(f"Source not found: {source_id}")

        if not source.enabled:
            raise DiscoveryError(f"Source is disabled: {source_id}")

        # Prepare source path
        source_path = self._prepare_source_path(source)

        # Discover tools and toolboxes
        tools = self._discover_tools_in_path(source_path, source_id)
        toolboxes = self._discover_toolboxes_in_path(source_path, source_id)

        # Update source metadata in catalog
        self._update_source_metadata(source_id, len(tools), len(toolboxes))

        return tools, toolboxes

    def scan_all_sources(self) -> dict[str, tuple[list[DiscoveredTool], list[DiscoveredToolbox]]]:
        """
        Scan all enabled sources for tools and toolboxes.

        Returns:
            Dictionary mapping source_id to (tools, toolboxes) tuple
        """
        catalog = self.catalog_service.load()
        results = {}

        for source in catalog.sources:
            if source.enabled:
                try:
                    results[source.id] = self.scan_source(source.id)
                except DiscoveryError as e:
                    # Log error but continue with other sources
                    print(f"Warning: Failed to scan source {source.id}: {e}")
                    results[source.id] = ([], [])

        return results

    def _prepare_source_path(self, source: Source) -> Path:
        """
        Prepare source path for scanning.

        For local/network sources, validates path exists.
        For git sources, ensures repo is cloned and up-to-date.

        Args:
            source: Source to prepare

        Returns:
            Path to scan

        Raises:
            DiscoveryError: If path preparation fails
        """
        if source.type == SourceType.LOCAL or source.type == SourceType.NETWORK:
            if source.path is None:
                raise DiscoveryError(f"Source {source.id} has no path configured")

            path = Path(source.path)
            if not path.exists():
                raise DiscoveryError(f"Source path does not exist: {path}")

            return path

        elif source.type == SourceType.GIT:
            if source.local_path is None:
                raise DiscoveryError(f"Git source {source.id} has no local_path configured")

            local_path = Path(source.local_path)

            # Clone if not exists, pull if exists
            if not local_path.exists():
                self._clone_git_repo(source)
            else:
                self._pull_git_repo(source)

            return local_path

        else:
            raise DiscoveryError(f"Unsupported source type: {source.type}")

    def _clone_git_repo(self, source: Source) -> None:
        """
        Clone a git repository.

        Args:
            source: Git source to clone

        Raises:
            GitError: If clone fails
        """
        if source.url is None or source.local_path is None:
            raise GitError(f"Git source {source.id} missing url or local_path")

        local_path = Path(source.local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cmd = ["git", "clone", source.url, str(local_path)]
            if source.branch and source.branch != "main":
                cmd.extend(["--branch", source.branch])

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to clone {source.url}: {e.stderr}") from e
        except FileNotFoundError:
            raise GitError("Git not found. Please install git.") from None

    def _pull_git_repo(self, source: Source) -> None:
        """
        Pull latest changes from git repository.

        Args:
            source: Git source to update

        Raises:
            GitError: If pull fails
        """
        if source.local_path is None:
            raise GitError(f"Git source {source.id} has no local_path")

        try:
            subprocess.run(
                ["git", "-C", str(source.local_path), "pull"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to pull {source.id}: {e.stderr}") from e

    def _discover_tools_in_path(self, path: Path, source_id: str) -> list[DiscoveredTool]:
        """
        Recursively discover all tools in a path.

        Looks for tool.yml files and validates them.

        Args:
            path: Path to scan
            source_id: ID of source being scanned

        Returns:
            List of discovered tools
        """
        tools = []

        for tool_file in path.rglob("tool.yml"):
            try:
                config = self._load_tool_config(tool_file)
                tool_id = config.tool.name
                tools.append(
                    DiscoveredTool(
                        tool_id=tool_id,
                        name=config.tool.label,
                        path=tool_file.parent,
                        config=config,
                        source_id=source_id,
                    )
                )
            except (ValidationError, ValueError, yaml.YAMLError) as e:
                # Log warning but continue
                print(f"Warning: Invalid tool config at {tool_file}: {e}")

        return tools

    def _discover_toolboxes_in_path(self, path: Path, source_id: str) -> list[DiscoveredToolbox]:
        """
        Recursively discover all toolboxes in a path.

        Looks for toolbox.yml files and validates them.

        Args:
            path: Path to scan
            source_id: ID of source being scanned

        Returns:
            List of discovered toolboxes
        """
        toolboxes = []

        for toolbox_file in path.rglob("toolbox.yml"):
            try:
                config = self._load_toolbox_config(toolbox_file)
                # Use alias as toolbox_id and label as name
                toolbox_id = config.toolbox.alias
                toolboxes.append(
                    DiscoveredToolbox(
                        toolbox_id=toolbox_id,
                        name=config.toolbox.label,
                        path=toolbox_file.parent,
                        config=config,
                        source_id=source_id,
                    )
                )
            except (ValidationError, ValueError, yaml.YAMLError) as e:
                # Log warning but continue
                print(f"Warning: Invalid toolbox config at {toolbox_file}: {e}")

        return toolboxes

    def _load_tool_config(self, tool_file: Path) -> ToolConfig:
        """
        Load and validate a tool configuration file.

        Args:
            tool_file: Path to tool.yml

        Returns:
            Validated ToolConfig

        Raises:
            ValidationError: If config is invalid
        """
        with open(tool_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return ToolConfig(**data)

    def _load_toolbox_config(self, toolbox_file: Path) -> ToolboxConfig:
        """
        Load and validate a toolbox configuration file.

        Args:
            toolbox_file: Path to toolbox.yml

        Returns:
            Validated ToolboxConfig

        Raises:
            ValidationError: If config is invalid
        """
        with open(toolbox_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return ToolboxConfig(**data)

    def _update_source_metadata(self, source_id: str, tool_count: int, toolbox_count: int) -> None:
        """
        Update source metadata with discovery results.

        Args:
            source_id: Source to update
            tool_count: Number of tools discovered
            toolbox_count: Number of toolboxes discovered
        """
        catalog = self.catalog_service.load()
        source = catalog.get_source_by_id(source_id)

        if source is None:
            return

        # Update source metadata
        source.discovered_tools = tool_count
        source.last_sync = datetime.now(UTC)

        self.catalog_service.save(catalog)

    def validate_tool_config(self, tool_file: Path) -> tuple[bool, str | None]:
        """
        Validate a tool configuration file.

        Args:
            tool_file: Path to tool.yml

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._load_tool_config(tool_file)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error loading file: {e}"

    def validate_toolbox_config(self, toolbox_file: Path) -> tuple[bool, str | None]:
        """
        Validate a toolbox configuration file.

        Args:
            toolbox_file: Path to toolbox.yml

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._load_toolbox_config(toolbox_file)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error loading file: {e}"
