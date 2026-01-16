"""
Tests for catalog schema Pydantic models.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.catalog.models import (
    Catalog,
    CatalogSettings,
    Source,
    SourceType,
    Toolbox,
    ToolReference,
)


class TestCatalogSettings:
    """Tests for CatalogSettings model."""

    def test_defaults(self):
        """Test default settings values."""
        settings = CatalogSettings()
        assert settings.arcgis_pro_path is None
        assert settings.python_env is None
        assert settings.auto_sync is True

    def test_custom_values(self):
        """Test custom settings values."""
        settings = CatalogSettings(
            arcgis_pro_path=Path("C:/Program Files/ArcGIS/Pro"),
            python_env="arcgispro-py3",
            auto_sync=False,
        )
        assert settings.arcgis_pro_path == Path("C:/Program Files/ArcGIS/Pro")
        assert settings.python_env == "arcgispro-py3"
        assert settings.auto_sync is False


class TestSource:
    """Tests for Source model."""

    def test_git_source_valid(self):
        """Test valid Git source."""
        source = Source(
            id="my-tools",
            name="My Tools",
            type=SourceType.GIT,
            url="https://github.com/user/repo",
        )
        assert source.id == "my-tools"
        assert source.type == SourceType.GIT
        assert source.branch == "main"  # default
        assert source.enabled is True  # default

    def test_git_source_missing_url(self):
        """Test Git source without URL raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Source(
                id="my-tools",
                name="My Tools",
                type=SourceType.GIT,
            )
        assert "Git sources must have a 'url' field" in str(exc_info.value)

    def test_local_source_valid(self):
        """Test valid local source."""
        source = Source(
            id="local-tools",
            name="Local Tools",
            type=SourceType.LOCAL,
            path=Path("C:/GIS/Tools"),
        )
        assert source.type == SourceType.LOCAL
        assert source.path == Path("C:/GIS/Tools")

    def test_local_source_missing_path(self):
        """Test local source without path raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Source(
                id="local-tools",
                name="Local Tools",
                type=SourceType.LOCAL,
            )
        assert "local sources must have a 'path' field" in str(exc_info.value)

    def test_network_source_valid(self):
        """Test valid network source."""
        source = Source(
            id="network-tools",
            name="Network Tools",
            type=SourceType.NETWORK,
            path=Path("//server/share/tools"),
        )
        assert source.type == SourceType.NETWORK
        assert source.path == Path("//server/share/tools")

    def test_invalid_id_format(self):
        """Test source ID validation."""
        with pytest.raises(ValidationError):
            Source(
                id="My Tools",  # Spaces not allowed
                name="My Tools",
                type=SourceType.LOCAL,
                path=Path("C:/Tools"),
            )

        with pytest.raises(ValidationError):
            Source(
                id="MY-TOOLS",  # Uppercase not allowed
                name="My Tools",
                type=SourceType.LOCAL,
                path=Path("C:/Tools"),
            )

    def test_valid_id_formats(self):
        """Test valid source ID formats."""
        valid_ids = ["tools", "my-tools", "team-hydrology-v2", "tools123"]
        for valid_id in valid_ids:
            source = Source(
                id=valid_id,
                name="Test",
                type=SourceType.LOCAL,
                path=Path("C:/Tools"),
            )
            assert source.id == valid_id

    def test_metadata_fields(self):
        """Test metadata fields."""
        source = Source(
            id="tools",
            name="Tools",
            type=SourceType.LOCAL,
            path=Path("C:/Tools"),
            last_sync=datetime(2026, 1, 16, 10, 30),
            discovered_tools=5,
            last_error="Some error",
        )
        assert source.last_sync == datetime(2026, 1, 16, 10, 30)
        assert source.discovered_tools == 5
        assert source.last_error == "Some error"


class TestToolReference:
    """Tests for ToolReference model."""

    def test_basic_reference(self):
        """Test basic tool reference."""
        ref = ToolReference(
            source_id="my-tools",
            tool_path="tools/buffer_analysis",
        )
        assert ref.source_id == "my-tools"
        assert ref.tool_path == "tools/buffer_analysis"
        assert ref.enabled is True  # default
        assert ref.alias is None  # default

    def test_disabled_reference(self):
        """Test disabled tool reference."""
        ref = ToolReference(
            source_id="my-tools",
            tool_path="tools/old_tool",
            enabled=False,
        )
        assert ref.enabled is False

    def test_aliased_reference(self):
        """Test tool reference with alias."""
        ref = ToolReference(
            source_id="my-tools",
            tool_path="tools/analysis",
            alias="Custom Analysis Tool",
        )
        assert ref.alias == "Custom Analysis Tool"


class TestToolbox:
    """Tests for Toolbox model."""

    def test_basic_toolbox(self):
        """Test basic toolbox."""
        toolbox = Toolbox(
            id="my-toolbox",
            name="My Toolbox",
            path=Path("C:/Projects/toolbox.pyt"),
        )
        assert toolbox.id == "my-toolbox"
        assert toolbox.name == "My Toolbox"
        assert toolbox.path == Path("C:/Projects/toolbox.pyt")
        assert toolbox.tools == []
        assert toolbox.auto_regenerate is True

    def test_toolbox_with_tools(self):
        """Test toolbox with tool references."""
        toolbox = Toolbox(
            id="analysis",
            name="Analysis Toolbox",
            path=Path("C:/analysis.pyt"),
            tools=[
                ToolReference(source_id="src1", tool_path="tools/buffer"),
                ToolReference(source_id="src2", tool_path="tools/clip"),
            ],
        )
        assert len(toolbox.tools) == 2
        assert toolbox.tools[0].source_id == "src1"

    def test_invalid_pyt_extension(self):
        """Test toolbox path must end with .pyt."""
        with pytest.raises(ValidationError) as exc_info:
            Toolbox(
                id="test",
                name="Test",
                path=Path("C:/toolbox.py"),  # Wrong extension
            )
        assert "must end with .pyt" in str(exc_info.value)

    def test_valid_pyt_path(self):
        """Test valid .pyt path."""
        toolbox = Toolbox(
            id="test",
            name="Test",
            path=Path("C:/Projects/my_toolbox.pyt"),
        )
        assert toolbox.path.suffix == ".pyt"

    def test_toolbox_metadata(self):
        """Test toolbox metadata fields."""
        created = datetime(2026, 1, 10, 12, 0)
        modified = datetime(2026, 1, 16, 10, 30)

        toolbox = Toolbox(
            id="test",
            name="Test",
            path=Path("C:/test.pyt"),
            description="Test toolbox",
            created=created,
            modified=modified,
            auto_regenerate=False,
        )
        assert toolbox.description == "Test toolbox"
        assert toolbox.created == created
        assert toolbox.modified == modified
        assert toolbox.auto_regenerate is False


class TestCatalog:
    """Tests for Catalog model."""

    def test_minimal_catalog(self):
        """Test minimal valid catalog."""
        catalog = Catalog(version="1.0")
        assert catalog.version == "1.0"
        assert catalog.sources == []
        assert catalog.toolboxes == []
        assert catalog.settings is None

    def test_catalog_with_settings(self):
        """Test catalog with settings."""
        catalog = Catalog(
            version="1.0",
            settings=CatalogSettings(auto_sync=False),
        )
        assert catalog.settings is not None
        assert catalog.settings.auto_sync is False

    def test_catalog_with_sources(self):
        """Test catalog with sources."""
        catalog = Catalog(
            version="1.0",
            sources=[
                Source(
                    id="src1",
                    name="Source 1",
                    type=SourceType.LOCAL,
                    path=Path("C:/Tools"),
                ),
                Source(
                    id="src2",
                    name="Source 2",
                    type=SourceType.GIT,
                    url="https://github.com/user/repo",
                ),
            ],
        )
        assert len(catalog.sources) == 2

    def test_duplicate_source_ids(self):
        """Test duplicate source IDs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Catalog(
                version="1.0",
                sources=[
                    Source(
                        id="duplicate",
                        name="Source 1",
                        type=SourceType.LOCAL,
                        path=Path("C:/Tools1"),
                    ),
                    Source(
                        id="duplicate",
                        name="Source 2",
                        type=SourceType.LOCAL,
                        path=Path("C:/Tools2"),
                    ),
                ],
            )
        assert "Duplicate source IDs" in str(exc_info.value)

    def test_duplicate_toolbox_ids(self):
        """Test duplicate toolbox IDs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Catalog(
                version="1.0",
                toolboxes=[
                    Toolbox(id="duplicate", name="TB1", path=Path("C:/tb1.pyt")),
                    Toolbox(id="duplicate", name="TB2", path=Path("C:/tb2.pyt")),
                ],
            )
        assert "Duplicate toolbox IDs" in str(exc_info.value)

    def test_get_source_by_id(self):
        """Test getting source by ID."""
        catalog = Catalog(
            version="1.0",
            sources=[
                Source(
                    id="src1",
                    name="Source 1",
                    type=SourceType.LOCAL,
                    path=Path("C:/Tools"),
                ),
            ],
        )
        source = catalog.get_source_by_id("src1")
        assert source is not None
        assert source.id == "src1"

        assert catalog.get_source_by_id("nonexistent") is None

    def test_get_toolbox_by_id(self):
        """Test getting toolbox by ID."""
        catalog = Catalog(
            version="1.0",
            toolboxes=[
                Toolbox(id="tb1", name="Toolbox 1", path=Path("C:/tb1.pyt")),
            ],
        )
        toolbox = catalog.get_toolbox_by_id("tb1")
        assert toolbox is not None
        assert toolbox.id == "tb1"

        assert catalog.get_toolbox_by_id("nonexistent") is None

    def test_get_enabled_sources(self):
        """Test getting only enabled sources."""
        catalog = Catalog(
            version="1.0",
            sources=[
                Source(
                    id="enabled",
                    name="Enabled",
                    type=SourceType.LOCAL,
                    path=Path("C:/Tools1"),
                    enabled=True,
                ),
                Source(
                    id="disabled",
                    name="Disabled",
                    type=SourceType.LOCAL,
                    path=Path("C:/Tools2"),
                    enabled=False,
                ),
            ],
        )
        enabled = catalog.get_enabled_sources()
        assert len(enabled) == 1
        assert enabled[0].id == "enabled"

    def test_validate_tool_references(self):
        """Test validation of tool references."""
        catalog = Catalog(
            version="1.0",
            sources=[
                Source(
                    id="valid-source",
                    name="Valid",
                    type=SourceType.LOCAL,
                    path=Path("C:/Tools"),
                ),
            ],
            toolboxes=[
                Toolbox(
                    id="tb1",
                    name="Toolbox 1",
                    path=Path("C:/tb1.pyt"),
                    tools=[
                        ToolReference(source_id="valid-source", tool_path="tools/buffer"),
                        ToolReference(source_id="missing-source", tool_path="tools/clip"),
                    ],
                ),
            ],
        )

        warnings = catalog.validate_tool_references()
        assert len(warnings) == 1
        assert "missing-source" in warnings[0]
        assert "tb1" in warnings[0]

    def test_get_tools_for_toolbox(self):
        """Test getting enabled tools for a toolbox."""
        catalog = Catalog(
            version="1.0",
            toolboxes=[
                Toolbox(
                    id="tb1",
                    name="Toolbox 1",
                    path=Path("C:/tb1.pyt"),
                    tools=[
                        ToolReference(source_id="src1", tool_path="tools/enabled"),
                        ToolReference(
                            source_id="src1",
                            tool_path="tools/disabled",
                            enabled=False,
                        ),
                    ],
                ),
            ],
        )

        tools = catalog.get_tools_for_toolbox("tb1")
        assert len(tools) == 1
        assert tools[0].tool_path == "tools/enabled"

    def test_invalid_version_format(self):
        """Test version must be in X.Y format."""
        with pytest.raises(ValidationError):
            Catalog(version="1")  # Missing minor version

        with pytest.raises(ValidationError):
            Catalog(version="v1.0")  # Extra character

        # Valid versions
        Catalog(version="1.0")
        Catalog(version="2.5")
        Catalog(version="10.99")
