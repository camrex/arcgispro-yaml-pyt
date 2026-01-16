"""Generate ArcGIS Pro metadata XML files from YAML tool documentation.

This module is part of the load_tool_metadata tool and handles XML generation
for both tool and toolbox metadata from YAML configuration files.
"""

import html
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from src.framework.config import ToolConfig


def wrap_in_html_div(text: str, preserve_newlines: bool = False) -> str:
    """Wrap text content in ArcGIS Pro HTML DIV format.

    Args:
        text: Plain text content
        preserve_newlines: If True, converts newlines to paragraphs (keeps "- " for bullets)

    Returns:
        HTML-formatted text in ArcGIS Pro style
    """
    if not preserve_newlines:
        # Simple paragraph for single-line text
        text_escaped = html.escape(text.strip())
        content = f"<P><SPAN>{text_escaped}</SPAN></P>"
        return f'<DIV STYLE="text-align:Left;"><DIV>{content}</DIV></DIV>'

    # Parse text with paragraphs, keeping bullet points as "- " text with line breaks
    lines = text.strip().split("\n")
    paragraphs = []
    current_paragraph_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line - finish current paragraph
            if current_paragraph_lines:
                # Escape each line individually, then join with <BR/>
                escaped_lines = [html.escape(line) for line in current_paragraph_lines]
                para_text = "<BR/>".join(escaped_lines)
                paragraphs.append(f"<P><SPAN>{para_text}</SPAN></P>")
                current_paragraph_lines = []
            continue

        # Check if this is a continuation of a bullet point (doesn't start with "- ")
        if (
            current_paragraph_lines
            and not stripped.startswith("- ")
            and current_paragraph_lines[-1].startswith("- ")
        ):
            # Join continuation line to previous bullet point
            current_paragraph_lines[-1] += " " + stripped
        else:
            # Add as new line (either new bullet or regular text)
            current_paragraph_lines.append(stripped)

    # Add any remaining content
    if current_paragraph_lines:
        # Escape each line individually, then join with <BR/>
        escaped_lines = [html.escape(line) for line in current_paragraph_lines]
        para_text = "<BR/>".join(escaped_lines)
        paragraphs.append(f"<P><SPAN>{para_text}</SPAN></P>")

    content = "".join(paragraphs)
    return f'<DIV STYLE="text-align:Left;"><DIV>{content}</DIV></DIV>'


def create_tool_metadata_xml(tool_config: ToolConfig, tool_class_name: str) -> str:
    """Create XML metadata for a tool from its configuration.

    Args:
        tool_config: Validated tool configuration with documentation
        tool_class_name: Name of the tool class (e.g., "BufferAnalysisTool")

    Returns:
        Formatted XML string for the tool metadata
    """
    if not tool_config.documentation:
        # Return minimal XML if no documentation is provided
        return """<?xml version="1.0"?>
<metadata xml:lang="en"><Esri><CreaDate>20260115</CreaDate><CreaTime>16363800</CreaTime><ArcGISFormat>1.0</ArcGISFormat><SyncOnce>TRUE</SyncOnce></Esri></metadata>"""

    doc = tool_config.documentation

    # Create root element
    root = ET.Element("metadata")
    root.set("xml:lang", "en")

    # Esri metadata
    esri = ET.SubElement(root, "Esri")
    ET.SubElement(esri, "CreaDate").text = "20260115"
    ET.SubElement(esri, "CreaTime").text = "16363800"
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    ET.SubElement(esri, "SyncOnce").text = "TRUE"

    # Tool metadata
    tool = ET.SubElement(root, "tool")
    tool.set("name", tool_class_name)
    tool.set("displayname", tool_config.tool.label)
    tool.set("toolboxalias", "yamlanalysistoolbox")
    tool.set("xmlns", "")

    # ArcToolbox help path (standard)
    ET.SubElement(
        tool, "arcToolboxHelpPath"
    ).text = r"c:\program files\arcgis\pro\Resources\Help\gp"

    # Parameters
    if doc.parameter_syntax:
        parameters = ET.SubElement(tool, "parameters")

        for param in tool_config.parameters:
            param_elem = ET.SubElement(parameters, "param")
            param_elem.set("name", param.name)
            param_elem.set("displayname", param.displayName)
            param_elem.set("type", param.parameterType)
            param_elem.set("direction", param.direction)
            param_elem.set("datatype", param.datatype)
            param_elem.set("expression", param.name)

            if param.name in doc.parameter_syntax:
                param_doc = doc.parameter_syntax[param.name]

                # Dialog explanation with HTML formatting
                ET.SubElement(param_elem, "dialogReference").text = wrap_in_html_div(
                    param_doc.dialog_explanation
                )

                # Scripting explanation with HTML formatting
                ET.SubElement(param_elem, "pythonReference").text = wrap_in_html_div(
                    param_doc.scripting_explanation
                )

    # Summary/Abstract with HTML formatting
    ET.SubElement(tool, "summary").text = wrap_in_html_div(doc.summary)

    # Usage with HTML formatting (preserves newlines/lists)
    ET.SubElement(tool, "usage").text = wrap_in_html_div(doc.usage, preserve_newlines=True)

    # Code samples
    if doc.code_samples:
        script_examples = ET.SubElement(tool, "scriptExamples")

        for sample in doc.code_samples:
            script_example = ET.SubElement(script_examples, "scriptExample")
            ET.SubElement(script_example, "title").text = sample.title
            ET.SubElement(script_example, "para").text = wrap_in_html_div(sample.description)
            ET.SubElement(script_example, "code").text = sample.code.strip()

    # Data identification info with search keywords
    data_id_info = ET.SubElement(root, "dataIdInfo")
    id_citation = ET.SubElement(data_id_info, "idCitation")
    ET.SubElement(id_citation, "resTitle").text = tool_config.tool.label

    if doc.tags:
        search_keys = ET.SubElement(data_id_info, "searchKeys")
        for tag in doc.tags:
            ET.SubElement(search_keys, "keyword").text = tag

    # Credits
    if doc.credits:
        ET.SubElement(data_id_info, "idCredit").text = doc.credits

    # Use limitations
    if doc.use_limitations:
        res_consts = ET.SubElement(data_id_info, "resConst")
        consts = ET.SubElement(res_consts, "Consts")
        ET.SubElement(consts, "useLimit").text = wrap_in_html_div(
            doc.use_limitations, preserve_newlines=True
        )

    # Distribution info
    dist_info = ET.SubElement(root, "distInfo")
    distributor = ET.SubElement(dist_info, "distributor")
    distor_format = ET.SubElement(distributor, "distorFormat")
    ET.SubElement(distor_format, "formatName").text = "ArcToolbox Tool"

    # Metadata hierarchy level
    md_hr_lv = ET.SubElement(root, "mdHrLv")
    scope_cd = ET.SubElement(md_hr_lv, "ScopeCd")
    scope_cd.set("value", "005")

    # Metadata date stamp
    md_date_st = ET.SubElement(root, "mdDateSt")
    md_date_st.set("Sync", "TRUE")
    md_date_st.text = "20260115"

    # Convert to string without pretty printing (ArcGIS Pro uses compact format)
    xml_str = ET.tostring(root, encoding="unicode")

    # Add XML declaration
    return f'<?xml version="1.0"?>\n{xml_str}'


