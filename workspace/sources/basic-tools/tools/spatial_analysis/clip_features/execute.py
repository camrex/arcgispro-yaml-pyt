"""Clip features business logic."""

import arcpy

from src.framework.config import ToolConfig
from src.framework.validators import validate_all_parameters, validate_inputs

from ..helpers.geoprocessing import (
    check_spatial_reference,
    get_feature_count,
)


def execute_clip(parameters, messages, config: ToolConfig):
    """
    Execute clip operation.

    Args:
        parameters: ArcGIS tool parameters
        messages: ArcGIS messages object
        config: Tool configuration from YAML
    """
    try:
        # Build parameter index map from config
        param_map = {p.name: p.index for p in config.parameters}

        # Extract parameters using index from YAML
        input_features = parameters[param_map["input_features"]].valueAsText
        clip_features = parameters[param_map["clip_features"]].valueAsText
        output_features = parameters[param_map["output_features"]].valueAsText

        # Validate parameters against YAML rules
        validate_all_parameters(parameters, config, messages)

        messages.addMessage("Validating inputs...")

        # Validate all inputs using helper
        validate_inputs(input_features, messages)
        validate_inputs(clip_features, messages)

        # Check spatial references
        check_spatial_reference(input_features, messages)
        check_spatial_reference(clip_features, messages)

        # Get input counts
        input_count = get_feature_count(input_features)
        messages.addMessage(f"Input features: {input_count:,}")

        messages.addMessage("Clipping features...")

        # Execute clip
        arcpy.analysis.Clip(
            in_features=input_features,
            clip_features=clip_features,
            out_feature_class=output_features,
        )

        # Report results
        result_count = get_feature_count(output_features)
        messages.addMessage(f"✓ Created {result_count:,} clipped features")
        messages.addMessage("Clip complete!")

    except Exception as e:
        messages.addErrorMessage(f"Error in clip: {str(e)}")
        raise
