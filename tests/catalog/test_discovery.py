"""
Tests for DiscoveryService.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.catalog.discovery import (
    DiscoveredTool,
    DiscoveryError,
    DiscoveryService,
    GitError,
)
from src.catalog.models import Source, SourceType
from src.catalog.service import CatalogService


@pytest.fixture
def temp_catalog_path(tmp_path):
    """Temporary catalog path."""
    return tmp_path / "catalog.yml"


@pytest.fixture
def catalog_service(temp_catalog_path):
    """CatalogService instance with temporary catalog."""
    service = CatalogService(temp_catalog_path)
    service.create_new()
    return service


@pytest.fixture
def discovery_service(catalog_service):
    """DiscoveryService instance."""
    return DiscoveryService(catalog_service)


@pytest.fixture
def temp_source_dir(tmp_path):
    """Create a temporary source directory with tools."""
    source_dir = tmp_path / "test_source"
    source_dir.mkdir()

    # Create tool 1
    tool1_dir = source_dir / "tools" / "buffer"
    tool1_dir.mkdir(parents=True)
    tool1_config = {
        "tool": {
            "name": "buffer_analysis",
            "label": "Buffer Analysis",
            "description": "Create buffer zones",
            "category": "Analysis",
        },
        "implementation": {"executeFunction": "test.buffer.execute"},
        "parameters": [],
    }
    with open(tool1_dir / "tool.yml", "w") as f:
        yaml.safe_dump(tool1_config, f)

    # Create tool 2
    tool2_dir = source_dir / "tools" / "clip"
    tool2_dir.mkdir(parents=True)
    tool2_config = {
        "tool": {
            "name": "clip_features",
            "label": "Clip Features",
            "description": "Clip features",
            "category": "Analysis",
        },
        "implementation": {"executeFunction": "test.clip.execute"},
        "parameters": [],
    }
    with open(tool2_dir / "tool.yml", "w") as f:
        yaml.safe_dump(tool2_config, f)

    # Create toolbox
    toolbox_dir = source_dir / "toolboxes" / "analysis"
    toolbox_dir.mkdir(parents=True)
    toolbox_config = {
        "toolbox": {
            "label": "Analysis Toolbox",
            "alias": "analysis",
            "description": "Analysis tools",
        }
    }
    with open(toolbox_dir / "toolbox.yml", "w") as f:
        yaml.safe_dump(toolbox_config, f)

    return source_dir


class TestDiscoveryService:
    """Tests for DiscoveryService basic operations."""

    def test_init(self, catalog_service):
        """Test service initialization."""
        service = DiscoveryService(catalog_service)
        assert service.catalog_service == catalog_service

    def test_scan_nonexistent_source(self, discovery_service):
        """Test scanning a source that doesn't exist."""
        with pytest.raises(DiscoveryError, match="Source not found"):
            discovery_service.scan_source("nonexistent")

    def test_scan_disabled_source(self, discovery_service, catalog_service):
        """Test scanning a disabled source."""
        catalog_service.add_source(
            "test", "Test", SourceType.LOCAL, path=Path("/test"), enabled=False
        )

        with pytest.raises(DiscoveryError, match="Source is disabled"):
            discovery_service.scan_source("test")


class TestLocalSourceDiscovery:
    """Tests for discovering tools from local sources."""

    def test_scan_local_source(self, discovery_service, catalog_service, temp_source_dir):
        """Test scanning a local source for tools."""
        catalog_service.add_source(
            "local-test", "Local Test", SourceType.LOCAL, path=temp_source_dir
        )

        tools, toolboxes = discovery_service.scan_source("local-test")

        assert len(tools) == 2
        assert len(toolboxes) == 1

        # Check tool details
        tool_ids = {t.tool_id for t in tools}
        assert "buffer_analysis" in tool_ids
        assert "clip_features" in tool_ids

        # Check toolbox details
        assert toolboxes[0].toolbox_id == "analysis"  # Uses alias as ID
        assert toolboxes[0].name == "Analysis Toolbox"

    def test_scan_nonexistent_local_path(self, discovery_service, catalog_service):
        """Test scanning a local path that doesn't exist."""
        catalog_service.add_source(
            "bad-local", "Bad Local", SourceType.LOCAL, path=Path("/nonexistent/path")
        )

        with pytest.raises(DiscoveryError, match="path does not exist"):
            discovery_service.scan_source("bad-local")

    def test_scan_updates_source_metadata(
        self, discovery_service, catalog_service, temp_source_dir
    ):
        """Test that scanning updates source metadata."""
        catalog_service.add_source(
            "local-test", "Local Test", SourceType.LOCAL, path=temp_source_dir
        )

        # Scan source
        discovery_service.scan_source("local-test")

        # Check metadata was updated
        catalog = catalog_service.load()
        source = catalog.get_source_by_id("local-test")

        assert source is not None
        assert source.discovered_tools == 2
        assert source.last_sync is not None
        assert isinstance(source.last_sync, datetime)

    def test_discovered_tool_structure(self, discovery_service, catalog_service, temp_source_dir):
        """Test the structure of discovered tools."""
        catalog_service.add_source(
            "local-test", "Local Test", SourceType.LOCAL, path=temp_source_dir
        )

        tools, _ = discovery_service.scan_source("local-test")
        tool = tools[0]

        assert isinstance(tool, DiscoveredTool)
        assert tool.tool_id in ["buffer_analysis", "clip_features"]
        assert tool.name in ["Buffer Analysis", "Clip Features"]
        assert isinstance(tool.path, Path)
        assert tool.path.exists()
        assert tool.source_id == "local-test"
        assert tool.config is not None


