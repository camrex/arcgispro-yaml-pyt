"""Tests for YAML configuration loading and validation."""

import pytest


@pytest.mark.unit
def test_load_toolbox_config(get_toolbox):
    """Test loading main toolbox configuration."""
    from src.framework.schema import load_toolbox_config

    config = load_toolbox_config(get_toolbox("spatial_analysis"))

    assert config.toolbox.label == "Spatial Analysis"
    assert config.toolbox.alias == "spatialanalysis"
    assert config.toolbox.version == "1.0.0"
    assert len(config.tools) == 2  # buffer_analysis, clip_features

    # Check tool references
    tool_names = [t.name for t in config.tools]
    assert "buffer_analysis" in tool_names
    assert "clip_features" in tool_names


@pytest.mark.unit
def test_tool_config_parameter_validation(get_tool):
    """Test that tool configs have valid parameter indices."""
    from src.framework.schema import load_tool_config

    # Buffer tool
    buffer_config = load_tool_config(get_tool("spatial_analysis/buffer_analysis") / "tool.yml")
    assert len(buffer_config.parameters) == 5
    # Check all indices are present
    indices = {p.index for p in buffer_config.parameters}
    assert indices == {0, 1, 2, 3, 4}

    # Clip tool
    clip_config = load_tool_config(get_tool("spatial_analysis/clip_features") / "tool.yml")
    assert len(clip_config.parameters) == 3
    # Check all indices are present
    indices = {p.index for p in clip_config.parameters}
    assert indices == {0, 1, 2}


@pytest.mark.unit
def test_parameter_config_validation():
    """Test parameter configuration validation."""
    from src.framework.schema import FilterConfig, ParameterConfig

    # Valid parameter with range filter
    param = ParameterConfig(
        name="test_param",
        displayName="Test Parameter",
        datatype="GPDouble",
        parameterType="Required",
        direction="Input",
        index=0,
        validation=None,
        filter=FilterConfig(type="Range", min=0, max=100),
    )
    assert param.name == "test_param"
    assert param.filter.type == "Range"  # type: ignore

    # Valid parameter with value list filter
    param2 = ParameterConfig(
        name="test_param2",
        displayName="Test Parameter 2",
        datatype="GPString",
        parameterType="Optional",
        direction="Input",
        index=1,
        validation=None,
        filter=FilterConfig(type="ValueList", values=["a", "b", "c"]),
    )
    assert param2.filter.values == ["a", "b", "c"]  # type: ignore


@pytest.mark.unit
def test_invalid_tool_config_duplicate_indices(tmp_path):
    """Test that invalid tool config with duplicate indices fails validation."""
    import yaml

    from src.framework.schema import load_tool_config

    # Create invalid config with duplicate indices
    invalid_config = {
        "tool": {
            "name": "test_tool",
            "label": "Test Tool",
            "description": "Test",
            "category": "Test",
        },
        "implementation": {
            "executeFunction": "test.execute",
        },
        "parameters": [
            {
                "name": "param1",
                "displayName": "Param 1",
                "datatype": "GPString",
                "parameterType": "Required",
                "direction": "Input",
                "index": 0,
            },
            {
                "name": "param2",
                "displayName": "Param 2",
                "datatype": "GPString",
                "parameterType": "Required",
                "direction": "Input",
                "index": 0,  # Duplicate index!
            },
        ],
    }

    # Write to temp file
    test_config_path = tmp_path / "test_tool.yml"
    with open(test_config_path, "w") as f:
        yaml.dump(invalid_config, f)

    # Should raise validation error
    with pytest.raises(Exception, match="Duplicate parameter indices"):
        load_tool_config(test_config_path)
