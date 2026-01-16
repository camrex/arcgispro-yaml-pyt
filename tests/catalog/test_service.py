"""
Tests for CatalogService.
"""

from pathlib import Path

import pytest

from src.catalog.models import SourceType
from src.catalog.service import (
    CatalogError,
    CatalogNotFoundError,
    CatalogService,
)


@pytest.fixture
def temp_catalog_path(tmp_path):
    """Fixture providing a temporary catalog path."""
    return tmp_path / "catalog.yml"


@pytest.fixture
def service(temp_catalog_path):
    """Fixture providing a CatalogService instance."""
    return CatalogService(temp_catalog_path)


class TestCatalogServiceBasics:
    """Tests for basic catalog operations."""

    def test_init_default_path(self):
        """Test service initialization with default path."""
        service = CatalogService()
        expected = Path.home() / ".arcgis_yaml_toolbox" / "catalog.yml"
        assert service.catalog_path == expected

    def test_init_custom_path(self, temp_catalog_path):
        """Test service initialization with custom path."""
        service = CatalogService(temp_catalog_path)
        assert service.catalog_path == temp_catalog_path

    def test_exists_false_initially(self, service):
        """Test exists() returns False before catalog created."""
        assert not service.exists()

    def test_load_nonexistent_catalog(self, service):
        """Test loading nonexistent catalog raises error."""
        with pytest.raises(CatalogNotFoundError):
            service.load()

    def test_create_new_catalog(self, service):
        """Test creating a new catalog."""
        catalog = service.create_new()
        assert catalog.version == "1.0"
        assert catalog.sources == []
        assert catalog.toolboxes == []
        assert service.exists()

    def test_create_new_when_exists(self, service):
        """Test creating catalog when one exists raises error."""
        service.create_new()
        with pytest.raises(CatalogError):
            service.create_new()

    def test_create_new_with_overwrite(self, service):
        """Test creating catalog with overwrite."""
        service.create_new()
        catalog = service.create_new(overwrite=True)
        assert catalog.version == "1.0"

    def test_get_or_create_nonexistent(self, service):
        """Test get_or_create creates new catalog if none exists."""
        catalog = service.get_or_create()
        assert catalog.version == "1.0"
        assert service.exists()

    def test_get_or_create_existing(self, service):
        """Test get_or_create loads existing catalog."""
        # Create catalog
        service.create_new()
        service.add_source("test", "Test Source", SourceType.LOCAL, path=Path("/test"))

        # Get or create should load existing
        catalog = service.get_or_create()
        assert len(catalog.sources) == 1
        assert catalog.sources[0].id == "test"

    def test_save_and_load(self, service):
        """Test saving and loading catalog."""
        # Create and save
        service.create_new()
        service.add_source("test", "Test", SourceType.LOCAL, path=Path("/test"))

        # Load in new service instance
        service2 = CatalogService(service.catalog_path)
        loaded = service2.load()

        assert len(loaded.sources) == 1
        assert loaded.sources[0].id == "test"

    def test_backup_created(self, service):
        """Test backup is created when saving over existing file."""
        service.create_new()
        service.save()  # Second save should create backup

        backup_files = list(service.catalog_path.parent.glob("*.bak"))
        assert len(backup_files) == 1


