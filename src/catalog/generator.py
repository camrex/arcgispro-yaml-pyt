"""
Toolbox generator service for creating .pyt files from catalog.

This service generates ArcGIS Pro Python Toolbox (.pyt) files from the catalog:
- Resolves tool references to actual tool configurations
- Generates Python toolbox code dynamically
- Creates metadata XML files
- Validates toolbox can be generated before creation
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

from src.catalog.models import Catalog, Source, SourceType, Toolbox, ToolReference
from src.catalog.service import CatalogService
from src.framework.config import ToolConfig, load_tool_config


class GeneratorError(Exception):
    """Base exception for generator errors."""

    pass


class ToolNotFoundError(GeneratorError):
    """Raised when a referenced tool cannot be found."""

    pass


class ToolLoadError(GeneratorError):
    """Raised when a tool configuration cannot be loaded."""

    pass


class ResolvedTool:
    """A tool that has been resolved from a reference."""

    def __init__(
        self,
        tool_reference: ToolReference,
        tool_path: Path,
        config: ToolConfig,
        alias: str | None = None,
    ):
        self.tool_reference = tool_reference
        self.tool_path = tool_path
        self.config = config
        self.alias = alias or config.tool.name

    @property
    def tool_name(self) -> str:
        """Get the tool's original name from config."""
        return self.config.tool.name

    @property
    def display_name(self) -> str:
        """Get the display name (alias if set, otherwise tool name)."""
        return self.alias


class GeneratorService:
    """Service for generating .pyt files from catalog."""

    def __init__(self, catalog_service: CatalogService):
        """
        Initialize the generator service.

        Args:
            catalog_service: CatalogService instance for loading catalog
        """
        self.catalog_service = catalog_service

    def validate_toolbox(self, toolbox_id: str) -> tuple[bool, list[str]]:
        """
        Validate that a toolbox can be generated.

        Checks that all tool references can be resolved and loaded.

        Args:
            toolbox_id: ID of the toolbox to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        catalog = self.catalog_service.load()
        toolbox = catalog.get_toolbox_by_id(toolbox_id)

        if not toolbox:
            return False, [f"Toolbox '{toolbox_id}' not found in catalog"]

        # Check each tool reference
        for tool_ref in toolbox.tools:
            try:
                self._resolve_tool(catalog, tool_ref)
            except (ToolNotFoundError, ToolLoadError) as e:
                errors.append(str(e))

        return len(errors) == 0, errors

    def generate_toolbox(
        self,
        toolbox_id: str,
        output_path: Path,
        generate_metadata: bool = True,
    ) -> Path:
        """
        Generate a .pyt file for a specific toolbox.

        Args:
            toolbox_id: ID of the toolbox to generate
            output_path: Path where the .pyt file should be created
            generate_metadata: Whether to generate .pyt.xml metadata file

        Returns:
            Path to the generated .pyt file

        Raises:
            GeneratorError: If toolbox cannot be generated
        """
        catalog = self.catalog_service.load()
        toolbox = catalog.get_toolbox_by_id(toolbox_id)

        if not toolbox:
            raise GeneratorError(f"Toolbox '{toolbox_id}' not found in catalog")

        # Validate before generating
        is_valid, errors = self.validate_toolbox(toolbox_id)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise GeneratorError(f"Cannot generate toolbox '{toolbox_id}':\n{error_msg}")

        # Resolve all tools
        resolved_tools = []
        for tool_ref in toolbox.tools:
            resolved = self._resolve_tool(catalog, tool_ref)
            resolved_tools.append(resolved)

        # Generate .pyt file
        pyt_content = self._generate_pyt_content(toolbox, resolved_tools)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pyt_content, encoding="utf-8")

        # Generate metadata if requested
        if generate_metadata:
            metadata_path = output_path.with_suffix(".pyt.xml")
            metadata_content = self._generate_metadata_xml(toolbox, resolved_tools)
            metadata_path.write_text(metadata_content, encoding="utf-8")

        return output_path

    def generate_all_toolboxes(
        self,
        output_dir: Path,
        generate_metadata: bool = True,
    ) -> list[Path]:
        """
        Generate .pyt files for all toolboxes in the catalog.

        Args:
            output_dir: Directory where .pyt files should be created
            generate_metadata: Whether to generate .pyt.xml metadata files

        Returns:
            List of paths to generated .pyt files

        Raises:
            GeneratorError: If any toolbox cannot be generated
        """
        catalog = self.catalog_service.load()
        generated_files = []

        for toolbox in catalog.toolboxes:
            output_path = output_dir / f"{toolbox.id}.pyt"
            try:
                generated = self.generate_toolbox(toolbox.id, output_path, generate_metadata)
                generated_files.append(generated)
            except GeneratorError as e:
                # Re-raise with context
                raise GeneratorError(f"Failed to generate toolbox '{toolbox.id}': {e}") from e

        return generated_files

    def _resolve_tool(self, catalog: Catalog, tool_ref: ToolReference) -> ResolvedTool:
        """
        Resolve a tool reference to its actual configuration.

        Args:
            catalog: The catalog containing sources
            tool_ref: The tool reference to resolve

        Returns:
            ResolvedTool with loaded configuration

        Raises:
            ToolNotFoundError: If tool or source not found
            ToolLoadError: If tool config cannot be loaded
        """
        # Get the source
        source = catalog.get_source_by_id(tool_ref.source_id)
        if not source:
            raise ToolNotFoundError(
                f"Source '{tool_ref.source_id}' not found for tool '{tool_ref.tool_path}'"
            )

        # Build path to tool
        tool_path = self._get_tool_path(source, tool_ref.tool_path)
        if not tool_path.exists():
            raise ToolNotFoundError(
                f"Tool path does not exist: {tool_path} (source: {tool_ref.source_id})"
            )

        # Load tool config
        tool_config_file = tool_path / "tool.yml"
        if not tool_config_file.exists():
            raise ToolNotFoundError(
                f"tool.yml not found at {tool_path} (source: {tool_ref.source_id})"
            )

        try:
            config = load_tool_config(tool_config_file)
        except Exception as e:
            raise ToolLoadError(f"Failed to load tool config from {tool_config_file}: {e}") from e

        return ResolvedTool(
            tool_reference=tool_ref,
            tool_path=tool_path,
            config=config,
            alias=tool_ref.alias,
        )

    def _get_tool_path(self, source: Source, tool_path: str) -> Path:
        """
        Get the absolute path to a tool within a source.

        Args:
            source: The source containing the tool
            tool_path: Relative path to tool within source

        Returns:
            Absolute path to the tool directory

        Raises:
            GeneratorError: If source path is not configured
        """
        if source.type == SourceType.LOCAL or source.type == SourceType.NETWORK:
            if not source.path:
                raise GeneratorError(f"Source '{source.id}' has no path configured")
            base_path = Path(source.path)
        elif source.type == SourceType.GIT:
            if not source.local_path:
                raise GeneratorError(
                    f"Git source '{source.id}' has no local_path configured. "
                    "Run discovery service to clone the repository first."
                )
            base_path = Path(source.local_path)
        else:
            raise GeneratorError(f"Unknown source type: {source.type}")

        return base_path / tool_path

    def _generate_pyt_content(self, toolbox: Toolbox, resolved_tools: list[ResolvedTool]) -> str:
        """
        Generate the Python code for a .pyt file.

        Args:
            toolbox: The toolbox to generate
            resolved_tools: List of resolved tools

        Returns:
            Python code as a string
        """
        # Build tool import paths
        tool_imports = []
        tool_references = []

        for resolved in resolved_tools:
            # Convert tool path to Python module path
            # e.g., tools/buffer_analysis -> tools.buffer_analysis
            module_path = str(resolved.tool_path.relative_to(resolved.tool_path.parent.parent))
            module_path = module_path.replace("\\", ".").replace("/", ".")

            tool_imports.append(f"# {resolved.display_name}")
            tool_references.append(resolved.display_name)

        imports = "\n".join(tool_imports) if tool_imports else "# No tools"
        tools_list = ",\n            ".join(f'"{name}"' for name in tool_references)

        timestamp = datetime.now(UTC).isoformat()

        content = f'''"""
{toolbox.name}

