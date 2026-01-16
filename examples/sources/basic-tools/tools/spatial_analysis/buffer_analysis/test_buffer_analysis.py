"""Tests for buffer analysis."""

from unittest.mock import Mock, patch

import pytest

from src.framework.config import (
    ImplementationConfig,
    ParameterConfig,
    ToolConfig,
    ToolMetadata,
    ValidationCheck,
)

from .execute import execute_buffer


@pytest.fixture
def mock_buffer_config():
    """Create mock tool configuration."""
    return ToolConfig(
        tool=ToolMetadata(
            name="buffer_analysis",
            label="Buffer Analysis",
            description="Buffer features",
            category="Analysis",
        ),
        implementation=ImplementationConfig(
            executeFunction="toolbox.utils.buffer.execute_buffer",
        ),
        parameters=[
            ParameterConfig(
                name="input_features",
                displayName="Input Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input",
                index=0,
                validation=[],
            ),
            ParameterConfig(
                name="buffer_distance",
                displayName="Buffer Distance",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input",
                index=1,
                validation=[
                    ValidationCheck(
                        type="greater_than", value=0, message="Buffer distance must be positive"
                    )
                ],
            ),
            ParameterConfig(
                name="buffer_units",
                displayName="Buffer Units",
                datatype="GPString",
                parameterType="Required",
                direction="Input",
                index=2,
                validation=[],
            ),
            ParameterConfig(
                name="dissolve_output",
                displayName="Dissolve Output",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input",
                index=3,
                validation=[],
            ),
            ParameterConfig(
                name="output_features",
                displayName="Output Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Output",
                index=4,
                validation=[],
            ),
        ],
    )


@pytest.fixture
def mock_parameters():
    """Create mock ArcGIS parameters."""
    params = [Mock() for _ in range(5)]
    params[0].valueAsText = "input.shp"
    params[0].value = None
    params[1].valueAsText = None
    params[1].value = 100.0
    params[2].valueAsText = "meters"
    params[2].value = None
    params[3].valueAsText = None
    params[3].value = True
    params[4].valueAsText = "output.shp"
    params[4].value = None
    return params


def test_buffer_execution(mock_buffer_config, mock_parameters):
    """Test buffer execution with mocked ArcPy."""
    messages = Mock()

    with patch("toolbox.tools.spatial_analysis.buffer_analysis.execute.arcpy") as mock_arcpy:
        # Mock GetCount result
        mock_arcpy.management.GetCount.return_value = ["42"]

        # Execute
        execute_buffer(mock_parameters, messages, mock_buffer_config)

        # Verify arcpy.Buffer was called
        mock_arcpy.analysis.Buffer.assert_called_once()

        # Verify messages
        assert messages.addMessage.called
        assert "42" in str(messages.addMessage.call_args_list[-2])


def test_buffer_with_invalid_distance(mock_buffer_config, mock_parameters):
    """Test buffer with invalid distance."""
    from src.framework.validators import ValidationError

    mock_parameters[1].value = -100.0  # Invalid negative
    messages = Mock()

    with pytest.raises(ValidationError):
        execute_buffer(mock_parameters, messages, mock_buffer_config)
