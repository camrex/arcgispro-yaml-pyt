"""Unit tests for clip analysis."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_load_clip_config(config_dir):
    """Test loading clip tool configuration."""
    from toolbox.framework.config.schema import load_tool_config

    config_path = config_dir / "tools" / "clip_features.yml"
    config = load_tool_config(config_path)

    assert config.tool.name == "clip_features"
    assert config.tool.label == "Clip Features"
    assert len(config.parameters) == 3

    # Check parameter indices
    input_param = next(p for p in config.parameters if p.name == "input_features")
    assert input_param.index == 0
    clip_param = next(p for p in config.parameters if p.name == "clip_features")
    assert clip_param.index == 1


@pytest.mark.unit
def test_clip_config_validation():
    """Test YAML-based validation for clip config."""
    from pathlib import Path

    from toolbox.framework.config.schema import load_tool_config

    config_path = (
        Path(__file__).parent.parent
        / "toolbox"
        / "tools"
        / "config"
        / "tools"
        / "clip_features.yml"
    )
    config = load_tool_config(config_path)

    # Verify config is loaded correctly
    assert config.tool.name == "clip_features"
    assert len(config.parameters) == 3


@pytest.mark.unit
def test_clip_tool_initialization(mock_arcpy, config_dir):
    """Test clip tool initialization via dynamic generation."""
    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        from toolbox.framework.factory import create_tool_class
        from toolbox.tools.utils.clip import execute_clip

        config_path = config_dir / "tools" / "clip_features.yml"

        # Also patch arcpy in yaml_tool module
        with patch("toolbox.framework.base.yaml_tool.arcpy", mock_arcpy):
            # Create tool class dynamically
            tool_class = create_tool_class("clip_features", config_path, execute_clip)
            tool = tool_class()

            assert tool.label == "Clip Features"
            assert tool.category == "Analysis"
            assert tool.canRunInBackground is True


@pytest.mark.unit
def test_clip_tool_parameters(mock_arcpy, config_dir):
    """Test clip tool parameter generation via dynamic tool."""
    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        from toolbox.framework.factory import create_tool_class
        from toolbox.tools.utils.clip import execute_clip

        config_path = config_dir / "tools" / "clip_features.yml"

        # Also patch arcpy in yaml_tool module
        with patch("toolbox.framework.base.yaml_tool.arcpy", mock_arcpy):
            # Create tool class dynamically
            tool_class = create_tool_class("clip_features", config_path, execute_clip)
            tool = tool_class()
            params = tool.getParameterInfo()

            assert len(params) == 3
            assert params[0].name == "input_features"
            assert params[1].name == "clip_features"
            assert params[2].name == "output_features"


@pytest.mark.integration
@pytest.mark.skip(reason="Requires ArcGIS Pro environment")
def test_clip_integration():
    """Integration test for clip tool (requires ArcGIS Pro)."""

    # This would require actual test data and ArcGIS Pro
    # Only run in ArcGIS Pro conda environment
    pass
