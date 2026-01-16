"""
Tests for the toolbox generator service.
"""

import pytest
import yaml

from src.catalog.generator import (
    GeneratorError,
    GeneratorService,
)
from src.catalog.models import SourceType
from src.catalog.service import CatalogService


class TestGeneratorService:
    """Test basic generator service operations."""

    def test_init(self, catalog_service):
        """Test generator service initialization."""
        generator = GeneratorService(catalog_service)
        assert generator.catalog_service is catalog_service

    def test_validate_toolbox_not_found(self, generator_service):
        """Test validation of non-existent toolbox."""
        is_valid, errors = generator_service.validate_toolbox("nonexistent")
        assert not is_valid
        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_generate_toolbox_not_found(self, generator_service, tmp_path):
        """Test generating non-existent toolbox."""
        output = tmp_path / "test.pyt"
        with pytest.raises(GeneratorError, match="not found"):
            generator_service.generate_toolbox("nonexistent", output)


class TestToolResolution:
    """Test tool reference resolution."""

    def test_resolve_local_tool(self, generator_service, catalog_service, temp_source_dir):
        """Test resolving a tool from a local source."""
        # Add source and toolbox
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test tools")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/tool1")

        # Validate should succeed
        is_valid, errors = generator_service.validate_toolbox("test-toolbox")
        assert is_valid
        assert len(errors) == 0

    def test_resolve_tool_source_not_found(
        self, generator_service, catalog_service, temp_source_dir
    ):
        """Test resolution when source doesn't exist."""
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test tools")

        # Manually add a tool reference with non-existent source
        # (bypass validation by directly modifying catalog)
        from src.catalog.models import ToolReference

        catalog = catalog_service.load()
        toolbox = catalog.get_toolbox_by_id("test-toolbox")
        toolbox.tools.append(ToolReference(source_id="nonexistent-source", tool_path="tools/tool1"))
        catalog_service.save(catalog)

        is_valid, errors = generator_service.validate_toolbox("test-toolbox")
        assert not is_valid
        assert any("Source" in err and "not found" in err for err in errors)

    def test_resolve_tool_path_not_found(self, generator_service, catalog_service, temp_source_dir):
        """Test resolution when tool path doesn't exist."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test tools")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/nonexistent")

        is_valid, errors = generator_service.validate_toolbox("test-toolbox")
        assert not is_valid
        assert any("does not exist" in err for err in errors)

    def test_resolve_tool_config_not_found(
        self, generator_service, catalog_service, temp_source_dir
    ):
        """Test resolution when tool.yml doesn't exist."""
        # Create tool dir without tool.yml
        tool_dir = temp_source_dir / "tools" / "incomplete"
        tool_dir.mkdir(parents=True)

        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test tools")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/incomplete")

        is_valid, errors = generator_service.validate_toolbox("test-toolbox")
        assert not is_valid
        assert any("tool.yml not found" in err for err in errors)

    def test_resolve_tool_invalid_config(self, generator_service, catalog_service, temp_source_dir):
        """Test resolution when tool.yml is invalid."""
        # Create tool with invalid config
        tool_dir = temp_source_dir / "tools" / "bad_tool"
        tool_dir.mkdir(parents=True)
        (tool_dir / "tool.yml").write_text("invalid: yaml: content: [[[")

        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test tools")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/bad_tool")

        is_valid, errors = generator_service.validate_toolbox("test-toolbox")
        assert not is_valid
        assert any("Failed to load" in err for err in errors)


