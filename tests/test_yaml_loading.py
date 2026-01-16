"""Unit tests for YAML configuration loading (no arcpy required)."""

import pytest

from src.framework.schema import load_tool_config, load_toolbox_config


@pytest.mark.unit
def test_load_toolbox_config(get_toolbox):
    """Test loading toolbox configuration."""
    config = load_toolbox_config(get_toolbox("spatial_analysis"))

    assert config is not None
    assert config.toolbox.label == "Spatial Analysis"
    assert config.toolbox.alias == "spatialanalysis"
    assert len(config.tools) == 2  # buffer_analysis, clip_features

    # Check tool references
    assert config.tools[0].name == "buffer_analysis"


@pytest.mark.unit
def test_load_buffer_tool_config(get_tool):
    """Test loading buffer tool configuration."""
    config = load_tool_config(get_tool("spatial_analysis/buffer_analysis") / "tool.yml")

    assert config.tool.name == "buffer_analysis"
    assert config.tool.label == "Buffer Analysis"
    assert len(config.parameters) == 5


@pytest.mark.unit
def test_load_clip_tool_config(get_tool):
    """Test loading clip tool configuration."""
    config = load_tool_config(get_tool("spatial_analysis/clip_features") / "tool.yml")

    assert config.tool.name == "clip_features"
    assert config.tool.label == "Clip Features"
    assert len(config.parameters) == 3


@pytest.mark.unit
def test_parameter_index_validation(get_tool):
    """Test that parameter indices are valid (unique, start at 0, no gaps)."""
    config = load_tool_config(get_tool("spatial_analysis/buffer_analysis") / "tool.yml")

    indices = sorted([p.index for p in config.parameters])
    expected_indices = list(range(len(config.parameters)))

    assert indices == expected_indices
