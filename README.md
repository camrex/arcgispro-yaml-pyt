# YAML-Based ArcGIS Pro Python Toolbox

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modern, maintainable approach to building ArcGIS Pro Python Toolboxes using YAML configuration with **dynamic tool generation** and **folder-per-tool architecture** - zero boilerplate code required.

## Overview

This project demonstrates a YAML-based architecture for ArcGIS Pro toolboxes that:

- ✅ **Eliminates boilerplate** - No wrapper classes needed, tools generated dynamically at runtime
- ✅ **Declarative configuration** - Define tools entirely in YAML  
- ✅ **Folder-per-tool** - Self-contained modules with co-located tests
- ✅ **Multiple toolboxes** - Support for organizing tools into separate .pyt files
- ✅ **Auto-discovery** - Tests discover tools and toolboxes automatically
- ✅ **Type-safe** - Pydantic validation for all configurations
- ✅ **Rich metadata** - Comprehensive documentation generated from YAML
- ✅ **Easy to test** - Mocked arcpy allows unit testing without ArcGIS Pro
- ✅ **Version control friendly** - Small, focused files with clear diffs

## Key Concepts

### Framework
Reusable infrastructure (`src/framework/`) providing dynamic tool generation, validation, and base classes. No domain-specific logic.

### Tool
A standalone unit (`src/tools/{tool_name}/`) with configuration, implementation, and tests. Example: `load_tool_metadata/`

### Toolset  
Related tools organized together (`src/tools/{toolset_name}/`) that share helper functions or form an orchestrated workflow. Example: `spatial_analysis/` contains `buffer_analysis/`, `clip_features/`, and shared `helpers/`

### Toolbox
An ArcGIS Pro .pyt file (`src/toolboxes/`) that registers tools. One toolbox can include tools from multiple toolsets, and one tool can appear in multiple toolboxes.

## Project Structure

```
arcgispro-yaml-pyt/
├── src/
│   ├── framework/                    # Backend infrastructure (reusable)
│   │   ├── factory.py               # Dynamic tool class generation
│   │   ├── yaml_tool.py             # YAMLTool base class
│   │   ├── schema.py                # Pydantic validation schemas
│   │   └── validators.py            # Runtime & config validation
│   │
│   ├── tools/                        # Tool implementations
│   │   ├── spatial_analysis/        # Toolset (related tools + helpers)
│   │   │   ├── buffer_analysis/    # Self-contained tool
│   │   │   │   ├── tool.yml        # Tool configuration
│   │   │   │   ├── execute.py      # Business logic
│   │   │   │   ├── test_buffer_analysis.py  # Co-located tests
│   │   │   │   └── __init__.py
│   │   │   ├── clip_features/      # Another tool in toolset
│   │   │   │   ├── tool.yml
│   │   │   │   ├── execute.py
│   │   │   │   ├── test_clip_features.py
│   │   │   │   └── __init__.py
│   │   │   ├── helpers/            # Shared by toolset
│   │   │   │   └── geoprocessing.py
│   │   │   └── README.md
│   │   │
│   │   └── load_tool_metadata/     # Standalone tool
│   │       ├── tool.yml
│   │       ├── execute.py
│   │       ├── metadata_generator.py
│   │       ├── test_metadata_loader.py
│   │       └── __init__.py
│   │
│   └── toolboxes/                   # Multiple .pyt files
│       ├── spatial_analysis/
│       │   ├── spatial_analysis.pyt
│       │   ├── toolbox.yml          # Toolbox config
│       │   └── *.pyt.xml            # ArcGIS metadata
│       ├── utilities/
│       │   ├── utilities.pyt
│       │   └── toolbox.yml
│       └── README.md
│
├── tests/                            # Framework tests
│   ├── conftest.py                  # Auto-discovery fixtures
│   ├── test_discovery.py            # Auto-discovery tests
│   ├── test_config_validation.py
│   └── test_yaml_loading.py
│
├── scripts/
│   └── validate_config.py           # Validation script
│
├── docs/                             # Documentation
│   ├── configuration-guide.md
│   ├── metadata-guide.md
│   ├── addon-concept.md
│   └── development/
│       ├── setup.md
│       ├── testing.md
│       └── architecture.md
│
├── pyproject.toml                    # Project dependencies
└── README.md                         # This file
```

## Quick Start

### Prerequisites

