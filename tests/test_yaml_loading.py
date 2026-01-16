"""Unit tests for YAML configuration loading (no arcpy required)."""

from pathlib import Path

import pytest

from toolbox.framework.config.schema import load_tool_config, load_toolbox_config


@pytest.mark.unit
def test_load_toolbox_config():
    """Test loading toolbox configuration."""
    config_dir = Path(__file__).parent.parent / "toolbox" / "tools" / "config"
    config = load_toolbox_config(config_dir)

    assert config is not None
    assert config.toolbox.label == "YAML Analysis Toolbox"
    assert config.toolbox.alias == "yamlanalysistoolbox"
    assert len(config.tools) == 3  # buffer_analysis, clip_features, load_tool_metadata

    # Check tool references
    assert config.tools[0].name == "buffer_analysis"


@pytest.mark.unit
def test_load_buffer_tool_config():
    """Test loading buffer tool configuration."""
    config_path = (
        Path(__file__).parent.parent
        / "toolbox"
        / "tools"
        / "config"
        / "tools"
        / "buffer_analysis.yml"
    )
    config = load_tool_config(config_path)

    assert config.tool.name == "buffer_analysis"
    assert config.tool.label == "Buffer Analysis"
    assert len(config.parameters) == 5


@pytest.mark.unit
def test_load_clip_tool_config():
    """Test loading clip tool configuration."""
    config_path = (
        Path(__file__).parent.parent
        / "toolbox"
        / "tools"
        / "config"
        / "tools"
        / "clip_features.yml"
    )
    config = load_tool_config(config_path)

    assert config.tool.name == "clip_features"
    assert config.tool.label == "Clip Features"
    assert len(config.parameters) == 3


@pytest.mark.unit
def test_parameter_index_validation():
    """Test that parameter indices are valid (unique, start at 0, no gaps)."""
    config_path = (
        Path(__file__).parent.parent
        / "toolbox"
        / "tools"
        / "config"
        / "tools"
        / "buffer_analysis.yml"
    )
    config = load_tool_config(config_path)

    indices = sorted([p.index for p in config.parameters])
    expected_indices = list(range(len(config.parameters)))

    assert indices == expected_indices
