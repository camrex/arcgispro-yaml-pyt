"""Buffer analysis business logic."""

import arcpy

from src.framework.schema import ToolConfig
from src.framework.validators import validate_all_parameters, validate_inputs
from src.tools.spatial_analysis.helpers.geoprocessing import check_spatial_reference


def execute_buffer(parameters, messages, config: ToolConfig):
    """
    Execute buffer analysis.

    Args:
        parameters: ArcGIS tool parameters
        messages: ArcGIS messages object
        config: Tool configuration loaded from YAML
    """
    try:
        # Build parameter index map from config
        param_map = {p.name: p.index for p in config.parameters}

        # Extract parameters using index from YAML
        input_features = parameters[param_map["input_features"]].valueAsText
        buffer_distance = parameters[param_map["buffer_distance"]].value
        buffer_units = parameters[param_map["buffer_units"]].valueAsText
        dissolve = parameters[param_map["dissolve_output"]].value
        output_features = parameters[param_map["output_features"]].valueAsText

        # Validate parameters against YAML rules
        validate_all_parameters(parameters, config, messages)

        # Validate inputs using helper
        validate_inputs(input_features, messages)

        # Check spatial references using helper
        check_spatial_reference(input_features, messages)

        messages.addMessage(f"Buffering with distance: {buffer_distance} {buffer_units}")

        # Execute geoprocessing
        arcpy.analysis.Buffer(
            in_features=input_features,
            out_feature_class=output_features,
            buffer_distance_or_field=f"{buffer_distance} {buffer_units}",
            dissolve_option="ALL" if dissolve else "NONE",
        )

        # Get result info
        result_count = int(arcpy.management.GetCount(output_features)[0])
        messages.addMessage(f"Created {result_count} buffer features")
        messages.addMessage("Buffer analysis complete!")

    except Exception as e:
        messages.addErrorMessage(f"Error in buffer analysis: {str(e)}")
        raise
