"""Reusable geoprocessing helpers."""

import arcpy


def check_spatial_reference(feature_class: str, messages):
    """
    Check and report spatial reference.

    Args:
        feature_class: Path to feature class
        messages: ArcGIS messages object
    """
    desc = arcpy.Describe(feature_class)
    sr = desc.spatialReference

    if sr.name == "Unknown":
        messages.addWarningMessage(f"Warning: {feature_class} has unknown spatial reference")
    else:
        messages.addMessage(f"Spatial Reference: {sr.name} (WKID: {sr.factoryCode})")


def get_feature_count(feature_class: str) -> int:
    """
    Get feature count.

    Args:
        feature_class: Path to feature class

    Returns:
        Number of features
    """
    return int(arcpy.management.GetCount(feature_class)[0])
