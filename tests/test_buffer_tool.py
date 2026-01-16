"""Unit tests for buffer analysis."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_load_buffer_config(config_dir):
    """Test loading buffer tool configuration."""
    from toolbox.framework.config.schema import load_tool_config

    config_path = config_dir / "tools" / "buffer_analysis.yml"
    config = load_tool_config(config_path)

    assert config.tool.name == "buffer_analysis"
    assert config.tool.label == "Buffer Analysis"
    assert len(config.parameters) == 5

    # Check parameter indices
    input_param = next(p for p in config.parameters if p.name == "input_features")
    assert input_param.index == 0
    buffer_dist_param = next(p for p in config.parameters if p.name == "buffer_distance")
    assert buffer_dist_param.index == 1


@pytest.mark.unit
def test_buffer_config_validation():
    """Test YAML-based validation for buffer config."""
    from pathlib import Path

    from toolbox.framework.config.schema import load_tool_config

    config_path = (
        Path(__file__).parent.parent
        / "toolbox"
        / "tools"
        / "config"
        / "tools"
        / "buffer_analysis.yml"
    )
    config = load_tool_config(config_path)

    # Verify validation rules are in parameters
    buffer_dist_param = next(p for p in config.parameters if p.name == "buffer_distance")
    assert buffer_dist_param.validation is not None
    assert any(check.type == "greater_than" for check in buffer_dist_param.validation)

    buffer_units_param = next(p for p in config.parameters if p.name == "buffer_units")
    assert buffer_units_param.validation is not None
    assert any(check.type == "one_of" for check in buffer_units_param.validation)


@pytest.mark.unit
def test_dynamic_tool_creation(mock_arcpy, config_dir):
    """Test dynamic tool class creation from YAML."""
    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        # Import AFTER patching arcpy
        from toolbox.framework.factory import create_tool_class
        from toolbox.tools.utils.buffer import execute_buffer

        config_path = config_dir / "tools" / "buffer_analysis.yml"

        # Also patch arcpy in yaml_tool module
        with patch("toolbox.framework.base.yaml_tool.arcpy", mock_arcpy):
            # Create tool class dynamically
            tool_class = create_tool_class("buffer_analysis", config_path, execute_buffer)

            # Instantiate and test
            tool = tool_class()
            assert tool.label == "Buffer Analysis"
            assert tool.category == "Analysis"
            assert tool.canRunInBackground is True


@pytest.mark.unit
def test_dynamic_tool_parameters(mock_arcpy, config_dir):
    """Test dynamically generated tool parameters."""
    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        # Import AFTER patching arcpy
        from toolbox.framework.factory import create_tool_class
        from toolbox.tools.utils.buffer import execute_buffer

        config_path = config_dir / "tools" / "buffer_analysis.yml"

        # Also patch arcpy in yaml_tool module
        with patch("toolbox.framework.base.yaml_tool.arcpy", mock_arcpy):
            # Create tool class dynamically
            tool_class = create_tool_class("buffer_analysis", config_path, execute_buffer)
            tool = tool_class()
            params = tool.getParameterInfo()

            assert len(params) == 5
            assert params[0].name == "input_features"
            assert params[1].name == "buffer_distance"
            assert params[1].value == 100  # default value
            assert params[2].name == "buffer_units"


@pytest.mark.unit
def test_buffer_execution_with_mock(mock_arcpy, mock_parameters, mock_messages, sample_tool_config):
    """Test buffer execution with mocked arcpy."""
    # Reset mock to clear any previous test calls
    mock_arcpy.analysis.Buffer.reset_mock()

    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        from toolbox.tools.utils.buffer import execute_buffer

        # Execute
        execute_buffer(mock_parameters, mock_messages, sample_tool_config)

        # Verify arcpy.Buffer was called
        mock_arcpy.analysis.Buffer.assert_called_once()

        # Verify messages were added
        assert mock_messages.addMessage.called
        assert mock_messages.addMessage.call_count >= 3


@pytest.mark.unit
def test_buffer_with_invalid_distance(
    mock_arcpy, mock_parameters, mock_messages, sample_tool_config
):
    """Test buffer with invalid distance."""
    from toolbox.framework.validation.runtime_validator import ValidationError

    mock_parameters[1].value = -100.0  # Invalid negative

    with patch.dict("sys.modules", {"arcpy": mock_arcpy}):
        from toolbox.tools.utils.buffer import execute_buffer

        with pytest.raises(ValidationError):
            execute_buffer(mock_parameters, mock_messages, sample_tool_config)


@pytest.mark.integration
@pytest.mark.skip(reason="Requires ArcGIS Pro environment")
def test_buffer_integration():
    """Integration test for buffer tool (requires ArcGIS Pro)."""

    # This would require actual test data and ArcGIS Pro
    # Only run in ArcGIS Pro conda environment
    pass
