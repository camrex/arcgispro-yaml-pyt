# Architecture Guide

## Overview

This project implements a **YAML-driven ArcGIS Pro Python Toolbox framework** with a clean separation between reusable infrastructure and tool-specific business logic.

## Core Design Principles

### 1. Zero Boilerplate
Tools are generated dynamically at runtime from YAML configuration. No wrapper classes needed.

### 2. Framework/Tools Separation
- **Framework** (`toolbox/framework/`) - Portable, reusable infrastructure
- **Tools** (`toolbox/tools/`) - Application-specific business logic

### 3. Configuration-Driven
Everything is defined in YAML:
- Tool parameters and their properties
- Validation rules
- Metadata and documentation
- Toolbox structure

### 4. Type-Safe
Pydantic validates all YAML configurations against schemas at load time.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│ ArcGIS Pro                                              │
│ • Discovers yaml_toolbox.pyt                            │
│ • Reads tool classes from module-level variables        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ yaml_toolbox.pyt (Entry Point)                          │
│ • Loads toolbox.yml                                     │
│ • Uses ToolFactory to generate tool classes             │
│ • Registers tools as module-level variables             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Framework Layer (toolbox/framework/)                    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ factory.py - ToolFactory                        │    │
│ │ • Dynamically generates tool classes            │    │
│ │ • Uses type() to create classes at runtime      │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ base/yaml_tool.py - YAMLTool                    │    │
│ │ • Base class for all generated tools            │    │
│ │ • Implements getParameterInfo(), updateParameters()│
│ │ • Delegates execution to implementation functions │  │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ config/schema.py - Pydantic Schemas             │    │
│ │ • ToolboxConfig, ToolConfig, ParameterConfig    │    │
│ │ • Validates YAML at load time                   │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ validation/ - Validation Engine                 │    │
│ │ • config_validator.py - YAML validation         │    │
│ │ • runtime_validator.py - Parameter validation   │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ metadata/ - Metadata System                     │    │
│ │ • generator.py - YAML → XML metadata            │    │
│ │ • loader_tool.py - In-toolbox metadata loader   │    │
│ └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Tools Layer (toolbox/tools/)                            │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ config/toolbox.yml - Toolbox Registry           │    │
│ │ • Toolbox metadata                              │    │
│ │ • List of tools to load                         │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ config/tools/*.yml - Tool Configurations        │    │
│ │ • buffer_analysis.yml                           │    │
│ │ • clip_features.yml                             │    │
│ │ • One YAML file per tool                        │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ utils/ - Business Logic                          │    │
│ │ • execute_buffer(parameters, messages)          │    │
│ │ • execute_clip(parameters, messages)            │    │
│ │ • Pure Python functions                         │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ helpers/ - Business Helpers                     │    │
│ │ • geoprocessing.py - GP utilities               │    │
│ │ • Domain-specific helper functions              │    │
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

### YAMLTool (framework/base/yaml_tool.py)

Base class that all generated tools inherit from:

- `getParameterInfo()` - Converts YAML parameter configs to arcpy.Parameter objects
- `updateParameters()` - Handles parameter dependencies and validation
- `execute()` - Delegates to implementation function from YAML config

### Configuration Schemas (framework/config/schema.py)

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
    parameters: List[ParameterConfig]
    implementation: str  # e.g., "toolbox.tools.utils.buffer:execute_buffer"
```

### Validation System

**Config Validation** (`framework/validation/config_validator.py`):
- Validates YAML structure against Pydantic schemas
- Checks implementation functions exist
- Ensures no duplicate tool names

**Runtime Validation** (`framework/validation/runtime_validator.py`):
- Validates parameter values during tool execution
- Checks required fields, data types, ranges
- Applies custom validation rules from YAML

### Metadata Generation (framework/metadata/)

Converts YAML documentation to ArcGIS XML metadata:

- Toolbox metadata from `toolbox.yml`
- Tool metadata from individual tool YAMLs
- Supports rich documentation: summary, usage, parameters, code samples, tags, credits

## Tool Execution Flow

1. **User opens ArcGIS Pro** → Pro discovers `yaml_toolbox.pyt`
2. **Pro imports pyt file** → Module-level code executes
3. **Load toolbox.yml** → Get list of tools to load
4. **For each tool:**
   - Load tool YAML (e.g., `buffer_analysis.yml`)
   - Validate against Pydantic schema
   - Generate tool class using `ToolFactory`
   - Register as module-level variable
5. **Pro reads tool classes** → Discovers tools via inspection
6. **User runs tool:**
   - Pro calls `getParameterInfo()` → Creates parameter UI
   - User enters values
   - Pro calls `updateParameters()` → Validates/updates parameters
   - Pro calls `execute()` → YAMLTool delegates to implementation function
   - Implementation function does the work using arcpy

## Testing Strategy

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

### Why Dynamic Tool Generation?

**Problem:** Traditional approach requires ~50 lines of boilerplate per tool
**Solution:** Generate tool classes at runtime from YAML

**Benefits:**
- One YAML file per tool (no Python wrapper needed)
- Changes to tool definition don't require code changes
- Easy to add/modify tools
- Clear separation of configuration and implementation

### Why Separate Framework and Tools?

**Portability:** Framework can be copied to start a new YAML toolbox project
**Maintainability:** Business logic changes don't affect framework
**Testability:** Framework and tools can be tested independently

### Why Pydantic?

- Type-safe validation at load time
- Clear error messages for invalid configs
- Auto-generates documentation from schema
- Modern Python approach (vs. manual validation)

### Why Module-Level Registration?

ArcGIS Pro discovers tools by inspecting module-level variables. Dynamic generation at module load time satisfies this requirement.

## Extension Points

### Adding New Parameter Types

1. Update `ParameterConfig` schema in `framework/config/schema.py`
2. Update parameter creation logic in `base/yaml_tool.py`
3. Add validation logic in `validation/runtime_validator.py`

### Adding New Validation Rules

1. Add validation config to `ParameterConfig` schema
2. Implement validation logic in `validation/runtime_validator.py`
3. Document in [configuration-guide.md](../configuration-guide.md)

### Custom Metadata Elements

1. Update schema in `framework/config/schema.py`
2. Update XML generation in `metadata/generator.py`
3. Document in [metadata-guide.md](../metadata-guide.md)

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