- ArcGIS Pro 3.0+
- Python 3.11+ (ArcGIS Pro environment)
- UV (for development environment) - [Install UV](https://docs.astral.sh/uv/)

### Installation

**Development environment setup:**

```powershell
# Install UV (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create and activate UV environment
uv venv
.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install pydantic>=2.5.0 pyyaml>=6.0
uv pip install pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 ruff>=0.1.0
```

**Quick reference:** See [docs/development/setup.md](docs/development/setup.md) for daily workflow  
**Full guide:** See [docs/development/setup.md](docs/development/setup.md) for detailed setup

### Using the Toolbox in ArcGIS Pro

1. Open ArcGIS Pro
2. In the Catalog pane, right-click on **Toolboxes**
3. Select **Add Toolbox**
4. Navigate to `src/toolboxes/spatial_analysis/spatial_analysis.pyt` (or `utilities/utilities.pyt`)
5. The toolbox will appear with its tools:
   - **Spatial Analysis Toolbox**: Buffer Analysis, Clip Features
   - **Utilities Toolbox**: Load Tool Metadata

## Adding a New Tool

The folder-per-tool structure keeps everything organized and self-contained.

### Option A: Standalone Tool

Create a new tool directory:

```
src/tools/my_new_tool/
├── tool.yml           # Tool configuration
├── execute.py         # Business logic  
├── test_my_tool.py    # Tests (co-located!)
└── __init__.py
```

**1. Create `tool.yml`:**

```yaml
tool:
  name: my_new_tool
  label: "My New Tool"
  description: "What the tool does"
  category: "Analysis"
  canRunInBackground: true

implementation:
  executeFunction: "toolbox.tools.my_new_tool.execute.execute_my_new_tool"

parameters:
  - name: input_param
    index: 0
    displayName: "Input Parameter"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    validation:
      - type: not_empty
        message: "Input is required"
```

**2. Create `execute.py`:**

```python
import arcpy
from src.framework.schema import ToolConfig
from src.framework.validators import validate_all_parameters

def execute_my_new_tool(parameters, messages, config: ToolConfig):
    """Execute the tool logic."""
    # Validate
    validate_all_parameters(parameters, config, messages)
    
    # Build param map
    param_map = {p.name: p.index for p in config.parameters}
    
    # Get parameters
    input_fc = parameters[param_map["input_param"]].valueAsText
    
    # Business logic
    messages.addMessage(f"Processing {input_fc}...")
    # ... your arcpy operations ...
    messages.addMessage("Complete!")
```

**3. Register in toolbox:**

Edit `src/toolboxes/spatial_analysis/toolbox.yml` (or create a new toolbox):

```yaml
tools:
  - name: my_new_tool
    enabled: true
    config: "../../tools/my_new_tool/tool.yml"
```

### Option B: Add to Existing Toolset

If your tool shares helpers with existing tools (e.g., more spatial analysis tools), add it to a toolset:

```
src/tools/spatial_analysis/
├── buffer_analysis/
├── clip_features/
├── my_new_tool/          # New tool in toolset
│   ├── tool.yml
│   ├── execute.py
│   ├── test_my_tool.py
│   └── __init__.py
└── helpers/              # Shared by all tools in toolset
    └── geoprocessing.py
```

Your tool can use shared helpers:

```python
from src.tools.spatial_analysis.helpers.geoprocessing import check_spatial_reference
```

That's it! The tool class is **generated dynamically** at runtime. No wrapper class needed!

## Testing with Auto-Discovery

Tests automatically discover all tools and toolboxes:

```python
# tests/test_discovery.py validates ALL tools
def test_all_tools_have_valid_config(all_tools):
    """Auto-discovers and validates all tool configs."""
    from src.framework.schema import load_tool_config
    
    for tool_path, tool_name in all_tools:
        config = load_tool_config(tool_path / "tool.yml")
        assert config.tool.name == tool_name
```

Tool-specific tests are co-located:

```
my_new_tool/
├── tool.yml
├── execute.py
└── test_my_tool.py  ← Tests live with the tool!
```

Run tests:

```powershell
pytest -v  # Discovers and runs all tests automatically
```

See [docs/development/testing.md](docs/development/testing.md) for details.

## Tool Documentation & Metadata

Tools support rich metadata documentation that appears in ArcGIS Pro's Item Description:

```yaml
documentation:
  summary: |
    Brief description of what the tool does
  usage: |
    Detailed usage information with tips and best practices
  tags:
    - keyword1
    - keyword2
  credits: "Author and attribution"
  use_limitations: |
    Legal restrictions, warranty disclaimers, usage policies
  parameter_syntax:
    param_name:
      dialog_explanation: "How to use in GUI"
      scripting_explanation: "How to use in scripts"
  code_samples:
    - title: "Example Usage"
      description: "Description of example"
      code: |
        import arcpy
        # Example code
```

See [docs/metadata-guide.md](docs/metadata-guide.md) for complete documentation.

**Regenerate metadata:**
```powershell
# From command line  
python scripts/validate_config.py

# Or use the built-in "Load Tool Metadata" tool in ArcGIS Pro
```

## Validation

Validate all YAML configurations:

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run validation
python scripts/validate_config.py
```

This checks:
- ✅ Toolbox configuration syntax
- ✅ Tool configuration syntax
- ✅ Parameter indices are unique and continuous (0, 1, 2, ...)
- ✅ Validation rules syntax
- ✅ Referenced execute functions exist
- ✅ Pydantic schema validation

## Testing

This project uses **mocked arcpy** for unit tests, allowing testing without ArcGIS Pro installed.

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run all tests (arcpy is automatically mocked)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=toolbox --cov-report=html

# Run specific test file
pytest tests/test_buffer_tool.py -v
```

**How arcpy mocking works:**
- `tests/conftest.py` installs a mock arcpy in `sys.modules` before any imports
- Unit tests run in UV environment (no ArcGIS Pro needed)
- Integration tests require ArcGIS Pro environment (marked with `@pytest.mark.slow`)

See [docs/development/testing.md](docs/development/testing.md) for complete testing documentation.

## Architecture Benefits

### Key Improvements

**1. Folder-per-Tool Organization**
- Each tool is a self-contained module
- Tests live with the tool (co-located)
- Easy to find, understand, and maintain
- Clear ownership and modularity

**2. Toolset Pattern**
- Related tools share helpers (e.g., `spatial_analysis/helpers/`)
- Domain-specific utilities stay scoped
- Framework remains pure machinery

**3. Flattened Framework**
- Simple, flat structure: `factory.py`, `schema.py`, `validators.py`, `yaml_tool.py`
- No nested subdirectories with single files
- Cleaner imports: `from src.framework.schema import ToolConfig`

**4. Multiple Toolboxes**
- Organize tools into separate .pyt files
- Many-to-many relationships (same tool in multiple toolboxes)
- Aligns with ArcGIS Pro Add-in concept

**5. Auto-Discovery Testing**
- Tests discover tools/toolboxes automatically
- Add new tool → automatically tested
- No hardcoded test fixtures

## Traditional vs YAML Approach

### Traditional Approach

```python
# tools/buffer_tool.py (50+ lines per tool)
class BufferTool:
    def __init__(self):
        self.label = "Buffer Analysis"
        self.description = "Create buffer polygons"
        
    def getParameterInfo(self):
        # Repetitive boilerplate for each parameter
        params = []
        param0 = arcpy.Parameter(
            displayName="Input Features",
            name="input_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        params.append(param0)
        # Repeat 4 more times...
        return params
        
    def execute(self, parameters, messages):
        # Extract parameters manually
        input_fc = parameters[0].valueAsText
        # ... more extraction ...
        # Business logic here
```

### YAML + Dynamic Generation Approach

```yaml
# config/tools/buffer_analysis.yml (entire tool definition)
tool:
  name: buffer_analysis
  label: "Buffer Analysis"
  description: "Create buffer polygons"

implementation:
  executeFunction: "toolbox.tools.utils.buffer.execute_buffer"

parameters:
  - name: input_features
    index: 0
    displayName: "Input Features"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
  # ... more parameters ...
```

```python
# utils/buffer.py (just business logic)
def execute_buffer(parameters, messages, config):
    """Pure function with business logic only."""
    param_map = {p.name: p.index for p in config.parameters}
    input_fc = parameters[param_map["input_features"]].valueAsText
    # Business logic here
```

**Result**: **Zero wrapper class boilerplate!** Tool classes generated dynamically at runtime.

## Key Features

- **Zero Boilerplate**: No wrapper classes - tools generated dynamically via `factory.py`
- **Inline Configuration**: Parameter ordering via `index` field, validation rules with parameters
- **Separation of Concerns**: Configuration (YAML), generation (factory), business logic (utils)
- **Type Safety**: Pydantic validates all configurations at load time
- **Testability**: Mocked arcpy allows unit tests without ArcGIS Pro installed
- **Modularity**: Each tool is one YAML file + one business logic file
- **Maintainability**: Small, focused files make code reviews easier
- **Extensibility**: Add new tools without touching existing code

## Documentation

### User Documentation
- [Configuration Guide](docs/configuration-guide.md) - Complete YAML configuration reference
- [Metadata Guide](docs/metadata-guide.md) - Tool documentation and metadata

### Developer Documentation
- [Development Setup](docs/development/setup.md) - Environment setup and workflow
- [Testing Guide](docs/development/testing.md) - Testing strategy and best practices
- [Architecture Guide](docs/development/architecture.md) - Design decisions and system architecture
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project

## Development

### Environment Strategy

This project uses a **hybrid two-environment approach**:

1. **UV Environment** (`.venv/`) - Fast development
   - Linting, formatting, type checking
   - Unit tests (no arcpy)
   - Daily development workflow

2. **ArcGIS Pro Environment** - Integration testing
   - Running tools in ArcGIS Pro
   - Integration tests with arcpy
   - Production environment

See [docs/development/setup.md](docs/development/setup.md) for daily workflow and full setup details.
### Code Quality

This project uses:
- **Ruff** for linting and formatting
- **ty** for type checking (Astral's new type checker)
- **Pytest** for testing with mocked arcpy
- **Pydantic** for schema validation

```powershell
# In UV environment (.venv)
ruff format .       # Format code
ruff check .        # Lint code
ty .                # Type check
pytest tests/ -v    # Run all tests (arcpy mocked)
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick checklist:
1. Fork the repository and create a feature branch
2. Make your changes with tests
3. Run tests, linting, and type checking
4. Update documentation as needed
5. Submit a pull request

## Contact

For questions or issues, please open an issue on GitHub.