class TestSourceManagement:
    """Tests for source management operations."""

    def test_add_git_source(self, service):
        """Test adding a Git source."""
        source = service.add_source(
            id="test-repo",
            name="Test Repo",
            type=SourceType.GIT,
            url="https://github.com/user/repo",
        )

        assert source.id == "test-repo"
        assert source.type == SourceType.GIT
        assert source.url == "https://github.com/user/repo"
        assert source.enabled is True

        # Verify saved
        catalog = service.load()
        assert len(catalog.sources) == 1

    def test_add_local_source(self, service):
        """Test adding a local source."""
        source = service.add_source(
            id="local-tools",
            name="Local Tools",
            type=SourceType.LOCAL,
            path=Path("/local/tools"),
        )

        assert source.id == "local-tools"
        assert source.type == SourceType.LOCAL
        assert source.path == Path("/local/tools")

    def test_add_duplicate_source(self, service):
        """Test adding source with duplicate ID fails."""
        service.add_source("test", "Test", SourceType.LOCAL, path=Path("/test"))

        with pytest.raises(CatalogError) as exc_info:
            service.add_source("test", "Test2", SourceType.LOCAL, path=Path("/test2"))

        assert "already exists" in str(exc_info.value)

    def test_get_source(self, service):
        """Test getting source by ID."""
        service.add_source("test", "Test", SourceType.LOCAL, path=Path("/test"))

        source = service.get_source("test")
        assert source is not None
        assert source.id == "test"

        assert service.get_source("nonexistent") is None

    def test_list_sources(self, service):
        """Test listing all sources."""
        service.add_source("src1", "Source 1", SourceType.LOCAL, path=Path("/src1"))
        service.add_source("src2", "Source 2", SourceType.LOCAL, path=Path("/src2"), enabled=False)

        all_sources = service.list_sources()
        assert len(all_sources) == 2

        enabled_only = service.list_sources(enabled_only=True)
        assert len(enabled_only) == 1
        assert enabled_only[0].id == "src1"

    def test_update_source(self, service):
        """Test updating source properties."""
        service.add_source("test", "Test", SourceType.LOCAL, path=Path("/test"))

        updated = service.update_source("test", name="Updated Name", enabled=False)
        assert updated.name == "Updated Name"
        assert updated.enabled is False

        # Verify saved
        catalog = service.load()
        source = catalog.get_source_by_id("test")
        assert source is not None
        assert source.name == "Updated Name"

    def test_update_nonexistent_source(self, service):
        """Test updating nonexistent source fails."""
        with pytest.raises(CatalogError):
            service.update_source("nonexistent", name="Test")

    def test_remove_source(self, service):
        """Test removing a source."""
        service.add_source("test", "Test", SourceType.LOCAL, path=Path("/test"))
        service.remove_source("test")

        catalog = service.load()
        assert len(catalog.sources) == 0

    def test_remove_nonexistent_source(self, service):
        """Test removing nonexistent source fails."""
        with pytest.raises(CatalogError):
            service.remove_source("nonexistent")

    def test_remove_source_referenced_by_toolbox(self, service):
        """Test removing source referenced by toolbox fails without force."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/toolbox.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/test")

        with pytest.raises(CatalogError) as exc_info:
            service.remove_source("src")

        assert "referenced by toolbox" in str(exc_info.value)

    def test_remove_source_with_force(self, service):
        """Test removing source with force=True even if referenced."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/toolbox.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/test")

        service.remove_source("src", force=True)

        catalog = service.load()
        assert len(catalog.sources) == 0
        # Toolbox still exists with broken reference
        assert len(catalog.toolboxes) == 1


class TestToolboxManagement:
    """Tests for toolbox management operations."""

    def test_add_toolbox(self, service):
        """Test adding a toolbox."""
        toolbox = service.add_toolbox(
            id="test-toolbox",
            name="Test Toolbox",
            path=Path("/projects/test.pyt"),
            description="Test description",
        )

        assert toolbox.id == "test-toolbox"
        assert toolbox.name == "Test Toolbox"
        assert toolbox.path == Path("/projects/test.pyt")
        assert toolbox.description == "Test description"
        assert toolbox.created is not None
        assert toolbox.auto_regenerate is True

        # Verify saved
        catalog = service.load()
        assert len(catalog.toolboxes) == 1

    def test_add_duplicate_toolbox(self, service):
        """Test adding toolbox with duplicate ID fails."""
        service.add_toolbox("test", "Test", Path("/test.pyt"))

        with pytest.raises(CatalogError) as exc_info:
            service.add_toolbox("test", "Test2", Path("/test2.pyt"))

        assert "already exists" in str(exc_info.value)

    def test_get_toolbox(self, service):
        """Test getting toolbox by ID."""
        service.add_toolbox("test", "Test", Path("/test.pyt"))

        toolbox = service.get_toolbox("test")
        assert toolbox is not None
        assert toolbox.id == "test"

        assert service.get_toolbox("nonexistent") is None

    def test_list_toolboxes(self, service):
        """Test listing all toolboxes."""
        service.add_toolbox("tb1", "Toolbox 1", Path("/tb1.pyt"))
        service.add_toolbox("tb2", "Toolbox 2", Path("/tb2.pyt"))

        toolboxes = service.list_toolboxes()
        assert len(toolboxes) == 2

    def test_update_toolbox(self, service):
        """Test updating toolbox properties."""
        service.add_toolbox("test", "Test", Path("/test.pyt"))

        updated = service.update_toolbox("test", name="Updated Name", description="New desc")
        assert updated.name == "Updated Name"
        assert updated.description == "New desc"
        assert updated.modified is not None

        # Verify saved
        catalog = service.load()
        toolbox = catalog.get_toolbox_by_id("test")
        assert toolbox is not None
        assert toolbox.name == "Updated Name"

    def test_update_nonexistent_toolbox(self, service):
        """Test updating nonexistent toolbox fails."""
        with pytest.raises(CatalogError):
            service.update_toolbox("nonexistent", name="Test")

    def test_remove_toolbox(self, service):
        """Test removing a toolbox."""
        service.add_toolbox("test", "Test", Path("/test.pyt"))
        service.remove_toolbox("test")

        catalog = service.load()
        assert len(catalog.toolboxes) == 0

    def test_remove_nonexistent_toolbox(self, service):
        """Test removing nonexistent toolbox fails."""
        with pytest.raises(CatalogError):
            service.remove_toolbox("nonexistent")


