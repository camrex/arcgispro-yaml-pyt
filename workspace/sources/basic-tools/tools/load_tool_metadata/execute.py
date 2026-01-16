"""Execute function for metadata loader tool."""

import traceback
from pathlib import Path

import arcpy


def execute_metadata_loader(parameters: list) -> None:
    """Load and apply documentation metadata from YAML to tool XML files.

    Args:
        parameters: List of arcpy.Parameter objects:
            [0] output_message (Derived/Output) - Success/error message
    """
    try:
        # Import the metadata generation module

        arcpy.AddMessage("=" * 70)
        arcpy.AddMessage("Loading Tool Metadata from YAML Documentation")
        arcpy.AddMessage("=" * 70)
        arcpy.AddMessage("")

        # Get the toolbox directory
        toolbox_dir = Path(__file__).parent.parent
        arcpy.AddMessage(f"Toolbox directory: {toolbox_dir}")
        arcpy.AddMessage("")

        # Capture the generation process
        from src.framework.config import load_toolbox_config

        config_dir = toolbox_dir / "tools" / "config"
        toolbox_config = load_toolbox_config(config_dir)

        # Generate toolbox metadata if available
        if toolbox_config.documentation:
            arcpy.AddMessage("Generating toolbox metadata...")
            from .metadata_generator import create_toolbox_metadata_xml

            toolbox_xml_content = create_toolbox_metadata_xml(toolbox_config)
            toolbox_xml_path = toolbox_dir / "yaml_toolbox.pyt.xml"

            with open(toolbox_xml_path, "w", encoding="utf-8") as f:
                f.write(toolbox_xml_content)

            arcpy.AddMessage("  ✓ Toolbox metadata → yaml_toolbox.pyt.xml")
            arcpy.AddMessage("")

        arcpy.AddMessage("Processing tools:")

        # Process each enabled tool
        tool_count = 0
        for tool_ref in toolbox_config.tools:
            if not tool_ref.enabled:
                arcpy.AddWarning(f"  ⊗ {tool_ref.name} (disabled - skipped)")
                continue

            tool_config_path = config_dir / tool_ref.config

            if not tool_config_path.exists():
                arcpy.AddWarning(f"  ⊗ {tool_ref.name} (config not found)")
                continue

            # Convert tool name to class name
            class_name = "".join(word.capitalize() for word in tool_ref.name.split("_")) + "Tool"

            # Generate metadata
            try:
                from .metadata_generator import generate_metadata_for_tool

                generate_metadata_for_tool(tool_config_path, toolbox_dir, class_name)

                xml_filename = f"yaml_toolbox.{class_name}.pyt.xml"
                arcpy.AddMessage(f"  ✓ {tool_ref.name} → {xml_filename}")
                tool_count += 1
            except Exception as e:
                arcpy.AddWarning(f"  ⊗ {tool_ref.name} - Error: {e}")
                continue

        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 70)
        arcpy.AddMessage(f"Metadata generation complete! ({tool_count} tools updated)")
        arcpy.AddMessage("=" * 70)
        arcpy.AddMessage("")
        arcpy.AddMessage("Next steps:")
        arcpy.AddMessage("1. Close and reopen the toolbox to see updated metadata")
        arcpy.AddMessage("2. Right-click any tool → Item Description to view")
        arcpy.AddMessage("3. Metadata files saved as: yaml_toolbox.{ToolName}.pyt.xml")

        # Set output parameter
        parameters[0].value = f"Successfully updated metadata for {tool_count} tool(s)"

    except Exception as e:
        error_msg = f"Error loading metadata: {str(e)}\n{traceback.format_exc()}"
        arcpy.AddError(error_msg)
        parameters[0].value = f"Error: {str(e)}"
        raise
