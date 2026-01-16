"""Reusable validation helpers."""

import arcpy


def validate_inputs(feature_class: str, messages) -> bool:
    """
    Validate input feature class exists.

    Args:
        feature_class: Path to feature class
        messages: ArcGIS messages object

    Returns:
        True if valid

    Raises:
        ValueError: If feature class doesn't exist
    """
    if not arcpy.Exists(feature_class):
        error_msg = f"Feature class does not exist: {feature_class}"
        messages.addErrorMessage(error_msg)
        raise ValueError(error_msg)

    messages.addMessage(f"✓ Validated: {feature_class}")
    return True


def check_geometry_type(feature_class: str, expected_type: str, messages) -> bool:
    """
    Check feature class geometry type.

    Args:
        feature_class: Path to feature class
        expected_type: Expected geometry type (Polygon, Point, Polyline)
        messages: ArcGIS messages object

    Returns:
        True if matches
    """
    desc = arcpy.Describe(feature_class)
    actual_type = desc.shapeType

    if actual_type != expected_type:
        messages.addWarningMessage(
            f"Expected {expected_type}, got {actual_type} for {feature_class}"
        )
        return False

    return True