class TestToolAssignment:
    """Tests for tool assignment operations."""

    def test_add_tool_to_toolbox(self, service):
        """Test adding a tool to a toolbox."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))

        tool_ref = service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        assert tool_ref.source_id == "src"
        assert tool_ref.tool_path == "tools/buffer"
        assert tool_ref.enabled is True

        # Verify saved
        catalog = service.load()
        toolbox = catalog.get_toolbox_by_id("tb")
        assert toolbox is not None
        assert len(toolbox.tools) == 1

    def test_add_tool_with_alias(self, service):
        """Test adding a tool with alias."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))

        tool_ref = service.add_tool_to_toolbox("tb", "src", "tools/buffer", alias="Custom Buffer")

        assert tool_ref.alias == "Custom Buffer"

    def test_add_tool_to_nonexistent_toolbox(self, service):
        """Test adding tool to nonexistent toolbox fails."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))

        with pytest.raises(CatalogError) as exc_info:
            service.add_tool_to_toolbox("nonexistent", "src", "tools/buffer")

        assert "not found" in str(exc_info.value)

    def test_add_tool_from_nonexistent_source(self, service):
        """Test adding tool from nonexistent source fails."""
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))

        with pytest.raises(CatalogError) as exc_info:
            service.add_tool_to_toolbox("tb", "nonexistent", "tools/buffer")

        assert "not found" in str(exc_info.value)

    def test_add_duplicate_tool(self, service):
        """Test adding duplicate tool to toolbox fails."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        with pytest.raises(CatalogError) as exc_info:
            service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        assert "already in toolbox" in str(exc_info.value)

    def test_list_tools_in_toolbox(self, service):
        """Test listing tools in a toolbox."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")
        service.add_tool_to_toolbox("tb", "src", "tools/clip", enabled=False)

        all_tools = service.list_tools_in_toolbox("tb")
        assert len(all_tools) == 2

        enabled_only = service.list_tools_in_toolbox("tb", enabled_only=True)
        assert len(enabled_only) == 1
        assert enabled_only[0].tool_path == "tools/buffer"

    def test_list_tools_nonexistent_toolbox(self, service):
        """Test listing tools for nonexistent toolbox fails."""
        with pytest.raises(CatalogError):
            service.list_tools_in_toolbox("nonexistent")

    def test_update_tool_in_toolbox(self, service):
        """Test updating tool properties in toolbox."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        updated = service.update_tool_in_toolbox(
            "tb", "src", "tools/buffer", enabled=False, alias="New Alias"
        )

        assert updated.enabled is False
        assert updated.alias == "New Alias"

        # Verify saved
        catalog = service.load()
        toolbox = catalog.get_toolbox_by_id("tb")
        assert toolbox is not None
        tool = toolbox.tools[0]
        assert tool.enabled is False

    def test_update_nonexistent_tool(self, service):
        """Test updating nonexistent tool fails."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))

        with pytest.raises(CatalogError) as exc_info:
            service.update_tool_in_toolbox("tb", "src", "tools/buffer", enabled=False)

        assert "not found" in str(exc_info.value)

    def test_remove_tool_from_toolbox(self, service):
        """Test removing a tool from toolbox."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        service.remove_tool_from_toolbox("tb", "src", "tools/buffer")

        catalog = service.load()
        toolbox = catalog.get_toolbox_by_id("tb")
        assert toolbox is not None
        assert len(toolbox.tools) == 0

    def test_remove_nonexistent_tool(self, service):
        """Test removing nonexistent tool fails."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))

        with pytest.raises(CatalogError) as exc_info:
            service.remove_tool_from_toolbox("tb", "src", "tools/buffer")

        assert "not found" in str(exc_info.value)


class TestValidation:
    """Tests for catalog validation."""

    def test_validate_no_warnings(self, service):
        """Test validation with valid catalog."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        warnings = service.validate()
        assert warnings == []

    def test_validate_with_broken_reference(self, service):
        """Test validation detects broken source reference."""
        service.add_source("src", "Source", SourceType.LOCAL, path=Path("/src"))
        service.add_toolbox("tb", "Toolbox", Path("/tb.pyt"))
        service.add_tool_to_toolbox("tb", "src", "tools/buffer")

        # Remove source with force (creates broken reference)
        service.remove_source("src", force=True)

        warnings = service.validate()
        assert len(warnings) == 1
        assert "non-existent source" in warnings[0].lower()