class TestToolboxGeneration:
    """Test .pyt file generation."""

    def test_generate_simple_toolbox(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test generating a simple toolbox with one tool."""
        # Setup
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "A test toolbox")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/tool1")

        # Generate
        output = tmp_path / "test.pyt"
        result = generator_service.generate_toolbox("test-toolbox", output, generate_metadata=False)

        # Verify
        assert result == output
        assert output.exists()
        content = output.read_text()
        assert "class Toolbox:" in content
        assert "Test Toolbox" in content
        assert "self.label" in content
        assert "self.tools" in content

    def test_generate_toolbox_with_metadata(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test generating toolbox with metadata XML."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "A test toolbox")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/tool1")

        output = tmp_path / "test.pyt"
        generator_service.generate_toolbox("test-toolbox", output, generate_metadata=True)

        # Check metadata file
        metadata = output.with_suffix(".pyt.xml")
        assert metadata.exists()
        content = metadata.read_text()
        assert "<?xml version" in content
        assert "Test Toolbox" in content
        assert "<toolbox" in content

    def test_generate_toolbox_with_multiple_tools(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test generating toolbox with multiple tools."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox(
            "multi-toolbox", "Multi Tool Toolbox", "multi.pyt", "Multiple tools"
        )
        catalog_service.add_tool_to_toolbox("multi-toolbox", "test-source", "tools/tool1")
        catalog_service.add_tool_to_toolbox("multi-toolbox", "test-source", "tools/tool2")

        output = tmp_path / "multi.pyt"
        generator_service.generate_toolbox("multi-toolbox", output)

        assert output.exists()
        content = output.read_text()
        assert "tool1" in content
        assert "tool2" in content

    def test_generate_toolbox_with_alias(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test generating toolbox with aliased tool."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("alias-toolbox", "Alias Toolbox", "alias.pyt", "Aliased tools")
        catalog_service.add_tool_to_toolbox(
            "alias-toolbox", "test-source", "tools/tool1", alias="CustomTool"
        )

        output = tmp_path / "alias.pyt"
        generator_service.generate_toolbox("alias-toolbox", output)

        content = output.read_text()
        assert "CustomTool" in content

    def test_generate_creates_parent_dirs(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test that generate creates parent directories."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("test-toolbox", "Test Toolbox", "test.pyt", "Test")
        catalog_service.add_tool_to_toolbox("test-toolbox", "test-source", "tools/tool1")

        output = tmp_path / "nested" / "dir" / "test.pyt"
        generator_service.generate_toolbox("test-toolbox", output)

        assert output.exists()
        assert output.parent.exists()


class TestBatchGeneration:
    """Test generating multiple toolboxes."""

    def test_generate_all_toolboxes(
        self, generator_service, catalog_service, temp_source_dir, tmp_path
    ):
        """Test generating all toolboxes in catalog."""
        catalog_service.add_source(
            "test-source", "Test Source", SourceType.LOCAL, path=temp_source_dir
        )
        catalog_service.add_toolbox("toolbox1", "Toolbox 1", "tb1.pyt", "First")
        catalog_service.add_tool_to_toolbox("toolbox1", "test-source", "tools/tool1")
        catalog_service.add_toolbox("toolbox2", "Toolbox 2", "tb2.pyt", "Second")
        catalog_service.add_tool_to_toolbox("toolbox2", "test-source", "tools/tool2")

        results = generator_service.generate_all_toolboxes(tmp_path, generate_metadata=False)

        assert len(results) == 2
        assert (tmp_path / "toolbox1.pyt").exists()
        assert (tmp_path / "toolbox2.pyt").exists()

    def test_generate_all_empty_catalog(self, generator_service, tmp_path):
        """Test generating all when catalog has no toolboxes."""
        results = generator_service.generate_all_toolboxes(tmp_path)
        assert len(results) == 0

    def test_generate_all_fails_on_invalid_toolbox(
        self, generator_service, catalog_service, tmp_path
    ):
        """Test that generate_all fails if any toolbox is invalid."""
        catalog_service.add_toolbox("bad-toolbox", "Bad Toolbox", "bad.pyt", "Invalid")

        # Manually add tool reference with non-existent source
        from src.catalog.models import ToolReference

        catalog = catalog_service.load()
        toolbox = catalog.get_toolbox_by_id("bad-toolbox")
        toolbox.tools.append(ToolReference(source_id="nonexistent", tool_path="tools/tool1"))
        catalog_service.save(catalog)

        with pytest.raises(GeneratorError, match="Failed to generate"):
            generator_service.generate_all_toolboxes(tmp_path)


# Fixtures


@pytest.fixture
def catalog_service(tmp_path):
    """Create a catalog service with temporary catalog."""
    catalog_path = tmp_path / "catalog.yml"
    service = CatalogService(catalog_path)
    service.create_new()
    return service


@pytest.fixture
def generator_service(catalog_service):
    """Create a generator service."""
    return GeneratorService(catalog_service)


@pytest.fixture
def temp_source_dir(tmp_path):
    """Create a temporary source directory with test tools."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create tool1
    tool1_dir = source_dir / "tools" / "tool1"
    tool1_dir.mkdir(parents=True)
    tool1_config = {
        "tool": {
            "name": "tool1",
            "label": "Tool 1",
            "description": "First test tool",
            "category": "Test",
        },
        "implementation": {"executeFunction": "execute.run"},
        "parameters": [],
    }
    with open(tool1_dir / "tool.yml", "w") as f:
        yaml.safe_dump(tool1_config, f)

    # Create tool2
    tool2_dir = source_dir / "tools" / "tool2"
    tool2_dir.mkdir(parents=True)
    tool2_config = {
        "tool": {
            "name": "tool2",
            "label": "Tool 2",
            "description": "Second test tool",
            "category": "Test",
        },
        "implementation": {"executeFunction": "execute.run"},
        "parameters": [],
    }
    with open(tool2_dir / "tool.yml", "w") as f:
        yaml.safe_dump(tool2_config, f)

    return source_dir