class TestInvalidConfigs:
    """Tests for handling invalid tool/toolbox configurations."""

    def test_scan_with_invalid_tool_config(self, discovery_service, catalog_service, tmp_path):
        """Test scanning with invalid tool config (should skip and continue)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Valid tool
        tool1_dir = source_dir / "tool1"
        tool1_dir.mkdir()
        with open(tool1_dir / "tool.yml", "w") as f:
            yaml.safe_dump(
                {
                    "tool": {
                        "name": "valid",
                        "label": "Valid",
                        "category": "Test",
                        "description": "Valid tool",
                    },
                    "implementation": {"executeFunction": "test.valid"},
                    "parameters": [],
                },
                f,
            )

        # Invalid tool (missing required fields)
        tool2_dir = source_dir / "tool2"
        tool2_dir.mkdir()
        with open(tool2_dir / "tool.yml", "w") as f:
            yaml.safe_dump({"tool": {"name": "invalid"}}, f)  # Missing required fields

        catalog_service.add_source("test", "Test", SourceType.LOCAL, path=source_dir)

        # Should discover only the valid tool
        tools, _ = discovery_service.scan_source("test")
        assert len(tools) == 1
        assert tools[0].tool_id == "valid"

    def test_validate_tool_config_valid(self, discovery_service, tmp_path):
        """Test validating a valid tool config."""
        tool_file = tmp_path / "tool.yml"
        with open(tool_file, "w") as f:
            yaml.safe_dump(
                {
                    "tool": {
                        "name": "test-tool",
                        "label": "Test Tool",
                        "category": "Test",
                        "description": "Test",
                    },
                    "implementation": {"executeFunction": "test.execute"},
                    "parameters": [],
                },
                f,
            )

        is_valid, error = discovery_service.validate_tool_config(tool_file)
        assert is_valid
        assert error is None

    def test_validate_tool_config_invalid(self, discovery_service, tmp_path):
        """Test validating an invalid tool config."""
        tool_file = tmp_path / "tool.yml"
        with open(tool_file, "w") as f:
            yaml.safe_dump({"tool": {"name": "test"}}, f)  # Missing required fields

        is_valid, error = discovery_service.validate_tool_config(tool_file)
        assert not is_valid
        assert error is not None


class TestGitSourceDiscovery:
    """Tests for discovering tools from git sources."""

    @patch("subprocess.run")
    def test_clone_git_repo(self, mock_run, discovery_service, catalog_service, tmp_path):
        """Test cloning a git repository."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        local_path = tmp_path / "git_repo"
        catalog_service.add_source(
            "git-test",
            "Git Test",
            SourceType.GIT,
            url="https://github.com/test/repo",
            local_path=local_path,
            branch="main",
        )

        # Mock rglob to return no tools (just testing clone)
        with patch.object(Path, "rglob", return_value=[]):
            # The scan will try to clone (directory doesn't exist yet)
            # We need to create the directory in the clone function's side effect
            def clone_side_effect(*args, **kwargs):
                local_path.mkdir(parents=True)
                return Mock(returncode=0, stderr="")

            mock_run.side_effect = clone_side_effect
            discovery_service.scan_source("git-test")

        # Verify git clone was called
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "clone" in call_args
        assert "https://github.com/test/repo" in call_args

    @patch("subprocess.run")
    def test_pull_git_repo(self, mock_run, discovery_service, catalog_service, tmp_path):
        """Test pulling latest changes from git repo."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        local_path = tmp_path / "git_repo"
        local_path.mkdir()  # Repo already exists

        catalog_service.add_source(
            "git-test",
            "Git Test",
            SourceType.GIT,
            url="https://github.com/test/repo",
            local_path=local_path,
        )

        # Mock rglob to return no tools
        with patch.object(Path, "rglob", return_value=[]):
            discovery_service.scan_source("git-test")

        # Verify git pull was called
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "pull" in call_args

    @patch("subprocess.run")
    def test_git_clone_failure(self, mock_run, discovery_service, catalog_service, tmp_path):
        """Test handling git clone failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="Authentication failed"
        )

        local_path = tmp_path / "git_repo"
        catalog_service.add_source(
            "git-test",
            "Git Test",
            SourceType.GIT,
            url="https://github.com/test/repo",
            local_path=local_path,
        )

        with pytest.raises(GitError, match="Failed to clone"):
            discovery_service.scan_source("git-test")

    def test_git_source_missing_url(self, discovery_service, catalog_service, tmp_path):
        """Test git source with missing URL raises validation error."""
        # Source validation should catch missing URL at creation time
        catalog = catalog_service.load()

        with pytest.raises(ValueError, match="Git sources must have a 'url' field"):
            catalog.sources.append(
                Source(
                    id="bad-git",
                    name="Bad Git",
                    type=SourceType.GIT,
                    enabled=True,
                    # Missing url - should fail validation
                    local_path=tmp_path / "repo",
                )
            )


