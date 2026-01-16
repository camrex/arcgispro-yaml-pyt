# Toolbox Configuration Schema (toolbox.yml)

**Version:** 1.0  
**Purpose:** Define a Python Toolbox (.pyt) with its metadata, documentation, and tool references.

## Overview

The `toolbox.yml` file configures a single Python Toolbox. It serves two purposes:

1. **Standalone Mode** - The toolbox directly references tool configurations by path
2. **Catalog Mode** - The catalog manages tool assignments; toolbox.yml defines only metadata

## File Location

**Standalone Mode:**
```
my-toolbox/
  ├─ spatial_analysis.pyt       # Generated Python Toolbox
  ├─ toolbox.yml                 # This configuration file
  └─ tools/                      # Tool configurations
      ├─ buffer_analysis/
      │   └─ tool.yml
      └─ clip_features/
          └─ tool.yml
```

**Catalog Mode:**
- Toolbox.yml lives alongside .pyt file
- Catalog.yml manages which tools are included
- Toolbox.yml defines only metadata (tools section optional/ignored)

## Complete Schema

```yaml
# Toolbox metadata - REQUIRED
toolbox:
  label: string                  # Display name in ArcGIS Pro
  alias: string                  # Internal identifier (alphanumeric, starts with letter)
  description: string            # Short description
  version: string                # Semantic version (default: "1.0.0")

# Documentation metadata - OPTIONAL
# Controls what appears in ArcGIS Pro item description
documentation:
  summary: string                # Purpose/summary (appears first)
  description: string            # Detailed description
  tags: list[string]             # Search tags
  credits: string                # Credits and attribution
  use_limitations: string        # Use limitations and restrictions

# Tool registry - REQUIRED in standalone, OPTIONAL in catalog mode
tools:
  - name: string                 # Tool identifier (matches tool.name in config)
    enabled: boolean             # Whether tool is active (default: true)
    config: string               # Relative path to tool.yml
```

## Field Definitions

### Toolbox Metadata

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `label` | string | ✓ | Display name in ArcGIS Pro | "Spatial Analysis" |
| `alias` | string | ✓ | Internal identifier (alphanumeric only, starts with letter) | "spatialanalysis" |
| `description` | string | ✓ | Short toolbox description | "Spatial analysis tools for buffer and clip operations" |
| `version` | string | | Semantic version (default: "1.0.0") | "1.2.3" |

**Alias Requirements:**
- Must start with a letter (a-z, A-Z)
- Can only contain letters and numbers (no underscores, hyphens, or special characters)
- Used internally by ArcGIS Pro for toolbox identification

### Documentation Metadata

All fields optional. Controls toolbox item description in ArcGIS Pro.

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| `summary` | string | Purpose/summary (1-2 sentences) | Item description, search results |
| `description` | string | Detailed description (multiple paragraphs OK) | Full item page |
| `tags` | list[string] | Search keywords | Pro search, catalog indexing |
| `credits` | string | Attribution, authors, sources | Item metadata |
| `use_limitations` | string | Legal/usage restrictions | Item metadata |

### Tool References

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Tool identifier (must match `tool.name` in referenced config) |
| `enabled` | boolean | | Whether tool is active (default: true) |
| `config` | string | ✓ | Relative path to tool.yml (forward slashes, must end with .yml) |

**Path Rules:**
- Paths are relative to toolbox.yml location
- Use forward slashes (/) even on Windows
- Must end with `.yml`
- Examples: `tools/buffer/tool.yml`, `../../shared-tools/clip/tool.yml`

## Usage Modes

### Standalone Mode (No Catalog)

Toolbox.yml is the source of truth for which tools are included:

```yaml
toolbox:
  label: "Spatial Analysis"
  alias: "spatialanalysis"
  description: "Spatial analysis tools"
  version: "1.0.0"

documentation:
  summary: "Tools for spatial analysis operations"
  description: |
    This toolbox provides essential spatial analysis tools including
    buffer creation and feature clipping operations.
  tags:
    - spatial analysis
    - geoprocessing
    - buffer
    - clip
  credits: "GIS Team"
  use_limitations: "Internal use only"

tools:
  - name: buffer_analysis
    enabled: true
    config: "tools/buffer_analysis/tool.yml"
  
  - name: clip_features
    enabled: true
    config: "tools/clip_features/tool.yml"
  
  - name: experimental_tool
    enabled: false  # Present but disabled
    config: "tools/experimental/tool.yml"
```

### Catalog Mode (Managed)

Catalog.yml controls tool assignments. Toolbox.yml defines only metadata:

```yaml
toolbox:
  label: "Field Analysis Toolbox"
  alias: "fieldanalysis"
  description: "Tools for field data collection"
  version: "2.0.0"

documentation:
  summary: "Field-ready analysis tools"
  description: |
    Curated collection of tools for field data collection workflows.
    Combines tools from multiple sources optimized for offline use.
  tags:
    - field work
    - mobile
    - data collection

# Tools section omitted - managed by catalog.yml
# Or included but ignored by catalog-managed toolbox generator
```

In catalog mode, the catalog.yml defines which tools are in the toolbox:

