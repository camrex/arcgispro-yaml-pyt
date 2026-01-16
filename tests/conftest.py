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
def toolbox_root():
    """Get path to toolboxes root directory."""
    return Path(__file__).parent.parent / "src" / "toolboxes"


@pytest.fixture
def tools_root():
    """Get path to tools root directory."""
    return Path(__file__).parent.parent / "src" / "tools"


@pytest.fixture
def all_toolboxes(toolbox_root):
    """Discover all toolbox directories (contain toolbox.yml)."""
    toolboxes = []
    for item in toolbox_root.iterdir():
        if item.is_dir() and (item / "toolbox.yml").exists():
            toolboxes.append(item)
    return toolboxes


@pytest.fixture
def all_tools(tools_root):
    """Discover all tool directories (contain tool.yml).

    Searches both standalone tools and tools within toolsets.
    Returns list of tuples: (tool_path, tool_name)
    """
    tools = []

    def find_tools(directory: Path, depth: int = 0):
        """Recursively find tool directories (max depth 2 for toolsets)."""
        if depth > 2:  # Prevent infinite recursion
            return

        for item in directory.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue

            # Check if this is a tool directory
            tool_yml = item / "tool.yml"
            if tool_yml.exists():
                tools.append((item, item.name))
            else:
                # Check subdirectories (for toolsets)
                find_tools(item, depth + 1)

    find_tools(tools_root)
    return tools


@pytest.fixture
def get_toolbox(toolbox_root):
    """Factory fixture to get a specific toolbox by name."""

    def _get_toolbox(name: str) -> Path:
        toolbox_path = toolbox_root / name
        if not toolbox_path.exists():
            raise FileNotFoundError(f"Toolbox not found: {name}")
        return toolbox_path

    return _get_toolbox


@pytest.fixture
def get_tool(tools_root):
    """Factory fixture to get a specific tool by path.

    Usage:
        get_tool("load_tool_metadata")  # Standalone tool
        get_tool("spatial_analysis/buffer_analysis")  # Toolset tool
    """

    def _get_tool(tool_path: str) -> Path:
        tool = tools_root / tool_path
        if not tool.exists():
            raise FileNotFoundError(f"Tool not found: {tool_path}")
        return tool

    return _get_tool


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