def generate_metadata_for_tool(
    tool_config_path: Path, output_dir: Path, tool_class_name: str
) -> None:
    """Generate metadata XML for a single tool.

    Args:
        tool_config_path: Path to tool YAML configuration file
        output_dir: Directory where .pyt.xml file will be written
        tool_class_name: Name of the tool class for the XML filename
    """
    # Load tool configuration
    with open(tool_config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tool_config = ToolConfig(**data)

    # Generate XML
    xml_content = create_tool_metadata_xml(tool_config, tool_class_name)

    # Write XML file
    # Format: yaml_toolbox.{ToolClassName}.pyt.xml
    xml_filename = f"yaml_toolbox.{tool_class_name}.pyt.xml"
    xml_path = output_dir / xml_filename

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)


def create_toolbox_metadata_xml(toolbox_config) -> str:
    """Create XML metadata for the toolbox from its configuration.

    Args:
        toolbox_config: Validated toolbox configuration

    Returns:
        Formatted XML string for the toolbox metadata
    """
    doc = toolbox_config.documentation

    if not doc:
        # Return minimal XML if no documentation is provided
        return """<?xml version="1.0"?>
<metadata xml:lang="en"><Esri><CreaDate>20260115</CreaDate><CreaTime>16183200</CreaTime><ArcGISFormat>1.0</ArcGISFormat><SyncOnce>TRUE</SyncOnce></Esri></metadata>"""

    # Create root element
    root = ET.Element("metadata")
    root.set("xml:lang", "en")

    # Esri metadata
    esri = ET.SubElement(root, "Esri")
    ET.SubElement(esri, "CreaDate").text = "20260115"
    ET.SubElement(esri, "CreaTime").text = "16183200"
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    ET.SubElement(esri, "SyncOnce").text = "TRUE"

    # Toolbox element
    toolbox = ET.SubElement(root, "toolbox")
    toolbox.set("name", "yaml_toolbox")
    toolbox.set("alias", toolbox_config.toolbox.alias)

    ET.SubElement(
        toolbox, "arcToolboxHelpPath"
    ).text = r"c:\program files\arcgis\pro\Resources\Help\gp"
    ET.SubElement(toolbox, "toolsets")

    # Data identification info
    data_id_info = ET.SubElement(root, "dataIdInfo")

    # Title - use toolbox label (consistent with tool behavior)
    id_citation = ET.SubElement(data_id_info, "idCitation")
    ET.SubElement(id_citation, "resTitle").text = toolbox_config.toolbox.label

    # Purpose (summary) - plain text
    ET.SubElement(data_id_info, "idPurp").text = doc.summary.strip()

    # Abstract (description) - HTML formatted
    ET.SubElement(data_id_info, "idAbs").text = wrap_in_html_div(
        doc.description, preserve_newlines=True
    )

    # Credits - plain text
    if doc.credits:
        ET.SubElement(data_id_info, "idCredit").text = doc.credits.strip()

    # Search keywords/tags
    if doc.tags:
        search_keys = ET.SubElement(data_id_info, "searchKeys")
        for tag in doc.tags:
            ET.SubElement(search_keys, "keyword").text = tag

    # Use limitations
    if doc.use_limitations:
        res_consts = ET.SubElement(data_id_info, "resConst")
        consts = ET.SubElement(res_consts, "Consts")
        ET.SubElement(consts, "useLimit").text = wrap_in_html_div(
            doc.use_limitations, preserve_newlines=True
        )

    # Distribution info
    dist_info = ET.SubElement(root, "distInfo")
    distributor = ET.SubElement(dist_info, "distributor")
    distor_format = ET.SubElement(distributor, "distorFormat")
    ET.SubElement(distor_format, "formatName").text = "ArcToolbox Toolbox"

    # Metadata date stamp
    md_date_st = ET.SubElement(root, "mdDateSt")
    md_date_st.set("Sync", "TRUE")
    md_date_st.text = "20260115"

    # Convert to string
    xml_str = ET.tostring(root, encoding="unicode")

    # Add XML declaration
    return f'<?xml version="1.0"?>\n{xml_str}'
