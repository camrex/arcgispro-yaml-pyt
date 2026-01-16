# ArcGIS Pro Tool Metadata Documentation

## Overview

This project supports generating rich metadata for both ArcGIS Pro Python Toolboxes and individual tools directly from YAML configuration files. The metadata appears in the Item Description and provides comprehensive documentation for users.

## Toolbox-Level Metadata

The `documentation` section in [toolbox.yml](../src/config/toolbox.yml) supports the following elements:

### Structure

```yaml
# Note: The toolbox title comes from src.label, not documentation.title
documentation:
  summary: |
    A brief purpose statement for the toolbox (1-3 sentences)
  description: |
    Detailed abstract describing the toolbox, its features, and capabilities.
    Can include multiple paragraphs and structured information.
  tags:
    - keyword1
    - keyword2
  credits: |
    Attribution and credits for the toolbox
  use_limitations: |
    Legal restrictions, usage policies, warranty disclaimers
```

### Fields

- **summary** (required): Purpose/summary statement
- **description** (required): Detailed abstract/description
- **tags** (optional): Search keywords for finding the toolbox
- **credits** (optional): Attribution and authorship information
- **use_limitations** (optional): Legal usage restrictions, warranty disclaimers, compliance requirements

**Note**: The toolbox title displayed in ArcGIS Pro comes from `toolbox.label` in the toolbox section, not from the documentation.

## Tool-Level Metadata

The `documentation` section in tool YAML files supports the following elements:

### 1. Summary (Required)
Brief abstract describing the tool's purpose. Displays at the top of the tool documentation.

```yaml
documentation:
  summary: |
    Creates buffer polygons around input features at a specified distance.
    Buffers are useful for proximity analysis and creating service areas.
```

### 2. Usage (Required)
Detailed usage information, tips, and best practices. Supports:
- Multiple paragraphs (separated by blank lines)
- Bullet lists (lines starting with `- `)
- Formatted text with proper HTML rendering

```yaml
documentation:
  usage: |
    The Buffer Analysis tool creates buffer polygons at a specified distance.
    
    Tips and Best Practices:
    - Buffer distances must be positive numbers
    - Use appropriate units for your analysis scale
    - Enable "Dissolve Output" to merge overlapping buffers
```

### 3. Tags (Optional)
Search keywords for finding the tool in ArcGIS Pro.

```yaml
documentation:
  tags:
    - buffer
    - proximity
    - analysis
    - spatial analysis
```

### 4. Credits (Optional)
Attribution and authorship information for the tool.

```yaml
documentation:
  credits: |
    Example tool demonstrating YAML-based configuration for ArcGIS Pro Python Toolbox. 
    Based on standard ArcGIS Buffer analysis operations.
```

### 5. Use Limitations (Optional)
Legal usage restrictions, warranty disclaimers, compliance requirements, and usage policies.

```yaml
documentation:
  use_limitations: |
    This tool is provided for educational and demonstration purposes. Users may 
    apply this tool to their analysis workflows subject to:
    - No warranty for accuracy or fitness for specific applications
    - User responsibility for validating results against authoritative sources
    - Compliance with organizational data usage and licensing policies
    - Not certified for regulatory or legal boundary determinations
```

**Note**: Use limitations should focus on legal/policy restrictions (who can use it, for what purposes, warranty disclaimers) rather than technical constraints.

### 6. Parameter Syntax (Recommended)
Detailed documentation for each parameter with separate explanations for dialog (GUI) and scripting usage.

```yaml
documentation:
  parameter_syntax:
    input_features:
      dialog_explanation: |
        The input point, line, or polygon features to be buffered. The features 
        can be from a feature class, shapefile, or layer in your map.
      scripting_explanation: |
        A string representing the path to the feature class, shapefile, or layer 
        name. Example: r"C:\Data\cities.shp" or "cities_layer"
```

### 7. Code Samples (Recommended)
Example code showing how to use the tool from Python scripts.

```yaml
documentation:
  code_samples:
    - title: "Basic Buffer with Default Settings"
      description: |
        Create a 100-meter buffer around city points with dissolved output.
      code: |
        import arcpy
        
        input_fc = r"C:\Data\cities.shp"
        output_fc = r"C:\Data\output.gdb\city_buffers"
        
        arcpy.yamlanalysistoolbox.BufferAnalysis(
            input_fc, 100, "meters", True, output_fc
        )
```

## Generating Metadata XML

### Automatic Generation

