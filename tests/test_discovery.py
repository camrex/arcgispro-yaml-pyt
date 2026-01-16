"""Tests for auto-discovery of toolboxes and tools."""

import pytest


@pytest.mark.unit
def test_discover_all_toolboxes(all_toolboxes):
    """Test that all toolboxes are discovered."""
    assert len(all_toolboxes) >= 2  # At least spatial_analysis and utilities

    toolbox_names = [tb.name for tb in all_toolboxes]
    assert "spatial_analysis" in toolbox_names
    assert "utilities" in toolbox_names

    # Each should have a toolbox.yml
    for toolbox in all_toolboxes:
        assert (toolbox / "toolbox.yml").exists()


@pytest.mark.unit
def test_discover_all_tools(all_tools):
    """Test that all tools are discovered."""
    assert len(all_tools) >= 3  # At least buffer_analysis, clip_features, load_tool_metadata

    tool_names = [name for _, name in all_tools]
    assert "buffer_analysis" in tool_names
    assert "clip_features" in tool_names
    assert "load_tool_metadata" in tool_names

    # Each should have a tool.yml
    for tool_path, _ in all_tools:
        assert (tool_path / "tool.yml").exists()


@pytest.mark.unit
def test_all_tools_have_valid_config(all_tools):
    """Test that all discovered tools have valid YAML configuration."""
    from src.framework.config import load_tool_config

    for tool_path, tool_name in all_tools:
        config = load_tool_config(tool_path / "tool.yml")
        assert config.tool.name == tool_name
        assert len(config.tool.label) > 0
        assert len(config.parameters) >= 0


@pytest.mark.unit
def test_all_toolboxes_have_valid_config(all_toolboxes):
    """Test that all discovered toolboxes have valid YAML configuration."""
    from src.framework.config import load_toolbox_config

    for toolbox_path in all_toolboxes:
        config = load_toolbox_config(toolbox_path)
        assert len(config.toolbox.label) > 0
        assert len(config.toolbox.alias) > 0
        assert len(config.tools) > 0


@pytest.mark.unit
def test_factory_fixtures(get_toolbox, get_tool):
    """Test factory fixtures for getting specific toolboxes and tools."""
    # Test getting toolbox
    spatial_tb = get_toolbox("spatial_analysis")
    assert spatial_tb.exists()
    assert (spatial_tb / "toolbox.yml").exists()

    # Test getting standalone tool
    metadata_tool = get_tool("load_tool_metadata")
    assert metadata_tool.exists()
    assert (metadata_tool / "tool.yml").exists()

    # Test getting toolset tool
    buffer_tool = get_tool("spatial_analysis/buffer_analysis")
    assert buffer_tool.exists()
    assert (buffer_tool / "tool.yml").exists()

    # Test error handling
    with pytest.raises(FileNotFoundError):
        get_toolbox("nonexistent_toolbox")

    with pytest.raises(FileNotFoundError):
        get_tool("nonexistent/tool")
