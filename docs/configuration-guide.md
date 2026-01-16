# YAML-Based ArcGIS Pro Toolbox Configuration Guide

**Complete guide to building maintainable, modular ArcGIS Pro Python Toolboxes using YAML configuration with minimal boilerplate.**

## Table of Contents

- [Overview](#overview)
- [Why YAML for Toolbox Definition?](#why-yaml-for-toolbox-definition)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Configuration Files](#configuration-files)
- [Pydantic Schemas](#pydantic-schemas)
- [Auto-Loading Container](#auto-loading-container)
- [Base Tool Class](#base-tool-class)
- [Tool Implementation](#tool-implementation)
- [Complete Workflow Example](#complete-workflow-example)
- [Benefits](#benefits)
- [Validation](#validation)
- [Testing](#testing)
- [Best Practices](#best-practices)

---

## Overview

Traditional ArcGIS Pro toolbox development involves significant boilerplate code in `getParameterInfo()` methods. This YAML-based approach reduces tool wrappers from 50+ lines to ~10 lines while improving maintainability, testability, and team collaboration.

### Key Features

- ✅ **Declarative Configuration** - Define tools in YAML, not Python
- ✅ **Modular Design** - One YAML file per tool
- ✅ **Minimal Boilerplate** - Tool wrappers reduced to ~10 lines
- ✅ **Type Safety** - Pydantic validation for all configurations
- ✅ **Separation of Concerns** - YAML → Container → Tools → Utils → Helpers
- ✅ **Version Control Friendly** - Small, focused files with clear diffs
- ✅ **Easy to Test** - Utils as pure functions, helpers isolated
- ✅ **Self-Documenting** - YAML serves as living documentation

---

## Why YAML for Toolbox Definition?

### Problems with Traditional Approach

**Before (Traditional):**
```python
def getParameterInfo(self):
    """50+ lines of boilerplate per tool."""
    params = []
    
    param = arcpy.Parameter(
        displayName="Input Features",
        name="input_features",
        datatype="GPFeatureLayer",
        parameterType="Required",
        direction="Input"
    )
    param.description = "The input features"
    params.append(param)
    
    # Repeat 5-10 times per tool...
    return params
```

**Issues:**
- 🔴 Repetitive boilerplate code
- 🔴 Hard to review in version control
- 🔴 Difficult to validate consistency
- 🔴 Mixes configuration with implementation
- 🔴 Testing requires ArcGIS Pro
- 🔴 Merge conflicts in large files

### Solution with YAML

**After (YAML):**
```yaml
# config/tools/buffer.yml
parameters:
  - name: input_features
    displayName: "Input Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    description: "The input features to buffer"
```

**Benefits:**
- ✅ Clear, declarative configuration
- ✅ Easy to diff and review
- ✅ Type-safe with Pydantic
- ✅ Separates what from how
- ✅ Tools testable without ArcGIS
- ✅ Small, focused files

---

## Architecture

The YAML-based architecture follows a clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────┐
│ toolbox.yml (Registry + Documentation)                      │
│ - Toolbox metadata                                           │
│ - Toolbox-level documentation                                │
│ - Tool registry (list of tools with enabled flags)          │
└─────────────────┬────────────────────────────────────────────┘
                  │
    ┌─────────────┴──────────────────┐
    │                                │
    ▼                                ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ buffer_analysis  │     │ clip_features    │     │ load_tool_       │
│ .yml             │     │ .yml             │ ... │ metadata.yml     │
│ (Individual)     │     │ (Individual)     │     │ (Individual)     │
│ - Tool metadata  │     │ - Tool metadata  │     │ - Tool metadata  │
│ - Parameters     │     │ - Parameters     │     │ - Parameters     │
│   (with index)   │     │   (with index)   │     │   (with index)   │
│ - executeFunction│     │ - executeFunction│     │ - executeFunction│
│ - Documentation  │     │ - Documentation  │     │ - Documentation  │
│ - Validation     │     │ - Validation     │     │ - Validation     │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                         │
         └────────────┬───────────┴─────────────────────────┘
                      │ Loaded by
                      ▼
┌──────────────────────────────────────────────────────────────┐
│ yaml_toolbox.pyt + factory.py (Dynamic container)           │
│ - Loads toolbox.yml registry at module import               │
│ - Loads individual tool configs via factory                 │
│ - Validates all configs with Pydantic                       │
│ - Dynamically creates tool classes at runtime               │
│ - Auto-registers enabled tools only                         │
│ - ~50 lines combined, rarely changes                        │
└─────────────────────────┬────────────────────────────────────┘
                          │ Creates dynamically
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Tool Classes (Generated by Factory - NO manual wrappers!)   │
│ - Inherit from YAMLTool base class                          │
│ - Created dynamically from YAML + execute function          │
│ - getParameterInfo() built from YAML parameters             │
│ - execute() delegates to configured utils function          │
└─────────────────────────┬────────────────────────────────────┘
                          │ Calls
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ tools/{tool_name}/execute.py (Business logic)               │
│ - Each tool has its own execute function                    │
│ - Extract parameters by index from parameters list          │
│ - Actual geoprocessing code                                 │
│ - Can use shared helpers from toolset                       │
└─────────────────────────┬────────────────────────────────────┘
                          │ Can use
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ tools/{toolset}/helpers/*.py (Shared utilities)             │
│ - validate_feature_class()                                  │
│ - check_spatial_reference()                                 │
│ - get_feature_count()                                       │
│ - Error handling utilities                                  │
└──────────────────────────────────────────────────────────────┘

                          │ Can generate
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ *.pyt.xml (Metadata files - generated from YAML docs)       │
│ - Generated by metadata loader utility                      │
│ - Displays in ArcGIS Pro tool help                          │
│ - Created from documentation sections in YAML               │
└──────────────────────────────────────────────────────────────┘
```

### Flow of Execution

1. **ArcGIS Pro** opens the `.pyt` file
2. **.pyt module import** triggers factory to load `toolbox.yml` registry
3. **Factory** iterates over enabled tools in registry
4. **Factory** loads each tool's individual YAML configuration
5. **Pydantic** validates all configurations on load (fail fast)
6. **Factory** imports execute function from `implementation.executeFunction`
7. **Factory** dynamically creates tool class inheriting from `YAMLTool`
8. **Tool classes** added to module globals for ArcGIS Pro discovery
9. **User runs tool** in ArcGIS Pro
10. **YAMLTool.getParameterInfo()** builds UI from YAML parameters (sorted by index)
11. **Tool.execute()** extracts parameters by index and calls utils function
12. **Utils function** performs geoprocessing using helpers
13. **Optional**: Run metadata loader to generate .pyt.xml from YAML docs

**Key Innovation:** No manual tool wrapper classes - factory generates them dynamically!

---

## Project Structure

Complete folder structure for YAML-based toolbox:

```
my-arcgis-src/
├── src/
│   ├── yaml_toolbox.pyt         # Legacy single-toolbox entry (optional)
│   │
│   ├── framework/                # Framework code (flat structure) ⭐
│   │   ├── factory.py           # Tool factory for dynamic loading
│   │   ├── yaml_tool.py         # YAMLTool base class
│   │   ├── schema.py            # Pydantic validation schemas
│   │   └── validators.py        # Config & runtime validation
│   │
│   ├── toolboxes/                # Multiple toolbox .pyt files ⭐
│   │   ├── spatial_analysis/
│   │   │   ├── spatial_analysis.pyt
│   │   │   └── toolbox.yml      # Toolbox config + tool list
│   │   └── utilities/
│   │       ├── utilities.pyt
│   │       └── toolbox.yml
│   │
│   └── tools/                    # Folder-per-tool structure ⭐
│       ├── spatial_analysis/     # Toolset (related tools)
│       │   ├── buffer_analysis/
│       │   │   ├── tool.yml
│       │   │   ├── execute.py
│       │   │   └── test_buffer.py
│       │   ├── clip_features/
│       │   │   ├── tool.yml
│       │   │   ├── execute.py
│       │   │   └── test_clip.py
│       │   └── helpers/          # Shared utilities
│       │       └── geoprocessing.py
│       └── load_tool_metadata/   # Standalone tool
│           ├── tool.yml
│           ├── execute.py
│           ├── metadata_generator.py  # Self-contained
│           └── test_metadata_loader.py
│
├── tests/                        # Framework tests (auto-discovery) ⭐
│   ├── conftest.py              # Dynamic fixtures (no hardcoded tools)
│   ├── test_discovery.py        # Validates all discovered tools
│   ├── test_config_validation.py
│   └── test_yaml_loading.py
│
├── scripts/                      # Development scripts
│   └── validate_config.py
│
├── docs/                         # Documentation
│   ├── configuration-guide.md
│   ├── metadata-guide.md
│   └── development/
│       ├── architecture.md
│       ├── setup.md
│       └── testing.md
│
├── pyproject.toml                # Project dependencies
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

---

## Configuration Files

### Toolbox Registry

**src/toolboxes/{toolbox_name}/toolbox.yml** - Toolbox metadata, tool registry, and documentation:

```yaml
# Toolbox metadata
toolbox:
  label: "Spatial Analysis Toolbox"
  alias: "spatialanalysistoolbox"
  description: "YAML-configured spatial analysis tools"
  version: "1.0.0"

# Toolbox documentation (appears in ArcGIS Pro metadata)
documentation:
  summary: |
    A collection of spatial analysis tools configured using YAML. 
    Tools are dynamically generated at runtime from configuration files.
  description: |
    This toolbox provides a modern approach to ArcGIS Pro Python Toolbox development 
    by using YAML configuration files to define tools instead of writing repetitive 
    wrapper classes. Tools are dynamically generated at runtime, allowing developers 
    to focus on business logic while the framework handles parameter management, 
    validation, and ArcGIS Pro integration.
  tags:
    - yaml
    - configuration
    - geoprocessing
    - analysis
  credits: |
    Developed as a proof of concept for YAML-based toolbox development.
  use_limitations: |
    This toolbox is provided as-is for demonstration and educational purposes.

# Tool registry - list of tools to include
tools:
  - name: buffer_analysis
    enabled: true
    config: "tools/buffer_analysis.yml"
  
  - name: clip_features
    enabled: true
    implementation_path: "spatial_analysis/clip_features"
  
  - name: load_tool_metadata
    enabled: true
    implementation_path: "load_tool_metadata"
```

**Key Features:**
- ✅ Central registry of all tools
- ✅ Enable/disable tools without code changes
- ✅ `implementation_path` points to folder in tools/
- ✅ Version tracking
- ✅ Toolbox-level documentation metadata
- ✅ Clear tool inventory

### Individual Tool Configuration

**src/tools/spatial_analysis/buffer_analysis/tool.yml** - Complete tool definition:

```yaml
# Tool metadata
tool:
  name: buffer_analysis
  label: "Buffer Analysis"
  description: "Create buffer polygons around input features"
  category: "Analysis"
  canRunInBackground: true

# Python implementation (execute function is in execute.py in same folder)
implementation:
  module: "execute"  # Relative import from tool folder

# Parameter definitions
parameters:
  - name: input_features
    index: 0  # Parameter position (0-based)
    displayName: "Input Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    description: "The input features to buffer"
  
  - name: buffer_distance
    index: 1
    displayName: "Buffer Distance"
    datatype: GPDouble
    parameterType: Required
    direction: Input
    defaultValue: 100
    description: "The distance to buffer"
    filter:
      type: Range
      min: 0
      max: 10000
    validation:  # Runtime validation rules
      - type: greater_than
        value: 0
        message: "Buffer distance must be positive"
  
  - name: buffer_units
    index: 2
    displayName: "Buffer Units"
    datatype: GPString
    parameterType: Required
    direction: Input
    defaultValue: "meters"
    description: "The unit of measurement"
    filter:
      type: ValueList
      values:
        - meters
        - feet
        - kilometers
        - miles
    validation:
      - type: one_of
        values: ["meters", "feet", "kilometers", "miles"]
        message: "Invalid unit of measurement"
  
  - name: dissolve_output
    index: 3
    displayName: "Dissolve Output"
    datatype: GPBoolean
    parameterType: Optional
    direction: Input
    defaultValue: true
    description: "Dissolve overlapping buffers"
  
  - name: output_features
    index: 4
    displayName: "Output Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Output
    description: "The output buffer features"

# Documentation metadata for ArcGIS Pro (optional)
documentation:
  summary: |
    Creates buffer polygons around input features at a specified distance.
  usage: |
    The Buffer Analysis tool creates buffer polygons at a specified distance 
    around input point, line, or polygon features.
  tags:
    - buffer
    - proximity
    - analysis
  credits: |
    Example tool demonstrating YAML-based configuration.
  use_limitations: |
    Provided for educational and demonstration purposes.
  parameter_syntax:
    input_features:
      dialog_explanation: |
        The input point, line, or polygon features to be buffered.
      scripting_explanation: |
        A string representing the path to the feature class or layer.
  code_samples:
    - title: "Basic Buffer"
      description: "Create a 100-meter buffer"
      code: |
        import arcpy
        arcpy.yamlanalysistoolbox.BufferAnalysis(
            "cities.shp", 100, "meters", True, "buffers.shp"
        )
```

**src/tools/config/tools/clip_features.yml** - Simpler example:

```yaml
tool:
  name: clip_features
  label: "Clip Features"
  description: "Clip features to a boundary"
  category: "Analysis"
  canRunInBackground: true

implementation:
  executeFunction: "toolbox.tools.utils.clip.execute_clip"

parameters:
  - name: input_features
    index: 0
    displayName: "Input Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    description: "Features to clip"
  
  - name: clip_features
    index: 1
    displayName: "Clip Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    description: "Boundary for clipping"
  
  - name: output_features
    index: 2
    displayName: "Output Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Output
    description: "Clipped output features"

documentation:
  summary: |
    Extracts input features that overlap the clip features boundary.
  usage: |
    The Clip Features tool operates like a cookie cutter.
  tags:
    - clip
    - extract
    - analysis
```

**Key Features:**
- ✅ Each parameter has an explicit `index` field (0-based)
- ✅ `implementation.executeFunction` points to the business logic
- ✅ Optional `validation` rules for runtime checks
- ✅ Optional `documentation` section for ArcGIS Pro metadata
- ✅ Supports parameter filters (Range, ValueList, File)
- ✅ No parameter mapping needed - use index directly

---

## Pydantic Schemas

Type-safe validation for all YAML configurations:

**src/framework/schema.py**:

```python
"""Pydantic schemas for YAML configuration validation."""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ToolboxMetadata(BaseModel):
    """Toolbox-level metadata."""
    label: str = Field(..., description="Display name of the toolbox")
    alias: str = Field(..., description="Internal alias (alphanumeric, start with letter)")
    description: str = Field(..., description="Toolbox description")
    version: str = Field(default="1.0.0", description="Toolbox version")
    
    @field_validator("alias")
    @classmethod
    def validate_alias(cls, v: str) -> str:
        """Validate alias meets ArcGIS Pro requirements."""
        if not v or not v[0].isalpha() or not v.isalnum():
            raise ValueError("Alias must start with letter and be alphanumeric")
        return v


class ToolboxDocumentation(BaseModel):
    """Toolbox-level documentation metadata for ArcGIS Pro."""
    summary: str = Field(..., description="Purpose/summary of the toolbox")
    description: str = Field(..., description="Detailed description")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    credits: str = Field(default="", description="Credits and attribution")
    use_limitations: str = Field(default="", description="Use limitations")


class ToolReference(BaseModel):
    """Reference to a tool configuration file."""
    name: str = Field(..., description="Tool identifier (must match tool.name)")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    config: str = Field(..., description="Path to tool YAML (relative to config/)")
    
    @field_validator("config")
    @classmethod
    def validate_config_path(cls, v: str) -> str:
        """Ensure config path uses forward slashes and .yml extension."""
        if not v.endswith(".yml"):
            raise ValueError(f"Config path must end with .yml: {v}")
        return v.replace("\\", "/")


class ToolboxConfig(BaseModel):
    """Complete toolbox configuration (toolbox.yml)."""
    toolbox: ToolboxMetadata
    tools: list[ToolReference] = Field(..., description="List of tools")
    documentation: ToolboxDocumentation | None = Field(
        default=None, description="Optional documentation metadata"
    )
    
    @field_validator("tools")
    @classmethod
    def validate_unique_names(cls, v: list[ToolReference]) -> list[ToolReference]:
        """Ensure tool names are unique."""
        names = [tool.name for tool in v]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate tool names found: {names}")
        return v


class FilterConfig(BaseModel):
    """Parameter filter configuration."""
    type: Literal["Range", "ValueList", "File"]
    min: float | None = None
    max: float | None = None
    values: list[str | int | float] | None = None
    fileFilters: list[str] | None = None


class ValidationCheck(BaseModel):
    """Individual validation check for runtime validation."""
    type: Literal[
        "greater_than", "less_than", "min_value", "max_value", 
        "one_of", "not_empty", "regex"
    ]
    value: float | int | str | None = None
    values: list[str | int | float] | None = None  # For one_of
    pattern: str | None = None  # For regex
    message: str | None = None


class ParameterConfig(BaseModel):
    """Individual parameter definition."""
    name: str = Field(..., description="Parameter identifier")
    displayName: str = Field(..., description="Display name in tool dialog")
    datatype: str = Field(..., description="ArcGIS datatype (e.g., GPFeatureLayer)")
    parameterType: Literal["Required", "Optional", "Derived"]
    direction: Literal["Input", "Output"]
    index: int = Field(..., description="Parameter position (0-based)", ge=0)
    description: str = Field(default="", description="Parameter description")
    defaultValue: str | int | float | bool | None = None
    filter: FilterConfig | None = None
    columns: list[list[str]] | None = None  # For GPValueTable
    validation: list[ValidationCheck] | None = Field(
        None, description="Runtime validation checks"
    )


class ParameterSyntax(BaseModel):
    """Parameter-level syntax documentation."""
    dialog_explanation: str = Field(..., description="Dialog/GUI usage")
    scripting_explanation: str = Field(..., description="Python usage")


class CodeSample(BaseModel):
    """Code sample documentation."""
    title: str = Field(..., description="Code sample title")
    description: str = Field(..., description="What the code does")
    code: str = Field(..., description="Actual code content")


class ToolDocumentation(BaseModel):
    """Tool documentation metadata for ArcGIS Pro XML."""
    summary: str = Field(..., description="Abstract/summary")
    usage: str = Field(..., description="Usage information and best practices")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    credits: str = Field(default="", description="Credits")
    use_limitations: str = Field(default="", description="Use limitations")
    parameter_syntax: dict[str, ParameterSyntax] = Field(
        default_factory=dict, description="Parameter docs by name"
    )
    code_samples: list[CodeSample] = Field(
        default_factory=list, description="Example code"
    )


class ImplementationConfig(BaseModel):
    """Tool implementation details."""
    executeFunction: str = Field(
        ..., description="Fully qualified path to execute function"
    )


class ToolMetadata(BaseModel):
    """Tool-level metadata."""
    name: str = Field(..., description="Tool identifier (must match filename)")
    label: str = Field(..., description="Display name")
    description: str = Field(..., description="Tool description")
    category: str = Field(default="General", description="Tool category")
    canRunInBackground: bool = Field(default=False, description="Background support")


class ToolConfig(BaseModel):
    """Individual tool configuration (tools/*.yml)."""
    tool: ToolMetadata
    implementation: ImplementationConfig
    parameters: list[ParameterConfig]
    documentation: ToolDocumentation | None = Field(
        default=None, description="Optional documentation metadata"
    )
    
    @model_validator(mode="after")
    def validate_parameter_indices(self) -> "ToolConfig":
        """Ensure parameter indices are unique, start at 0, with no gaps."""
        if not self.parameters:
            return self
        
        indices = [p.index for p in self.parameters]
        
        # Check for duplicates
        if len(indices) != len(set(indices)):
            duplicates = [idx for idx in set(indices) if indices.count(idx) > 1]
            raise ValueError(f"Duplicate parameter indices: {duplicates}")
        
        # Check for 0-based sequence with no gaps
        expected = set(range(len(self.parameters)))
        actual = set(indices)
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            msg = []
            if missing:
                msg.append(f"Missing indices: {sorted(missing)}")
            if extra:
                msg.append(f"Invalid indices: {sorted(extra)}")
            raise ValueError("; ".join(msg))
        
        return self


def load_toolbox_config(config_dir: Path) -> ToolboxConfig:
    """Load and validate toolbox configuration."""
    import yaml
    
    toolbox_path = config_dir / "toolbox.yml"
    with open(toolbox_path) as f:
        data = yaml.safe_load(f)
    
    config = ToolboxConfig(**data)
    
    # Validate that all referenced tool configs exist
    for tool_ref in config.tools:
        tool_config_path = config_dir / tool_ref.config
        if not tool_config_path.exists():
            raise FileNotFoundError(
                f"Tool config not found: {tool_config_path}"
            )
    
    return config


def load_tool_config(config_path: Path) -> ToolConfig:
    """Load and validate individual tool configuration."""
    import yaml
    
    with open(config_path) as f:
        data = yaml.safe_load(f)
    
    config = ToolConfig(**data)
    
    # Validate tool name matches filename
    expected_name = config_path.stem
    if config.tool.name != expected_name:
        raise ValueError(
            f"Tool name '{config.tool.name}' doesn't match filename '{expected_name}'"
        )
    
    return config
```

**Key Validation Features:**
- ✅ Validates alias format (alphanumeric, starts with letter)
- ✅ Ensures unique tool names in toolbox registry
- ✅ Validates parameter indices are 0-based with no gaps or duplicates
- ✅ Validates tool name matches YAML filename
- ✅ Supports optional documentation and validation sections
- ✅ Type-safe with Pydantic v2 syntax

---

## Auto-Loading Container

The `.pyt` file becomes a generic, YAML-driven container using a factory pattern:

**src/yaml_toolbox.pyt**:

```python
"""ArcGIS Pro Python Toolbox - Auto-loaded from YAML."""

import importlib
import sys
from pathlib import Path

# Add toolbox to path
toolbox_path = Path(__file__).parent
sys.path.insert(0, str(toolbox_path.parent))

# Import after path setup
from src.framework.factory import load_and_register_tools

# Load and register all tool classes at module level
# (ArcGIS Pro needs them discoverable as module-level names)
try:
    _toolbox_config, _tool_classes = load_and_register_tools(
        toolbox_path / "tools" / "config"
    )
    
    # Add tool classes to module globals so ArcGIS Pro can discover them
    for tool_class in _tool_classes:
        globals()[tool_class.__name__] = tool_class
        
except Exception as e:
    print(f"ERROR loading toolbox: {e}")
    import traceback
    traceback.print_exc()
    _toolbox_config = None
    _tool_classes = []


class Toolbox:
    """YAML-Configured Toolbox - Auto-loads all tools."""
    
    def __init__(self):
        """Initialize the toolbox with YAML configuration."""
        if _toolbox_config is None:
            raise RuntimeError("Failed to load toolbox configuration")
        
        # Set toolbox properties from YAML
        self.label = _toolbox_config.toolbox.label
        self.alias = _toolbox_config.toolbox.alias
        self.description = _toolbox_config.toolbox.description
        
        # Reference the pre-loaded tool classes
        self.tools = _tool_classes
        
        print(f"Toolbox loaded: {len(self.tools)} tools")
```

**src/framework/factory.py** - Tool factory for dynamic class generation:

```python
"""Dynamic tool class factory."""

import importlib
from pathlib import Path

from src.framework.base.yaml_tool import YAMLTool
from src.framework.config.schema import load_tool_config, load_toolbox_config


def create_tool_class(tool_name: str, config_path: Path, execute_func):
    """
    Dynamically create a tool class from YAML config.
    
    Args:
        tool_name: Name of the tool (must match YAML filename)
        config_path: Path to the tool's YAML configuration
        execute_func: The execute function to call when tool runs
        
    Returns:
        Dynamically created tool class
    """
    
    class DynamicTool(YAMLTool):
        """Dynamically generated tool class."""
        
        def __init__(self):
            super().__init__(tool_name)
            self._execute_func = execute_func
            self._config_path = config_path
        
        def execute(self, parameters, messages):
            """Execute tool - delegates to configured function."""
            try:
                execute_func(parameters, messages, self.config)
            except Exception as e:
                messages.addErrorMessage(
                    f"Error in {self.label}: {e}"
                )
                raise
    
    # Set class name and metadata
    class_name = f"{tool_name.title().replace('_', '')}Tool"
    DynamicTool.__name__ = class_name
    DynamicTool.__qualname__ = class_name
    DynamicTool.__module__ = "toolbox.factory"
    
    return DynamicTool


def load_and_register_tools(config_dir: Path):
    """
    Load all enabled tools from YAML configuration.
    
    Args:
        config_dir: Path to config directory containing toolbox.yml
        
    Returns:
        Tuple of (toolbox_config, list of tool classes)
    """
    tool_classes = []
    
    # Load toolbox configuration
    toolbox_config = load_toolbox_config(config_dir)
    
    for tool_ref in toolbox_config.tools:
        if not tool_ref.enabled:
            continue
        
        try:
            # Load individual tool config
            tool_config_path = config_dir / tool_ref.config
            tool_config = load_tool_config(tool_config_path)
            
            # Import execute function dynamically
            func_path = tool_config.implementation.executeFunction
            module_path, func_name = func_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            execute_func = getattr(module, func_name)
            
            # Create tool class
            tool_class = create_tool_class(
                tool_config.tool.name, tool_config_path, execute_func
            )
            tool_classes.append(tool_class)
            
            print(f"✓ Loaded: {tool_ref.name}")
            
        except Exception as e:
            print(f"Warning: Could not load tool {tool_ref.name}: {e}")
    
    return toolbox_config, tool_classes
```

**Key Features:**
- ✅ ~50 lines total (never needs modification)
- ✅ Auto-discovers and loads enabled tools via factory
- ✅ Tools created dynamically at module load time
- ✅ Validates on load with Pydantic
- ✅ Clear error messages with full stack traces
- ✅ No manual tool class imports needed

---

## Base Tool Class

All tools inherit from `YAMLTool` which handles YAML loading and parameter generation:

**src/framework/yaml_tool.py**:

```python
"""Base class for YAML-configured tools."""

from pathlib import Path

import arcpy

from src.framework.config.schema import ToolConfig, load_tool_config


class YAMLTool:
    """Base class for tools configured via YAML."""
    
    def __init__(self, tool_name: str):
        """
        Initialize tool from YAML configuration.
        
        Args:
            tool_name: Name of the tool (must match YAML filename without extension)
        """
        self.tool_name = tool_name
        
        # Load tool configuration from individual YAML file
        toolbox_path = Path(__file__).parent.parent.parent  # Go up to src/
        config_path = toolbox_path / "tools" / "config" / "tools" / f"{tool_name}.yml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Tool config not found: {config_path}")
        
        # Load and validate config
        self.config: ToolConfig = load_tool_config(config_path)
        
        # Set tool properties from YAML
        self.label = self.config.tool.label
        self.description = self.config.tool.description
        self.category = self.config.tool.category
        self.canRunInBackground = self.config.tool.canRunInBackground
    
    def getParameterInfo(self):
        """Build parameters from YAML configuration."""
        # Sort parameters by index to ensure correct order
        sorted_params = sorted(self.config.parameters, key=lambda p: p.index)
        
        parameters = []
        
        for param_config in sorted_params:
            # Create parameter
            param = arcpy.Parameter(
                name=param_config.name,
                displayName=param_config.displayName,
                datatype=param_config.datatype,
                parameterType=param_config.parameterType,
                direction=param_config.direction
            )
            
            # Set default value
            if param_config.defaultValue is not None:
                param.value = param_config.defaultValue
            
            # Set filter if provided
            if param_config.filter:
                filter_config = param_config.filter
                if filter_config.type == "Range":
                    param.filter.type = "Range"
                    param.filter.list = [filter_config.min, filter_config.max]
                elif filter_config.type == "ValueList":
                    param.filter.type = "ValueList"
                    param.filter.list = filter_config.values
                elif filter_config.type == "File":
                    param.filter.list = filter_config.fileFilters
            
            # Set columns for ValueTable
            if param_config.columns:
                param.columns = param_config.columns
            
            parameters.append(param)
        
        return parameters
    
    def execute(self, parameters, messages):
        """Execute tool - must be overridden by subclasses."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
```

**Key Features:**
- ✅ Loads configuration from YAML automatically
- ✅ Builds `getParameterInfo()` from YAML parameters
- ✅ Sorts parameters by index field
- ✅ Handles all parameter types, filters, and defaults
- ✅ Validates configuration with Pydantic on load
- ✅ Subclasses only need to implement `execute()`

---

## Tool Implementation

### No Manual Tool Wrappers Needed!

### Business Logic Implementation

Each tool has its own `execute.py` file with the actual implementation.

**src/tools/spatial_analysis/buffer_analysis/execute.py**:

```python
"""Buffer analysis business logic."""

import arcpy
from pathlib import Path

# Import shared helpers from toolset
from ..helpers.geoprocessing import validate_feature_class


def execute_buffer(parameters, messages):
    """
    Execute buffer analysis.
    
    Args:
        parameters: ArcGIS tool parameters (list)
        messages: ArcGIS messages object
    """
    try:
        # Extract parameters by index (defined in tool.yml)
        input_features = parameters[0].valueAsText
        buffer_distance = parameters[1].value
        buffer_units = parameters[2].valueAsText
        dissolve = parameters[3].value
        output_features = parameters[4].valueAsText
        
        # Validate inputs using shared helper
        validate_feature_class(input_features, messages)
        
        messages.addMessage(
            f"Buffering with distance: {buffer_distance} {buffer_units}"
        )
        
        # Execute geoprocessing
        arcpy.analysis.Buffer(
            in_features=input_features,
            out_feature_class=output_features,
            buffer_distance_or_field=f"{buffer_distance} {buffer_units}",
            dissolve_option="ALL" if dissolve else "NONE"
        )
        
        # Get result info
        result_count = int(arcpy.management.GetCount(output_features)[0])
        messages.addMessage(f"Created {result_count} buffer features")
        messages.addMessage("Buffer analysis complete!")
        
    except Exception as e:
        messages.addErrorMessage(f"Error in buffer analysis: {str(e)}")
        raise
```

**Key Innovation:** Build a parameter map from the config to access parameters by **name** instead of raw index numbers! This makes the code more readable and maintainable.

### Tool Complexity: From Simple to Complex

**Important Note:** The `buffer` and `clip` examples shown here are intentionally simple to demonstrate the framework. In practice, your tools can be **as simple or complex as your needs require**.

**The framework handles any level of complexity:**

**Simple Tool** (like the examples above):
```python
def execute_simple_tool(parameters, messages, config):
    param_map = {p.name: p.index for p in config.parameters}
    input_fc = parameters[param_map["input"]].valueAsText
    output_fc = parameters[param_map["output"]].valueAsText
    
    # Single geoprocessing operation
    arcpy.analysis.Buffer(input_fc, output_fc, "100 meters")
```

**Complex Orchestrated Workflow** (multiple utils, helpers, business logic):
```python
def execute_complex_analysis(parameters, messages, config):
    """
    Complex multi-step spatial analysis workflow.
    Could involve multiple utilities, validation, data preparation, 
    analysis steps, and post-processing.
    """
    param_map = {p.name: p.index for p in config.parameters}
    
    # Step 1: Extract and validate all parameters
    from .validation_utils import validate_all_inputs
    inputs = validate_all_inputs(parameters, param_map, messages)
    
    # Step 2: Data preparation
    from .prep_utils import prepare_datasets, check_coordinate_systems
    prepared_data = prepare_datasets(inputs, messages)
    check_coordinate_systems(prepared_data, messages)
    
    # Step 3: Run multiple analysis steps
    from .analysis_utils import (
        run_proximity_analysis,
        run_overlay_analysis, 
        calculate_statistics
    )
    proximity_results = run_proximity_analysis(prepared_data, messages)
    overlay_results = run_overlay_analysis(proximity_results, messages)
    stats = calculate_statistics(overlay_results, messages)
    
    # Step 4: Post-processing and output
    from .output_utils import format_results, generate_report
    final_output = format_results(overlay_results, stats, messages)
    generate_report(final_output, inputs["output_path"], messages)
    
    messages.addMessage("Complex analysis workflow complete!")
```

**The Key Benefit:** 

Regardless of complexity, you only write **one YAML file** and **one utils function** (which can call as many helper functions/modules as needed). The framework eliminates the boilerplate:

- ❌ No manual `getParameterInfo()` boilerplate (50+ lines per tool)
- ❌ No manual tool class wrappers
- ❌ No manual parameter validation code in the tool class
- ✅ Just YAML config + business logic

**Focus on what matters:** Your tool's business logic, not ArcGIS Pro integration code.

**Examples of complex tools you could build:**
- Multi-step spatial analysis workflows
- Data quality assessment with multiple validation rules  
- Automated map production pipelines
- Complex overlay analysis with multiple inputs
- Data transformation and ETL processes
- Batch processing with parallel execution
- Machine learning model integration
- Custom reporting and visualization

The framework scales with your needs - from simple single-operation tools to sophisticated multi-step workflows.

**src/tools/utils/clip.py**:

```python
"""Clip features business logic."""

import arcpy

from src.framework.config.schema import ToolConfig
from src.tools.helpers.geoprocessing import validate_feature_class


def execute_clip(parameters, messages, config: ToolConfig):
    """
    Execute clip operation.
    
    Args:
        parameters: ArcGIS tool parameters (list)
        messages: ArcGIS messages object
        config: Tool configuration from YAML
    """
    try:
        # Build parameter map for semantic access
        param_map = {p.name: p.index for p in config.parameters}
        
        # Extract parameters by name
        input_features = parameters[param_map["input_features"]].valueAsText
        clip_features = parameters[param_map["clip_features"]].valueAsText
        output_features = parameters[param_map["output_features"]].valueAsText
        
        # Validate inputs
        validate_feature_class(input_features, messages)
        validate_feature_class(clip_features, messages)
        
        messages.addMessage("Executing clip operation...")
        
        # Execute clip
        arcpy.analysis.Clip(
            in_features=input_features,
            clip_features=clip_features,
            out_feature_class=output_features
        )
        
        # Report results
        result_count = int(arcpy.management.GetCount(output_features)[0])
        messages.addMessage(f"✓ Created {result_count} clipped features")
        
    except Exception as e:
        messages.addErrorMessage(f"Error in clip: {str(e)}")
        raise
```

### Shared Helpers (Toolset Pattern)

Tools within a toolset can share helper functions:

**src/tools/spatial_analysis/helpers/geoprocessing.py**:

```python
"""Shared geoprocessing helpers for spatial analysis tools."""

import arcpy


def validate_feature_class(feature_class: str, messages) -> bool:
    """
    Validate that a feature class exists.
    
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
        messages.addWarningMessage(
            f"Warning: {feature_class} has unknown spatial reference"
        )
    else:
        messages.addMessage(
            f"Spatial Reference: {sr.name} (WKID: {sr.factoryCode})"
        )


def get_feature_count(feature_class: str) -> int:
    """
    Get feature count.
    
    Args:
        feature_class: Path to feature class
        
    Returns:
        Number of features
    """
    return int(arcpy.management.GetCount(feature_class)[0])
```

---

## Metadata Generation

### The Problem with ArcGIS Pro Python Toolbox Metadata

Traditional ArcGIS Pro Python Toolbox metadata management has significant challenges:

**Common Issues:**
- 🔴 **Metadata Loss** - `.pyt.xml` files are easily lost, corrupted, or accidentally deleted
- 🔴 **Manual Editing** - Editing XML by hand is error-prone and tedious
- 🔴 **Version Control Issues** - Large XML files create messy diffs and merge conflicts
- 🔴 **Inconsistency** - No single source of truth; docs can drift from actual tool parameters
- 🔴 **Regeneration Difficulty** - If metadata is lost, recreating it manually is painful
- 🔴 **Team Collaboration** - Hard to review/maintain when spread across multiple XML files

**Traditional Workflow (Problematic):**
```
┌─────────────────┐
│ Write .pyt code │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Right-click tool in │
│ ArcGIS Pro catalog  │
│ → Edit metadata     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Manually enter:     │
│ - Summary           │
│ - Usage             │
│ - Parameters        │
│ - Code samples      │
│ → Saved to .pyt.xml │
└────────┬────────────┘
         │
         ▼
    ⚠️ XML file can be:
    - Lost during moves
    - Corrupted by ArcGIS Pro
    - Accidentally deleted
    - Overwritten incorrectly
    
    → No easy way to recover!
```

### The YAML-Based Solution

This framework solves metadata management by treating YAML as the **single source of truth**:

**YAML-Driven Workflow (Robust):**
```
┌──────────────────────────┐
│ Write tool YAML config   │
│ with documentation:      │
│                          │
│ documentation:           │
│   summary: ...           │
│   usage: ...             │
│   parameter_syntax: ...  │
│   code_samples: ...      │
│                          │
│ ✓ Version controlled     │
│ ✓ Easy to edit           │
│ ✓ Human readable         │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Run metadata generator:  │
│                          │
│ Option 1: CLI            │
│ python -m toolbox...     │
│                          │
│ Option 2: Toolbox Tool   │
│ "Load Tool Metadata"     │
│                          │
│ → Generates .pyt.xml     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ .pyt.xml files created   │
│ (can regenerate anytime!)│
│                          │
│ Lost metadata? Just run  │
│ the generator again!     │
└──────────────────────────┘
```

**Key Benefits:**
- ✅ **Regenerable** - Lost or corrupted metadata? Just regenerate from YAML
- ✅ **Version Controlled** - YAML is clean, readable, and git-friendly
- ✅ **Single Source of Truth** - Documentation lives with tool configuration
- ✅ **Easy Editing** - Markdown-style text in YAML vs. XML editing
- ✅ **Consistency** - Tool parameters and docs always in sync
- ✅ **Team Friendly** - Easy to review changes in pull requests
- ✅ **Automated** - Can be part of build/deployment pipeline

### Load Tool Metadata Utility

The toolbox includes a utility tool to generate ArcGIS Pro XML metadata from YAML documentation sections.

**Note:** The metadata loader is a self-contained tool in `tools/load_tool_metadata/` with its own `metadata_generator.py` module.

**Usage Methods:**

#### Method 1: Using the Toolbox Tool (GUI)

1. Open your toolbox in ArcGIS Pro
2. Run the **"Load Tool Metadata"** tool
3. Tool will process all enabled tools and generate `.pyt.xml` files
4. Close and reopen the toolbox to see updated metadata
5. Right-click tool → Item Description to verify

**Perfect for:**
- Developers working in ArcGIS Pro
- Quick metadata updates during development
- Testing documentation changes

#### Method 2: Using the CLI (Automation)

```powershell
# From project root (if you create a script)
python scripts/regenerate_metadata.py

# Or use the tool's execute function directly
python -c "from src.tools.load_tool_metadata.execute import execute_load_tool_metadata; execute_load_tool_metadata(...)"
```

**Perfect for:**
- CI/CD pipelines
- Automated builds
- Batch regeneration after git pulls
- Pre-commit hooks

**Script Example:**

```python
# scripts/regenerate_metadata.py
"""Regenerate all tool metadata from YAML configurations."""

from pathlib import Path
from src.framework.metadata.generator import MetadataGenerator
from src.framework.config.schema import load_toolbox_config, load_tool_config

def regenerate_all_metadata():
    """Regenerate metadata for all enabled tools."""
    # Load toolbox configuration
    config_dir = Path(__file__).parent.parent / "toolbox" / "tools" / "config"
    toolbox_config = load_toolbox_config(config_dir)
    
    print(f"Regenerating metadata for {toolbox_config.toolbox.label}...")
    
    generator = MetadataGenerator()
    success_count = 0
    
    for tool_ref in toolbox_config.tools:
        if not tool_ref.enabled:
            continue
        
        try:
            # Load tool config
            tool_config_path = config_dir / tool_ref.config
            tool_config = load_tool_config(tool_config_path)
            
            # Generate XML metadata
            xml_path = generator.generate_tool_metadata(tool_config)
            print(f"✓ Generated: {xml_path.name}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Failed: {tool_ref.name} - {e}")
    
    print(f"\nSuccessfully regenerated metadata for {success_count} tool(s)")
    return success_count > 0

if __name__ == "__main__":
    import sys
    success = regenerate_all_metadata()
    sys.exit(0 if success else 1)
```

### What Gets Generated

The metadata generator creates comprehensive `.pyt.xml` files that populate ArcGIS Pro's tool help interface with:

**When you open a tool in ArcGIS Pro, users see:**
- **Tool Summary** - Brief description (appears in search results and tool dialog)
- **Detailed Usage** - Instructions, tips, and best practices
- **Parameter Help** - For each parameter:
  - Dialog explanation (what users see in GUI)
  - Scripting explanation (how to use in Python)
- **Code Samples** - Ready-to-run Python examples with explanations
- **Keywords/Tags** - For better tool discovery
- **Credits & Limitations** - Attribution and usage restrictions

**The key benefit:** All this rich documentation appears directly in ArcGIS Pro when users click the help icon or view tool information - no need for separate documentation files or wikis!

### Recovery Scenarios

**Scenario 1: Lost XML Files**
```powershell
# Oops! Deleted all .pyt.xml files
# No problem - regenerate from YAML:
python -m toolbox.framework.metadata.loader_tool
```

**Scenario 2: After Git Pull**
```powershell
# Team member updated tool documentation
git pull
python -m toolbox.framework.metadata.loader_tool
# Fresh metadata from updated YAML
```

**Scenario 3: Corrupted Metadata**
```powershell
# ArcGIS Pro corrupted a metadata file
# Delete it and regenerate:
Remove-Item src/yaml_toolbox.BufferAnalysisTool.pyt.xml
python -m toolbox.framework.metadata.loader_tool
```

### Best Practices

1. **Don't Version Control `.pyt.xml` Files**
   - Add `*.pyt.xml` to `.gitignore`
   - These are generated artifacts, not source files
   - Let each developer regenerate locally

2. **Regenerate After YAML Changes**
   - Update documentation in YAML
   - Run metadata generator
   - Test in ArcGIS Pro

3. **Include in CI/CD**
   ```yaml
   # .github/workflows/build.yml
   - name: Generate metadata
     run: python -m toolbox.framework.metadata.loader_tool
   
   - name: Verify metadata exists
     run: |
       if (!(Test-Path src/*.pyt.xml)) {
         throw "Metadata generation failed"
       }
   ```

4. **Pre-commit Hook** (Optional)
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   # Regenerate metadata if YAML configs changed
   if git diff --cached --name-only | grep -q "\.yml$"; then
       python -m toolbox.framework.metadata.loader_tool
   fi
   ```

**Benefits:**
- ✅ Single source of truth (YAML files)
- ✅ Automatically generated XML metadata
- ✅ No manual XML editing needed
- ✅ Version control friendly
- ✅ Comprehensive tool documentation
- ✅ Recoverable at any time

---

## Complete Workflow Example

### Adding a New Tool

**Option A: Standalone Tool**

**Step 1: Create tool folder**

```powershell
mkdir src/tools/merge_features
```

**Step 2: Create tool.yml**

Create `src/tools/merge_features/tool.yml`:

```yaml
tool:
  name: merge_features
  label: "Merge Features"
  description: "Merge multiple feature classes into one"
  category: "Data Management"
  canRunInBackground: true

implementation:
  module: "execute"  # execute.py in same folder

parameters:
  - name: input_features
    index: 0
    displayName: "Input Features"
    datatype: GPValueTable
    parameterType: Required
    direction: Input
    description: "Feature classes to merge"
    columns:
      - ["Feature Class", "GPFeatureLayer"]
  
  - name: output_features
    index: 1
    displayName: "Output Features"  
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Output
    description: "Merged output feature class"

documentation:
  summary: |
    Merges multiple feature classes into a single feature class.
  usage: |
    Use this tool to combine features from multiple sources.
  tags:
    - merge
    - combine
    - data management
```

**Step 3: Implement execute.py**

Create `src/tools/merge_features/execute.py`:

```python
"""Merge features business logic."""

import arcpy


def execute_merge(parameters, messages):
    """
    Execute merge operation.
    
    Args:
        parameters: ArcGIS tool parameters (list)
        messages: ArcGIS messages object
    """
    try:
        # Extract parameters by index
        input_value_table = parameters[0].value
        output_features = parameters[1].valueAsText
        
        # Parse value table
        input_list = [row[0] for row in input_value_table]
        
        messages.addMessage(f"Merging {len(input_list)} feature classes...")
        
        # Validate all inputs
        for fc in input_list:
            validate_feature_class(fc, messages)
            count = get_feature_count(fc)
            messages.addMessage(f"  {fc}: {count:,} features")
        
        # Execute merge
        arcpy.management.Merge(
            inputs=input_list,
            output=output_features
        )
        
        # Report results
        result_count = int(arcpy.management.GetCount(output_features)[0])
        messages.addMessage(f"✓ Created {result_count:,} merged features")
        messages.addMessage("Merge complete!")
        
    except Exception as e:
        messages.addErrorMessage(f"Error in merge: {str(e)}")
        raise
```

**Step 4: Add to toolbox**

Edit `src/toolboxes/spatial_analysis/toolbox.yml`:

```yaml
tools:
  # ... existing tools ...
  
  - name: merge_features
    enabled: true
    implementation_path: "merge_features"
```

**Step 5: Create test (optional but recommended)**

Create `src/tools/merge_features/test_merge.py`:

```python
"""Tests for merge tool."""

import pytest


def test_merge_tool_exists(get_tool):
    """Verify merge tool can be loaded."""
    tool_path = get_tool("merge_features")
    assert (tool_path / "tool.yml").exists()
```

**That's it!** Auto-discovery will find and test the tool automatically.

---

## Benefits

### 1. Folder-per-Tool Organization
- **Self-contained**: Each tool is a complete module
- **Co-located tests**: Tests live with implementation
- **Toolset pattern**: Related tools can share helpers
- **Easy to navigate**: Clear folder structure
- **Scalable**: Add tools without affecting others

### 2. Complete Separation of Concerns
- **tool.yml**: Tool configuration and documentation
- **execute.py**: Business logic implementation
- **test_*.py**: Tests (co-located with tool)
- **helpers/**: Shared utilities (for toolsets)
- **framework/**: Core infrastructure (rarely changes)

### 2. Minimal Boilerplate
- **Traditional**: 50+ lines per tool for parameters + separate tool class
- **YAML approach**: Just YAML config + utils function (no tool wrapper class!)
- **Factory-based**: Tool classes created automatically at runtime

### 3. Easy to Maintain
- Change parameter? Edit tool's YAML file only
- Add tool? Create YAML + utils function + add to registry (no manual tool class)
- Fix logic? Edit utils only
- Enable/disable tool? Set `enabled: false` in registry
- Update documentation? Edit YAML and run metadata loader

### 4. Easy to Test
- Utils are pure functions with clear interfaces
- Helpers are isolated
- Mock ArcPy in utils tests
- No ArcGIS Pro needed for logic tests
- Configuration validation separate from runtime

### 5. Self-Documenting
- Each tool has its own YAML file
- Clear parameter definitions with indices
- Comprehensive documentation metadata in YAML
- Automatic XML metadata generation
- Easy to review changes in git (small files)
- Better for team collaboration

### 6. Reusability
- Helpers shared across all tools
- Utils functions can be called standalone or from tools
- Runtime validation rules reusable across parameters
- Documentation patterns consistent

### 7. Modular Configuration
- One file per tool = easy to find
- Less merge conflicts in version control
- Can distribute tool configs independently
- Clear ownership (one file = one tool)
- Tools can be enabled/disabled without code changes

### 8. Advanced Features
- **Runtime validation** - Define validation rules in YAML
- **Metadata generation** - Automatic XML from YAML docs
- **Factory pattern** - Dynamic tool class generation
- **Type safety** - Pydantic validates everything
- **Index-based parameters** - Simple, direct parameter access

---

## Validation

### Runtime Validation

Define validation rules in parameter YAML configuration:

```yaml
parameters:
  - name: buffer_distance
    # ... other fields ...
    validation:
      - type: greater_than
        value: 0
        message: "Buffer distance must be positive"
      - type: less_than
        value: 10000
        message: "Buffer distance too large"
```

**Supported validation types:**
- `greater_than`, `less_than` - Numeric comparisons
- `min_value`, `max_value` - Range validation
- `one_of` - Value must be in list
- `not_empty` - String cannot be empty
- `regex` - Pattern matching

### Configuration Validation Script

Validate all YAML configurations before deployment:

**src/framework/scripts/validate_config.py**:

```python
"""Validate all YAML configurations."""

from pathlib import Path

from src.framework.config.schema import load_tool_config, load_toolbox_config


def validate_all_configs():
    """Validate toolbox and all tool configurations."""
    config_dir = Path(__file__).parent.parent.parent / "tools" / "config"
    
    print("Validating toolbox configuration...")
    try:
        toolbox_config = load_toolbox_config(config_dir)
        print(f"✓ Toolbox: {toolbox_config.toolbox.label}")
        print(f"  Found {len(toolbox_config.tools)} tool references")
    except Exception as e:
        print(f"✗ Toolbox validation failed: {e}")
        return False
    
    print("\nValidating individual tool configurations...")
    all_valid = True
    for tool_ref in toolbox_config.tools:
        tool_config_path = config_dir / tool_ref.config
        try:
            tool_config = load_tool_config(tool_config_path)
            status = "✓ (enabled)" if tool_ref.enabled else "○ (disabled)"
            print(f"{status} {tool_ref.name}: {tool_config.tool.label}")
            print(f"      {len(tool_config.parameters)} parameters")
        except Exception as e:
            print(f"✗ {tool_ref.name}: {e}")
            all_valid = False
    
    if all_valid:
        print("\n✓ All configurations valid!")
    else:
        print("\n✗ Some configurations have errors")
    
    return all_valid


if __name__ == "__main__":
    import sys
    success = validate_all_configs()
    sys.exit(0 if success else 1)
```

**Run before committing:**

```powershell
python -m toolbox.framework.scripts.validate_config
```

---

## Testing

### Unit Testing Utils Functions

**tests/test_buffer.py**:

```python
"""Tests for buffer analysis."""

import pytest
from unittest.mock import Mock, patch

from src.framework.config.schema import (
    ImplementationConfig,
    ParameterConfig,
    ToolConfig,
    ToolMetadata,
)
from src.tools.utils.buffer import execute_buffer


@pytest.fixture
def mock_buffer_config():
    """Create mock tool configuration."""
    return ToolConfig(
        tool=ToolMetadata(
            name="buffer_analysis",
            label="Buffer Analysis",
            description="Buffer features",
            category="Analysis"
        ),
        implementation=ImplementationConfig(
            executeFunction="toolbox.tools.utils.buffer.execute_buffer"
        ),
        parameters=[
            ParameterConfig(
                name="input_features",
                index=0,
                displayName="Input Features",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input"
            ),
            # ... other parameters
        ]
    )


@pytest.fixture
def mock_parameters():
    """Create mock ArcGIS parameters."""
    params = [Mock() for _ in range(5)]
    params[0].valueAsText = "input.shp"
    params[1].value = 100.0
    params[2].valueAsText = "meters"
    params[3].value = True
    params[4].valueAsText = "output.shp"
    return params


@patch('arcpy.analysis.Buffer')
@patch('arcpy.management.GetCount')
def test_execute_buffer(mock_count, mock_buffer, mock_parameters, mock_buffer_config):
    """Test buffer execution with mocked arcpy."""
    mock_count.return_value = ["42"]
    messages = Mock()
    
    # Execute
    execute_buffer(mock_parameters, messages, mock_buffer_config)
    
    # Verify arcpy calls
    mock_buffer.assert_called_once()
    
    # Verify messages
    assert messages.addMessage.called
    assert messages.addErrorMessage.call_count == 0
```

### Integration Testing

**tests/test_buffer_tool.py**:

```python
"""Integration tests for buffer tool."""

import pytest
from pathlib import Path

from src.framework.base.yaml_tool import YAMLTool
from src.framework.config.schema import load_tool_config


def test_buffer_tool_config_loads():
    """Test that buffer tool configuration loads correctly."""
    toolbox_path = Path(__file__).parent.parent / "toolbox"
    config_path = toolbox_path / "tools" / "config" / "tools" / "buffer_analysis.yml"
    
    # Load and validate config
    config = load_tool_config(config_path)
    
    assert config.tool.name == "buffer_analysis"
    assert config.tool.label == "Buffer Analysis"
    assert len(config.parameters) == 5
    
    # Verify parameter indices are correct
    indices = [p.index for p in config.parameters]
    assert indices == [0, 1, 2, 3, 4]


def test_buffer_tool_parameters():
    """Test that YAMLTool generates parameters correctly."""
    # Create a test tool instance (doesn't need arcpy for this)
    from src.framework.factory import create_tool_class
    from unittest.mock import Mock
    
    config_path = Path(__file__).parent.parent / "toolbox" / "tools" / "config" / "tools" / "buffer_analysis.yml"
    tool_class = create_tool_class("buffer_analysis", config_path, Mock())
    tool = tool_class()
    
    # Get parameters (requires arcpy)
    params = tool.getParameterInfo()
    
    assert len(params) == 5
    assert params[0].name == "input_features"
    assert params[1].name == "buffer_distance"
```

**tests/test_integration.py** - Full integration tests (requires ArcGIS Pro):

```python
"""Integration tests for ArcGIS tools."""

import pytest
import arcpy
from pathlib import Path


@pytest.fixture
def test_workspace(tmp_path):
    """Create temporary geodatabase for testing."""
    gdb_path = tmp_path / "test.gdb"
    arcpy.management.CreateFileGDB(str(tmp_path), "test.gdb")
    return str(gdb_path)


@pytest.fixture
def sample_features(test_workspace):
    """Create sample features for testing."""
    fc_path = f"{test_workspace}\\test_points"
    
    # Create feature class
    arcpy.management.CreateFeatureclass(
        test_workspace,
        "test_points",
        "POINT"
    )
    
    # Add sample point
    with arcpy.da.InsertCursor(fc_path, ["SHAPE@XY"]) as cursor:
        cursor.insertRow([(0, 0)])
    
    return fc_path


def test_buffer_tool_execution(test_workspace, sample_features):
    """Test buffer tool execution."""
    output_fc = f"{test_workspace}\\buffer_output"
    
    # Execute buffer
    arcpy.analysis.Buffer(
        in_features=sample_features,
        out_feature_class=output_fc,
        buffer_distance_or_field="100 meters"
    )
    
    # Verify output exists
    assert arcpy.Exists(output_fc)
    
    # Verify feature count
    count = int(arcpy.management.GetCount(output_fc)[0])
    assert count == 1
```

---

## Best Practices

### 1. YAML Organization
- ✅ One YAML file per tool
- ✅ Keep toolbox.yml focused (metadata + registry only)
- ✅ Use consistent naming: `{tool_name}.yml`
- ✅ Use `index` field explicitly for all parameters (0-based)
- ✅ Include documentation sections for metadata generation

### 2. Naming Conventions
- ✅ Tool names: `snake_case` (buffer_analysis)
- ✅ Display names: "Title Case" (Buffer Analysis)
- ✅ Python modules: `snake_case` (buffer.py in utils/)
- ✅ Execute functions: `execute_{tool_name}`
- ✅ YAML filenames must match `tool.name` field

### 3. Documentation
- ✅ Add descriptions to all parameters
- ✅ Document expected values and ranges
- ✅ Include `documentation` section for ArcGIS Pro metadata
- ✅ Provide code samples showing typical usage
- ✅ Keep YAML comments minimal - use documentation section instead

### 4. Parameter Design
- ✅ Always specify explicit `index` for each parameter
- ✅ Ensure indices start at 0 with no gaps
- ✅ Use filters to constrain input values
- ✅ Add validation rules for runtime checks
- ✅ Set appropriate default values

### 5. Version Control
- ✅ Commit YAML changes separately from Python
- ✅ Use descriptive commit messages for config changes
- ✅ Validate configs in CI/CD pipeline
- ✅ Tag releases with version numbers

### 6. Testing Strategy
- ✅ Unit test utils functions (mock ArcPy)
- ✅ Integration test with real ArcPy (mark as slow)
- ✅ Validate YAML in pre-commit hooks
- ✅ Test helpers independently
- ✅ Test configuration loading separately from execution

### 7. Error Handling
- ✅ Validate inputs in utils functions using helpers
- ✅ Provide clear error messages with context
- ✅ Use Pydantic for type validation at load time
- ✅ Log warnings for non-fatal issues
- ✅ Add error context in factory-generated tool classes

### 8. Performance
- ✅ Load YAML configs once at module import time
- ✅ Tools are created dynamically but cached
- ✅ Use lazy imports for heavy dependencies
- ✅ Profile geoprocessing operations
- ✅ Consider background execution for long tasks

### 9. Metadata Management
- ✅ Define documentation in YAML files
- ✅ Generate XML metadata with loader utility
- ✅ Keep metadata synchronized with code
- ✅ Version control XML output for tracking changes
- ✅ Use consistent documentation patterns

---

## Summary

This YAML-based approach provides:

1. **Zero Boilerplate** - No manual tool wrapper classes needed
2. **Factory Pattern** - Dynamic tool class generation at runtime
3. **Index-Based Parameters** - Direct, simple parameter access
4. **Comprehensive Documentation** - YAML to XML metadata generation
5. **Runtime Validation** - Optional validation rules in YAML
6. **Type Safety** - Pydantic validates all configurations
7. **Modular Design** - Clear separation of concerns
8. **Easy Testing** - Utils as pure functions, helpers isolated
9. **Version Control Friendly** - Small, focused YAML files
10. **Self-Documenting** - YAML serves as living documentation

**Workflow for Adding a New Tool:**

1. Add tool reference to `toolbox.yml` registry
2. Create tool YAML configuration with parameters and documentation
3. Implement business logic in utils function
4. Run metadata loader to generate XML (optional)
5. Tool automatically discovered and loaded by factory

**No manual tool class creation. No parameter mapping. Just YAML and business logic.**

---

## Additional Resources

- **[Metadata Guide](metadata-guide.md)** - Comprehensive documentation metadata
- **[Architecture Guide](development/architecture.md)** - System architecture details
- **[Testing Guide](development/testing.md)** - Testing strategies and examples
- **[Setup Guide](development/setup.md)** - Development environment setup

---

**This YAML-based approach with factory pattern transforms ArcGIS Pro toolbox development into a maintainable, scalable, and collaborative process. By eliminating manual tool wrapper classes and using dynamic code generation, teams can focus entirely on business logic while the framework handles all boilerplate.**

