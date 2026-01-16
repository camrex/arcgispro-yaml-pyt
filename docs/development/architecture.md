# Architecture Guide

## Overview

This project implements a **YAML-driven ArcGIS Pro Python Toolbox framework** with a clean separation between reusable infrastructure and tool-specific business logic.

## Key Concepts

### Framework
The reusable infrastructure layer (`src/framework/`) that provides:
- Dynamic tool class generation from YAML
- Base classes and schemas
- Validation engine
- No domain-specific logic

**Purpose:** Pure machinery for YAML-driven toolbox generation

### Tool
A self-contained, standalone unit (`src/tools/{tool_name}/`) with:
- `tool.yml` - Configuration
- `execute.py` - Implementation
- `test_*.py` - Tests

**Example:** `load_tool_metadata/`

**Use when:** Tool has no related dependencies or shared logic

### Toolset
A collection of related tools (`src/tools/{toolset_name}/`) organized as:
- Multiple tool subdirectories (e.g., `buffer_analysis/`, `clip_features/`)
- Shared `helpers/` directory for common utilities
- Each tool still self-contained with own config/implementation/tests

**Example:** `spatial_analysis/` (contains buffer_analysis, clip_features, shared geoprocessing helpers)

**Use when:** 
- Tools share helper functions or utilities
- Tools are part of an orchestrated workflow
- Related tools benefit from shared domain logic

### Toolbox
An ArcGIS Pro Python Toolbox (`.pyt` file in `src/toolboxes/`) that:
- Registers tools from the tools/ directory
- Has its own `toolbox.yml` configuration
- Can include tools from multiple toolsets
- Same tool can appear in multiple toolboxes

**Example:** `spatial_analysis.pyt`, `utilities.pyt`

**Relationship:** Many-to-many between toolboxes and tools

## Core Design Principles

### 1. Folder-per-Tool Organization
Each tool is a self-contained module with:
- Configuration (tool.yml)
- Implementation (execute.py)
- Tests (test_*.py)
- Optional shared helpers

### 2. Framework/Tools Separation
- **Framework** (`src/framework/`) - Flat, focused infrastructure (4 files)
- **Tools** (`src/tools/`) - Self-contained tool modules
- **Toolboxes** (`src/toolboxes/`) - Multiple .pyt files for organization

### 3. Configuration-Driven
Everything is defined in YAML:
- Tool parameters and their properties
- Validation rules
- Metadata and documentation
- Toolbox structure and tool assignments

### 4. Type-Safe and Auto-Discovered
- Pydantic validates all YAML configurations at load time
- Tests auto-discover all tools and toolboxes (no hardcoded fixtures)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│ ArcGIS Pro                                              │
│ • Discovers .pyt files in toolboxes/                    │
│ • Loads tools from each toolbox independently           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Toolboxes (src/toolboxes/)                          │
│ • spatial_analysis/spatial_analysis.pyt                 │
│ • utilities/utilities.pyt                               │
│ • Each loads its own toolbox.yml                        │
│ • Tools can appear in multiple toolboxes                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Framework Layer (src/framework/) - FLAT STRUCTURE   │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ factory.py - ToolFactory                        │    │
│ │ • Dynamically generates tool classes            │    │
│ │ • Uses type() to create classes at runtime      │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ yaml_tool.py - YAMLTool Base Class              │    │
│ │ • Base for all generated tools                  │    │
│ │ • Implements getParameterInfo(), updateParameters()│
│ │ • Delegates execution to tool's execute.py      │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ schema.py - Pydantic Schemas                    │    │
│ │ • ToolboxConfig, ToolConfig, ParameterConfig    │    │
│ │ • Validates all YAML at load time               │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ validators.py - Validation Engine               │    │
│ │ • YAML structure validation                     │    │
│ │ • Runtime parameter validation                  │    │
│ └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Tools Layer (src/tools/) - FOLDER-PER-TOOL          │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ spatial_analysis/ (Toolset Pattern)             │    │
│ │ ├── buffer_analysis/                            │    │
│ │ │   ├── tool.yml (config)                       │    │
│ │ │   ├── execute.py (implementation)             │    │
│ │ │   └── test_buffer.py (co-located test)        │    │
│ │ ├── clip_features/                              │    │
│ │ │   ├── tool.yml                                │    │
│ │ │   ├── execute.py                              │    │
│ │ │   └── test_clip.py                            │    │
│ │ └── helpers/ (shared utilities)                 │    │
│ │     └── geoprocessing.py                        │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ load_tool_metadata/ (Standalone Tool)           │    │
│ │ ├── tool.yml                                    │    │
│ │ ├── execute.py                                  │    │
│ │ ├── metadata_generator.py (self-contained)     │    │
│ │ └── test_metadata_loader.py                    │    │
│ └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### ToolFactory (framework/factory.py)

Generates tool classes dynamically using `type()`:

```python
def create_tool_class(tool_config: ToolConfig) -> type:
    """Generate a tool class at runtime from YAML config."""
    return type(
        tool_config.name,           # Class name
        (YAMLTool,),                # Base class
        {
            "label": tool_config.label,
            "description": tool_config.description,
            "config": tool_config,
        }
    )
```

### YAMLTool (framework/yaml_tool.py)

Base class that all generated tools inherit from:

- `getParameterInfo()` - Converts YAML parameter configs to arcpy.Parameter objects
- `updateParameters()` - Handles parameter dependencies and validation
- `execute()` - Delegates to implementation function from tool's execute.py