{toolbox.description or ""}

Generated by ArcGIS Pro YAML-PYT Framework
Generated: {timestamp}
Toolbox ID: {toolbox.id}
"""

from pathlib import Path
from src.framework.factory import create_tool_from_config

{imports}


class Toolbox:
    """Toolbox definition for {toolbox.name}."""

    def __init__(self):
        self.label = "{toolbox.name}"
        self.alias = "{toolbox.id}"
        self.description = "{toolbox.description or ""}"
        
        # Tools will be loaded dynamically from catalog
        self.tools = [
            {tools_list}
        ]

    def get_tool(self, tool_name: str):
        """Get a tool instance by name."""
        # This would use the factory to create tool instances
        # For now, return the tool name
        return tool_name
'''

        return content

    def _generate_metadata_xml(self, toolbox: Toolbox, resolved_tools: list[ResolvedTool]) -> str:
        """
        Generate metadata XML for a .pyt file.

        Args:
            toolbox: The toolbox
            resolved_tools: List of resolved tools

        Returns:
            XML metadata as a string
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d")

        xml = dedent(f'''<?xml version="1.0" encoding="UTF-8"?>
            <metadata xml:lang="en">
                <Esri>
                    <CreaDate>{timestamp}</CreaDate>
                    <CreaTime>12000000</CreaTime>
                    <ArcGISFormat>1.0</ArcGISFormat>
                    <SyncOnce>TRUE</SyncOnce>
                </Esri>
                <toolbox name="{toolbox.name}" alias="{toolbox.id}">
                    <arcToolboxHelpPath>c:\\program files\\arcgis\\pro\\Resources\\Help\\gp</arcToolboxHelpPath>
                    <toolsets/>
                </toolbox>
                <dataIdInfo>
                    <idCitation>
                        <resTitle>{toolbox.name}</resTitle>
                    </idCitation>
                    <idAbs>{toolbox.description or ""}</idAbs>
                    <idCredit>Generated by ArcGIS Pro YAML-PYT Framework</idCredit>
                </dataIdInfo>
            </metadata>
        ''').strip()

        return xml