class TestScanAllSources:
    """Tests for scanning all sources."""

    def test_scan_all_sources(self, discovery_service, catalog_service, tmp_path):
        """Test scanning all enabled sources."""
        # Create two local sources
        source1 = tmp_path / "source1"
        source1.mkdir()
        tool1_dir = source1 / "tool1"
        tool1_dir.mkdir()
        with open(tool1_dir / "tool.yml", "w") as f:
            yaml.safe_dump(
                {
                    "tool": {
                        "name": "tool1",
                        "label": "Tool 1",
                        "category": "Test",
                        "description": "Tool 1",
                    },
                    "implementation": {"executeFunction": "test.tool1"},
                    "parameters": [],
                },
                f,
            )

        source2 = tmp_path / "source2"
        source2.mkdir()
        tool2_dir = source2 / "tool2"
        tool2_dir.mkdir()
        with open(tool2_dir / "tool.yml", "w") as f:
            yaml.safe_dump(
                {
                    "tool": {
                        "name": "tool2",
                        "label": "Tool 2",
                        "category": "Test",
                        "description": "Tool 2",
                    },
                    "implementation": {"executeFunction": "test.tool2"},
                    "parameters": [],
                },
                f,
            )

        catalog_service.add_source("src1", "Source 1", SourceType.LOCAL, path=source1)
        catalog_service.add_source("src2", "Source 2", SourceType.LOCAL, path=source2)

        results = discovery_service.scan_all_sources()

        assert len(results) == 2
        assert "src1" in results
        assert "src2" in results
        assert len(results["src1"][0]) == 1  # 1 tool in source1
        assert len(results["src2"][0]) == 1  # 1 tool in source2

    def test_scan_all_sources_skips_disabled(self, discovery_service, catalog_service, tmp_path):
        """Test that scan_all skips disabled sources."""
        source1 = tmp_path / "source1"
        source1.mkdir()

        catalog_service.add_source(
            "enabled", "Enabled", SourceType.LOCAL, path=source1, enabled=True
        )
        catalog_service.add_source(
            "disabled",
            "Disabled",
            SourceType.LOCAL,
            path=tmp_path / "nonexistent",
            enabled=False,
        )

        results = discovery_service.scan_all_sources()

        # Should only scan enabled source
        assert "enabled" in results
        assert "disabled" not in results

    def test_scan_all_sources_continues_on_error(
        self, discovery_service, catalog_service, tmp_path
    ):
        """Test that scan_all continues even if one source fails."""
        good_source = tmp_path / "good"
        good_source.mkdir()

        catalog_service.add_source("good", "Good", SourceType.LOCAL, path=good_source)
        catalog_service.add_source("bad", "Bad", SourceType.LOCAL, path=tmp_path / "nonexistent")

        results = discovery_service.scan_all_sources()

        # Should have results for both, but bad one has empty lists
        assert "good" in results
        assert "bad" in results
        assert len(results["bad"][0]) == 0  # No tools
        assert len(results["bad"][1]) == 0  # No toolboxes
