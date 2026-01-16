"""Tests for clip analysis."""

from unittest.mock import Mock, patch

import pytest

from src.framework.config import (
    ImplementationConfig,
    ParameterConfig,
    ToolConfig,
    ToolMetadata,
)

from .execute import execute_clip


@pytest.fixture
def mock_clip_config():
    """Create mock tool configuration."""
    return ToolConfig(
        tool=ToolMetadata(
            name="clip_features",
            label="Clip Features",
            description="Clip features",
            category="Analysis",
        ),
        implementation=ImplementationConfig(
            executeFunction="toolbox.utils.clip.execute_clip",
        ),
        parameters=[
            ParameterConfig(
                name="input_features",
                displayName="Input Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input",
                index=0,
                validation=None,
            ),
            ParameterConfig(
                name="clip_features",
                displayName="Clip Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input",
                index=1,
                validation=None,
            ),
            ParameterConfig(
                name="output_features",
                displayName="Output Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Output",
                index=2,
                validation=None,
            ),
        ],
    )


@pytest.fixture
def mock_parameters():
    """Create mock ArcGIS parameters."""
    params = [Mock() for _ in range(3)]
    params[0].valueAsText = "input.shp"
    params[1].valueAsText = "clip.shp"
    params[2].valueAsText = "output.shp"
    return params


def test_clip_execution(mock_clip_config, mock_parameters):
    """Test clip execution with mocked ArcPy."""
    messages = Mock()

    with patch("toolbox.tools.spatial_analysis.clip_features.execute.arcpy") as mock_arcpy:
        # Mock GetCount results
        mock_arcpy.management.GetCount.side_effect = [["100"], ["50"]]

        # Execute
        execute_clip(mock_parameters, messages, mock_clip_config)

        # Verify arcpy.Clip was called
        mock_arcpy.analysis.Clip.assert_called_once()

        # Verify messages
        assert messages.addMessage.called