### Configuration Schemas (framework/schema.py)

Pydantic models ensure type safety:

```python
class ParameterConfig(BaseModel):
    name: str
    display_name: str
    data_type: str
    parameter_type: str = "Required"
    direction: str = "Input"
    # ... validation rules, defaults, filters, etc.

class ToolConfig(BaseModel):
    name: str
    label: str
    description: str
    category: str
```python
class ToolConfig(BaseModel):
    name: str
    parameters: List[ParameterConfig]
    implementation_path: str  # e.g., "spatial_analysis/buffer_analysis"
```

### Validation System (framework/validators.py)

All validation logic in one module:
- **Config validation** - YAML structure against Pydantic schemas
- **Runtime validation** - Parameter values during execution
- Checks required fields, data types, ranges
- Applies custom validation rules from YAML

## Tool Execution Flow

1. **User opens ArcGIS Pro** → Pro discovers .pyt files in toolboxes/
2. **Pro imports .pyt file** → spatial_analysis.pyt or utilities.pyt
3. **Load toolbox.yml** → Get list of tools to load for this toolbox
4. **For each tool:**
   - Load tool.yml from tools/{implementation_path}/
   - Validate against Pydantic schema
   - Generate tool class using `ToolFactory`
   - Register as module-level variable
5. **Pro reads tool classes** → Discovers tools via inspection
6. **User runs tool:**
   - Pro calls `getParameterInfo()` → Creates parameter UI
   - User enters values
   - Pro calls `updateParameters()` → Validates/updates parameters
   - Pro calls `execute()` → YAMLTool delegates to tool's execute.py
   - execute.py function does the work using arcpy

## Testing Strategy

### Auto-Discovery (tests/conftest.py)
- **Dynamic fixtures** - No hardcoded tool/toolbox names
- Discovers all tools and toolboxes automatically
- Factory fixtures: `get_toolbox(name)`, `get_tool(path)`
- Add new tool → automatically tested

### Unit Tests (UV Environment)
- **Mock arcpy** - No ArcGIS Pro required
- Fast, isolated testing
- Test framework components independently
- Test business logic without arcpy

### Integration Tests (ArcGIS Pro Environment)
- **Real arcpy** - Run in Pro Python environment
- Test tool execution end-to-end
- Verify arcpy interactions

See [testing.md](testing.md) for details.

## Design Decisions

### Why Folder-per-Tool?

**Problem:** Large monolithic files hard to navigate and test
**Solution:** Each tool is a self-contained module

**Benefits:**
- Clear ownership and boundaries
- Co-located tests with implementation
- Easy to add/remove tools
- Supports toolset pattern (shared helpers)

### Why Flattened Framework?

**Problem:** Over-nested folder structure with 1 file per folder
**Solution:** 4 flat files in framework/

**Benefits:**
- Simpler imports (toolbox.framework.yaml_tool)
- Easier to navigate
- Reduced cognitive overhead
- Still maintains clear separation of concerns

### Why Multiple Toolboxes?

**Problem:** Single monolithic toolbox hard to organize
**Solution:** Multiple .pyt files in toolboxes/ directory

**Benefits:**
- Logical grouping (spatial_analysis, utilities, etc.)
- Same tool can appear in multiple toolboxes
- Each team/domain can have its own toolbox
- Easier to distribute subsets of tools

### Why Auto-Discovery for Tests?

**Problem:** Hardcoded fixtures break when adding tools
**Solution:** Dynamic discovery and factory fixtures

**Benefits:**
- Add tool → automatically tested
- No conftest.py updates needed
- Validates ALL tools consistently
- Scales effortlessly

### Why Pydantic?

- Type-safe validation at load time
- Clear error messages for invalid configs
- Auto-generates documentation from schema
- Modern Python approach (vs. manual validation)

### Why Module-Level Registration?

ArcGIS Pro discovers tools by inspecting module-level variables. Dynamic generation at module load time satisfies this requirement.

## Extension Points

### Adding New Tools

**Option A: Standalone Tool**
1. Create `src/tools/my_tool/` directory
2. Add `tool.yml`, `execute.py`, `test_my_tool.py`
3. Add to toolbox's `toolbox.yml`

**Option B: Tool in Toolset**
1. Create `src/tools/my_toolset/my_tool/` directory
2. Add `tool.yml`, `execute.py`, `test_my_tool.py`
3. Share helpers via `my_toolset/helpers/`
4. Add to toolbox's `toolbox.yml`

Auto-discovery will find and test it automatically.

### Adding New Parameter Types

1. Update `ParameterConfig` schema in `framework/schema.py`
2. Update parameter creation logic in `framework/yaml_tool.py`
3. Add validation logic in `framework/validators.py`

### Adding New Validation Rules

1. Add validation config to `ParameterConfig` schema
2. Implement validation logic in `framework/validators.py`
3. Document in [configuration-guide.md](../configuration-guide.md)

## Future Enhancements

Potential areas for expansion:

- **Tool templates** - Generate YAML from templates
- **Validation library** - Pre-built validation rules
- **Helper library** - Common geoprocessing patterns
- **CLI tools** - Scaffold new tools from command line
- **Web interface** - Visual tool builder
- **Plugin system** - Custom parameter types

## References

- ArcGIS Pro Python Toolbox documentation
- Pydantic documentation
- Python `type()` and metaclasses
- Design patterns: Factory, Template Method

