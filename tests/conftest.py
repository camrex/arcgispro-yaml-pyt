"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Mock arcpy before any imports to allow testing without ArcGIS Pro
_mock_arcpy = MagicMock()


# Mock Parameter class
class MockParameter:
    def __init__(self, name, displayName, datatype, parameterType, direction):
        self.name = name
        self.displayName = displayName
        self.datatype = datatype
        self.parameterType = parameterType
        self.direction = direction
        self.description = ""
        self.value = None
        self.valueAsText = None
        self.filter = Mock()
        self.filter.type = None
        self.filter.list = []
        self.columns = None


_mock_arcpy.Parameter = MockParameter
_mock_arcpy.Exists = Mock(return_value=True)

# Mock Describe
mock_desc = Mock()
mock_desc.shapeType = "Polygon"
mock_sr = Mock()
mock_sr.name = "WGS_1984_Web_Mercator_Auxiliary_Sphere"
mock_sr.factoryCode = 3857
mock_desc.spatialReference = mock_sr
_mock_arcpy.Describe = Mock(return_value=mock_desc)

# Mock management
_mock_arcpy.management = Mock()
_mock_arcpy.management.GetCount = Mock(return_value=["100"])
_mock_arcpy.management.CreateFileGDB = Mock()
_mock_arcpy.management.CreateFeatureclass = Mock()

# Mock analysis
_mock_arcpy.analysis = Mock()
_mock_arcpy.analysis.Buffer = Mock()
_mock_arcpy.analysis.Clip = Mock()

# Mock da cursor
_mock_arcpy.da = Mock()

# Install mock in sys.modules before any other imports
sys.modules["arcpy"] = _mock_arcpy


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: integration tests with arcpy")
    config.addinivalue_line("markers", "unit: unit tests without arcpy")
    config.addinivalue_line("markers", "integration: integration tests with arcpy (alias for slow)")


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    return tmp_path / "test_workspace"


@pytest.fixture
def mock_arcpy():
    """Return the global mock arcpy module."""
    return sys.modules["arcpy"]


@pytest.fixture
def config_dir():
    """Get path to config directory."""
    return Path(__file__).parent.parent / "toolbox" / "tools" / "config"


@pytest.fixture
def sample_tool_config(config_dir):
    """Load a sample tool configuration."""
    from toolbox.framework.config.schema import load_tool_config

    return load_tool_config(config_dir / "tools" / "buffer_analysis.yml")


@pytest.fixture
def mock_messages():
    """Mock ArcGIS messages object."""
    messages = Mock()
    messages.addMessage = Mock()
    messages.addWarningMessage = Mock()
    messages.addErrorMessage = Mock()
    return messages


@pytest.fixture
def mock_parameters():
    """Create mock ArcGIS parameters for buffer tool."""
    params = []

    # input_features
    p = Mock()
    p.valueAsText = "C:/data/test.shp"
    p.value = None
    params.append(p)

    # buffer_distance
    p = Mock()
    p.valueAsText = None
    p.value = 100.0
    params.append(p)

    # buffer_units
    p = Mock()
    p.valueAsText = "meters"
    p.value = "meters"  # Set value for validation
    params.append(p)

    # dissolve_output
    p = Mock()
    p.valueAsText = None
    p.value = True
    params.append(p)

    # output_features
    p = Mock()
    p.valueAsText = "C:/data/buffer_output.shp"
    p.value = None
    params.append(p)

    return params
