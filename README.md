# YAML-Based ArcGIS Pro Python Toolbox

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modern, maintainable approach to building ArcGIS Pro Python Toolboxes using YAML configuration with **dynamic tool generation** - zero boilerplate code required.

## Overview

This project demonstrates a YAML-based architecture for ArcGIS Pro toolboxes that:

- ✅ **Eliminates boilerplate** - No wrapper classes needed, tools generated dynamically at runtime
- ✅ **Declarative configuration** - Define tools entirely in YAML
- ✅ **Type-safe** - Pydantic validation for all configurations
- ✅ **Modular design** - One YAML file per tool
- ✅ **Rich metadata** - Comprehensive documentation generated from YAML
- ✅ **Easy to test** - Mocked arcpy allows unit testing without ArcGIS Pro
- ✅ **Version control friendly** - Small, focused files with clear diffs

## Project Structure

```
arcgispro-yaml-pyt/
├── toolbox/
│   ├── yaml_toolbox.pyt        # Toolbox entry point (auto-discovers tools)
│   │
│   ├── framework/               # Backend infrastructure (reusable)
│   │   ├── factory.py          # Dynamic tool class generation
│   │   ├── base/
│   │   │   └── yaml_tool.py    # YAMLTool base class
│   │   ├── config/
│   │   │   └── schema.py       # Pydantic validation schemas
│   │   ├── validation/
│   │   │   ├── runtime_validator.py      # Parameter validation
│   │   │   └── config_validator.py       # Config validation
│   │   ├── metadata/
│   │   │   ├── generator.py              # XML metadata generation
│   │   │   └── loader_tool.py            # Metadata loader utility
│   │   └── scripts/            # Dev/admin scripts
│   │       └── validate_config.py
│   │
│   └── tools/                   # Business logic (tool-specific)
│       ├── config/
│       │   ├── toolbox.yml     # Toolbox metadata + registry
│       │   └── tools/          # Individual tool YAMLs
│       │       ├── buffer_analysis.yml
│       │       ├── clip_features.yml
│       │       └── load_tool_metadata.yml
│       ├── utils/              # Tool execution functions
│       │   ├── buffer.py
│       │   └── clip.py
│       └── helpers/            # Business helpers
│           └── geoprocessing.py
│
├── tests/                       # Test suite (arcpy mocked)
│   ├── conftest.py             # Pytest fixtures & arcpy mocking
│   ├── test_buffer_tool.py
│   ├── test_buffer.py
│   ├── test_clip_tool.py
│   ├── test_clip.py
│   ├── test_config_validation.py
│   └── test_yaml_loading.py
│
├── docs/                        # Documentation
│   ├── configuration-guide.md
│   ├── metadata-guide.md
│   └── development/
│       ├── setup.md
│       ├── testing.md
│       └── architecture.md
│
├── pyproject.toml               # Project dependencies
└── README.md                    # This file
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
4. Navigate to `toolbox/yaml_toolbox.pyt`
5. The toolbox will appear with two tools:
   - **Buffer Analysis** - Create buffer polygons around input features
   - **Clip Features** - Clip features to a boundary

## Adding a New Tool

Adding a tool requires **only 2 files** - no wrapper classes needed!

### 1. Add tool to registry

Edit `toolbox/tools/config/toolbox.yml`:

```yaml
tools:
  - name: my_new_tool
    enabled: true
    config: "tools/my_new_tool.yml"
```

### 2. Create tool YAML configuration

Create `toolbox/tools/config/tools/my_new_tool.yml`:

```yaml
tool:
  name: my_new_tool
  label: "My New Tool"
  description: "Description of what the tool does"
  category: "Analysis"
  canRunInBackground: true

implementation:
  executeFunction: "toolbox.tools.utils.my_new_tool.execute_my_new_tool"
  canRunInBackground: true

parameters:
  - name: input_param
    index: 0  # Parameter order (0-based)
    displayName: "Input Parameter"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Input
    description: "Description of parameter"
  
  - name: output_param
    index: 1
    displayName: "Output Parameter"
    datatype: GPFeatureLayer
    parameterType: Required
    direction: Output
    description: "Output description"
    
  # Optional: Add validation rules inline
  - name: distance_param
    index: 2
    displayName: "Distance"
    datatype: GPDouble
    parameterType: Optional
    direction: Input
    validation:
      - type: greater_than
        value: 0
        message: "Distance must be positive"
```

### 3. Implement business logic

Create `toolbox/tools/utils/my_new_tool.py`:

```python
import arcpy
from toolbox.framework.config.schema import ToolConfig
from toolbox.framework.validation.runtime_validator import validate_all_parameters

def execute_my_new_tool(parameters, messages, config: ToolConfig):
    """Execute the tool logic."""
    # Build parameter index map
    param_map = {p.name: p.index for p in config.parameters}
    
    # Validate parameters
    validate_all_parameters(parameters, config, messages)
    
    # Extract parameters
    input_param = parameters[param_map["input_param"]].valueAsText
    output_param = parameters[param_map["output_param"]].valueAsText
    
    # Your geoprocessing logic here
    messages.addMessage("Processing...")
    # ... arcpy operations ...
    messages.addMessage("Complete!")
```

That's it! The tool class is **generated dynamically** at runtime. No wrapper class needed!

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
python toolbox/framework/scripts/validate_config.py

# Or use the built-in "Load Tool Metadata" utility in ArcGIS Pro
```

## Validation

Validate all YAML configurations before committing:

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run validation
python toolbox/framework/scripts/validate_config.py
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