```yaml
# catalog.yml
toolboxes:
  - id: field-analysis
    name: "Field Analysis Toolbox"
    path: C:/Projects/FieldWork/field_analysis.pyt
    tools:
      - source_id: team-tools
        tool_path: tools/buffer_analysis
      - source_id: local-tools
        tool_path: tools/gps_import
```

## Migration Path

**From Standalone to Catalog:**
1. Keep existing toolbox.yml (metadata still used)
2. Add toolbox to catalog.yml
3. Assign tools via catalog
4. Tools section in toolbox.yml ignored (but can stay for reference)

**From Catalog to Standalone:**
1. Export tool list from catalog
2. Add tools section to toolbox.yml
3. Update config paths to point to actual tool locations
4. Remove from catalog (optional)

## Examples

### Minimal Toolbox (Standalone)

```yaml
toolbox:
  label: "My Tools"
  alias: "mytools"
  description: "Personal GIS tools"

tools:
  - name: buffer
    config: "tools/buffer/tool.yml"
```

### Full Featured Toolbox (Standalone)

```yaml
toolbox:
  label: "Hydrology Analysis Suite"
  alias: "hydroanalysis"
  description: "Comprehensive watershed and stream network analysis tools"
  version: "2.1.0"

documentation:
  summary: |
    Professional-grade hydrology analysis tools for watershed delineation,
    stream network extraction, and flow analysis.
  description: |
    This toolbox provides a complete suite of hydrology analysis tools designed
    for watershed modeling, stream network analysis, and hydrologic processing.
    
    Features:
    - DEM preprocessing and conditioning
    - Flow direction and accumulation
    - Watershed delineation
    - Stream network extraction
    - Pour point analysis
    
    All tools support large raster datasets and include progress indicators.
  tags:
    - hydrology
    - watershed
    - stream network
    - DEM
    - flow analysis
  credits: |
    Developed by: Hydrology Team
    Based on: Standard hydrologic modeling techniques
    Funding: Department of Water Resources
  use_limitations: |
    For professional use only. Results should be validated against field data.
    Not suitable for regulatory purposes without additional validation.

tools:
  - name: fill_sinks
    enabled: true
    config: "tools/preprocessing/fill_sinks/tool.yml"
  
  - name: flow_direction
    enabled: true
    config: "tools/flow/direction/tool.yml"
  
  - name: flow_accumulation
    enabled: true
    config: "tools/flow/accumulation/tool.yml"
  
  - name: watershed_delineation
    enabled: true
    config: "tools/watershed/delineate/tool.yml"
  
  - name: stream_network
    enabled: true
    config: "tools/stream/extract/tool.yml"
  
  - name: pour_point_analysis
    enabled: false  # Beta - not ready for production
    config: "tools/watershed/pour_point/tool.yml"
```

### Catalog-Managed Toolbox (Metadata Only)

```yaml
toolbox:
  label: "Project Analysis Tools"
  alias: "projectanalysis"
  description: "Project-specific analysis tools curated from multiple sources"
  version: "1.0.0"

documentation:
  summary: "Curated toolbox for Project XYZ analysis workflows"
  description: |
    This toolbox contains tools selected from various sources, optimized
    for the Project XYZ workflow. Tool selection and versions are managed
    via the catalog system for consistency across the project team.
  tags:
    - project-xyz
    - curated
    - team-tools

# No tools section - managed via catalog.yml
```

## Validation Rules

1. **Unique Tool Names:** All tool names must be unique within the toolbox
2. **Valid Alias:** Must start with letter, alphanumeric only
3. **Valid Paths:** Config paths must use forward slashes and end with .yml
4. **Tool Name Matching:** tool.name in referenced config must match name in reference
5. **Required Fields:** toolbox.label, toolbox.alias, toolbox.description must be present

## Error Handling

**Missing Tool Config:**
- Log warning
- Skip that tool
- Continue loading other tools
- Don't break toolbox generation

**Disabled Tool:**
- Tool config loaded for validation
- Not registered with ArcGIS Pro
- Remains in toolbox.yml for easy re-enabling

**Invalid Alias:**
- Validation error on load
- Clear message about alias requirements
- Toolbox fails to load (this is critical)

## Integration with Framework

**Loading Process:**
1. Read toolbox.yml
2. Validate schema (Pydantic)
3. Load each enabled tool's config
4. Generate .pyt file with tool classes
5. Register with ArcGIS Pro

**Catalog Integration:**
- Catalog can override tools list
- Toolbox metadata always from toolbox.yml
- Enables same toolbox metadata with different tool sets

## Future Enhancements

**Possible v2.0 features:**
- Tool categories/grouping within toolbox
- Tool ordering/positioning
- Conditional tool loading (Pro version, license requirements)
- Tool dependencies (tool X requires tool Y)
- Custom Python environment per toolbox

## Related Files

- `tool.yml` - Individual tool configuration
- `catalog.yml` - Central catalog of sources and toolboxes
- `{toolbox}.pyt` - Generated Python Toolbox file
- `{toolbox}.pyt.xml` - ArcGIS Pro metadata XML
