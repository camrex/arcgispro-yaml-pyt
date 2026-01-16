"""Test metadata loader tool."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_arcpy(monkeypatch):
    """Mock arcpy module for testing."""
    mock = MagicMock()
    mock.Parameter = MagicMock
    mock.AddMessage = MagicMock()
    mock.AddWarning = MagicMock()
    mock.AddError = MagicMock()
    monkeypatch.setitem(globals(), "arcpy", mock)
    return mock


def test_metadata_loader_tool_creation():
    """Test that metadata loader tool can be created from YAML config."""
    from src.framework.factory import create_tool_class

    from .execute import execute_metadata_loader

    config_path = Path(__file__).parent / "tool.yml"
    assert config_path.exists(), f"Config not found: {config_path}"

    # Create the tool class
    LoadToolMetadataTool = create_tool_class(
        "load_tool_metadata", config_path, execute_metadata_loader
    )

    assert LoadToolMetadataTool is not None
    assert LoadToolMetadataTool.__name__ == "LoadToolMetadataTool"

    # Instantiate and check properties
    tool = LoadToolMetadataTool()
    assert tool.label == "Load Tool Metadata"
    assert tool.description == "Update tool metadata XML files from YAML documentation"
    assert tool.category == "Utilities"
    assert tool.canRunInBackground is False

    # Check parameters
    params = tool.getParameterInfo()
    assert len(params) == 1
    assert params[0].name == "output_message"
    assert params[0].direction == "Output"
    assert params[0].parameterType == "Derived"


def test_metadata_loader_in_toolbox():
    """Test that metadata loader tool is registered in the toolbox."""
    from src.framework.config import load_toolbox_config

    # Get utilities toolbox path relative to this test file
    # From: src/tools/load_tool_metadata/test_metadata_loader.py
    # To:   src/toolboxes/utilities/
    utilities_toolbox = Path(__file__).parent.parent.parent / "toolboxes" / "utilities"
    toolbox_config = load_toolbox_config(utilities_toolbox)

    # Check tool is registered
    tool_names = [tool.name for tool in toolbox_config.tools]
    assert "load_tool_metadata" in tool_names

    # Check it's enabled
    metadata_tool = next(t for t in toolbox_config.tools if t.name == "load_tool_metadata")
    assert metadata_tool.enabled is True
    assert metadata_tool.config == "../../tools/load_tool_metadata/tool.yml"


def test_metadata_loader_has_documentation():
    """Test that metadata loader tool has proper documentation."""
    from src.framework.config import load_tool_config

    config_path = Path(__file__).parent / "tool.yml"
    tool_config = load_tool_config(config_path)

    assert tool_config.documentation is not None
    assert len(tool_config.documentation.summary) > 0
    assert len(tool_config.documentation.usage) > 0
    assert len(tool_config.documentation.tags) > 0
    assert "output_message" in tool_config.documentation.parameter_syntax
    assert len(tool_config.documentation.code_samples) > 0