Run the metadata generator script to create `.pyt.xml` files from YAML documentation:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Generate metadata for all tools
python src/scripts/generate_metadata_xml.py
```

This creates XML files like:
- `yaml_toolbox.BufferAnalysisTool.pyt.xml`
- `yaml_toolbox.ClipFeaturesTool.pyt.xml`

### Manual Editing in ArcGIS Pro

You can also edit metadata directly in ArcGIS Pro:

1. Open the toolbox in ArcGIS Pro Catalog
2. Right-click a tool → **Item Description**
3. Click **Edit** to modify metadata
4. Fill in Summary, Usage, Parameter descriptions, Code Samples, etc.
5. Save changes

ArcGIS Pro stores edits in the `.pyt.xml` file using HTML-formatted XML.

## XML Format Details

The generated XML uses ArcGIS Pro's expected structure:

```xml
<metadata xml:lang="en">
  <Esri>
    <CreaDate>20260115</CreaDate>
    <ArcGISFormat>1.0</ArcGISFormat>
    <SyncOnce>TRUE</SyncOnce>
  </Esri>
  
  <tool name="BufferAnalysisTool" displayname="Buffer Analysis" toolboxalias="yamlanalysistoolbox">
    <arcToolboxHelpPath>c:\program files\arcgis\pro\Resources\Help\gp</arcToolboxHelpPath>
    
    <parameters>
      <param name="input_features" displayname="Input Features" type="Required" direction="Input">
        <dialogReference>HTML-formatted text for GUI users</dialogReference>
        <pythonReference>HTML-formatted text for Python scripters</pythonReference>
      </param>
    </parameters>
    
    <summary>HTML-formatted summary</summary>
    <usage>HTML-formatted usage with lists and paragraphs</usage>
    
    <scriptExamples>
      <scriptExample>
        <title>Sample Title</title>
        <para>HTML-formatted description</para>
        <code>Python code here</code>
      </scriptExample>
    </scriptExamples>
  </tool>
  
  <dataIdInfo>
    <searchKeys>
      <keyword>buffer</keyword>
      <keyword>analysis</keyword>
    </searchKeys>
  </dataIdInfo>
</metadata>
```

### HTML Formatting

Text content is wrapped in HTML DIV/SPAN tags with specific styles:

```html
<DIV STYLE="text-align:Left;"><DIV><P><SPAN>Your text here</SPAN></P></DIV></DIV>
```

Bullet lists use UL/LI tags:

```html
<UL><LI><P><SPAN>Bullet point text</SPAN></P></LI></UL>
```

## Workflow Integration

### Development Workflow

1. **Edit YAML**: Add/update `documentation` section in tool YAML files
2. **Generate XML**: Run `generate_metadata_xml.py` to create `.pyt.xml` files
3. **Review in AGP**: Open toolbox in ArcGIS Pro to verify metadata displays correctly
4. **Iterate**: Adjust YAML or XML as needed

### Hybrid Approach

You can combine YAML-generated metadata with manual ArcGIS Pro edits:

1. Generate initial XML from YAML documentation
2. Open in ArcGIS Pro and add additional formatting, images, or links
3. ArcGIS Pro saves edits back to the `.pyt.xml` file
4. Re-running the generator will overwrite manual edits (backup first!)

### Version Control

- **Commit** `.yml` files with documentation sections
- **Optional**: Commit generated `.pyt.xml` files or regenerate on deployment
- **Recommended**: Add `.pyt.xml` to `.gitignore` and regenerate from YAML as needed

## Best Practices

### Writing Good Documentation

1. **Be concise in summaries** - 1-3 sentences maximum
2. **Provide context in usage** - Explain when and why to use the tool
3. **Document all parameters** - Even "obvious" ones need explanation
4. **Include examples** - Show common use cases and patterns
5. **Use consistent terminology** - Match ArcGIS Pro's vocabulary
6. **Add helpful tips** - Mention performance considerations, limitations, or gotchas

### Parameter Documentation

For each parameter, provide:
- **Dialog explanation**: What the user sees/does in the GUI
- **Scripting explanation**: Data type, format, and Python examples

Example:
```yaml
parameter_syntax:
  buffer_distance:
    dialog_explanation: |
      The distance from input features within which buffer zones are created. 
      Must be a positive number.
    scripting_explanation: |
      A numeric value (int or float) representing the buffer distance. 
      Example: 100, 250.5, 1000
```

### Code Samples

- **Show realistic examples** - Use actual file paths and typical workflows
- **Include comments** - Explain what each section does
- **Demonstrate options** - Show both simple and advanced usage
- **Use proper syntax** - Ensure code runs without errors

## Troubleshooting

### Metadata Not Appearing

1. Verify `.pyt.xml` file exists in same directory as `.pyt` file
2. Check filename matches pattern: `yaml_toolbox.{ToolClassName}.pyt.xml`
3. Ensure XML is well-formed (no syntax errors)
4. Close and reopen the toolbox in ArcGIS Pro

### XML Validation Errors

1. Run the metadata generator to ensure proper structure
2. Check for unescaped HTML entities (should use `&lt;` not `<`)
3. Verify all required elements are present (Esri, tool, dataIdInfo)

### Manual Edits Lost

- The generator overwrites existing `.pyt.xml` files
- Backup manually-edited files before regenerating
- Consider maintaining complex edits in ArcGIS Pro after initial generation

## Examples

See the complete examples in:
- [src/config/tools/buffer_analysis.yml](../src/config/tools/buffer_analysis.yml)
- [src/config/tools/clip_features.yml](../src/config/tools/clip_features.yml)

These demonstrate comprehensive documentation with all supported elements.

## References

- [ArcGIS Pro Python Toolbox Documentation](https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/a-quick-tour-of-python-toolboxes.htm)
- [Tool Metadata in ArcGIS Pro](https://pro.arcgis.com/en/pro-app/latest/help/analysis/geoprocessing/basics/geoprocessing-tool-reference.htm)
- YAML Tool Configuration: [docs/yaml-toolbox-configuration-guide.md](yaml-toolbox-configuration-guide.md)

