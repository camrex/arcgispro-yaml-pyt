# Contributing to arcgispro-yaml-pyt

Thank you for your interest in contributing to this project! This guide will help you get started.

## Development Setup

See [docs/development/setup.md](docs/development/setup.md) for complete development environment setup instructions.

### Quick Start

```powershell
# 1. Clone the repository
git clone https://github.com/camrex/arcgispro-yaml-pyt.git
cd arcgispro-yaml-pyt

# 2. Set up UV environment for development
uv venv
.venv\Scripts\Activate.ps1
uv pip install pydantic>=2.5.0 pyyaml>=6.0 pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 ruff>=0.1.0

# 3. Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

### Daily Development

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run tests
pytest tests/ -v

# Lint and format
ruff check .
ruff format .

# Type checking
ty .
```

### Running Tools in ArcGIS Pro

1. Activate the ArcGIS Pro environment
2. Open ArcGIS Pro
3. Add the toolbox: `src/toolboxes/spatial_analysis/spatial_analysis.pyt` or `src/toolboxes/utilities/utilities.pyt`

## Testing

We use a hybrid testing approach:

- **Unit tests** - Run in UV environment with mocked arcpy
- **Integration tests** - Run in ArcGIS Pro environment with real arcpy

See [docs/development/testing.md](docs/development/testing.md) for details.

## Project Structure

```
arcgispro-yaml-pyt/
├── src/
│   ├── framework/                    # Reusable framework
│   │   ├── factory.py               # Dynamic tool generation
│   │   ├── yaml_tool.py             # Base class
│   │   ├── schema.py                # Pydantic schemas
│   │   └── validators.py            # Validation
│   │
│   ├── tools/                        # Tool implementations
│   │   ├── spatial_analysis/        # Toolset (related tools)
│   │   │   ├── buffer_analysis/    # Self-contained tool
│   │   │   ├── clip_features/
│   │   │   └── helpers/            # Shared helpers
│   │   └── load_tool_metadata/     # Standalone tool
│   │
│   └── toolboxes/                   # Multiple .pyt files
│       ├── spatial_analysis/        # spatial_analysis.pyt
│       └── utilities/               # utilities.pyt
│
├── tests/                            # Framework tests + auto-discovery
├── scripts/                          # Validation scripts
└── docs/                             # Documentation
```

## Key Concepts

Before contributing, understand these core concepts:

### Framework
The reusable infrastructure layer (`src/framework/`) that provides:
- Dynamic tool class generation from YAML
- Validation engine and schemas
- No domain-specific business logic
- Pure machinery for toolbox generation

### Tool
A self-contained, standalone unit with its own directory:
- Location: `src/tools/{tool_name}/`
- Contains: `tool.yml`, `execute.py`, `test_*.py`
- Example: `load_tool_metadata/`
- **Use when:** Tool has no dependencies or shared logic with other tools

### Toolset
A collection of related tools organized together:
- Location: `src/tools/{toolset_name}/`
- Contains: Multiple tool subdirectories + shared `helpers/`
- Example: `spatial_analysis/` with `buffer_analysis/`, `clip_features/`, and shared geoprocessing helpers
- **Use when:** 
  - Tools share helper functions or utilities
  - Tools are part of an orchestrated workflow
  - Related tools benefit from shared domain logic

### Toolbox
An ArcGIS Pro Python Toolbox (`.pyt` file):
- Location: `src/toolboxes/{toolbox_name}/`
- Contains: `{toolbox_name}.pyt` and `toolbox.yml`
- Registers tools from the tools/ directory
- Many-to-many: Same tool can appear in multiple toolboxes
- Examples: `spatial_analysis.pyt`, `utilities.pyt`

## Architecture Principles

### Framework (src/framework/)
- **Flat, focused structure** - No nested subdirectories
- **Dynamic tool generation** - Zero boilerplate classes
- **Pure machinery** - No domain logic
- Files: `factory.py`, `yaml_tool.py`, `schema.py`, `validators.py`

### Tools (src/tools/)
- **Folder-per-tool** - Each tool is self-contained
- **Co-located tests** - Tests live with the tool
- **Toolset pattern** - Related tools can share helpers
- Examples: `spatial_analysis/buffer_analysis/`, `load_tool_metadata/`

### Toolboxes (src/toolboxes/)
- **Multiple .pyt files** - Separate toolboxes for organization
- **Many-to-many** - Same tool can be in multiple toolboxes
- Each toolbox has its own `toolbox.yml`
- Business-specific helpers

## Making Changes

### Adding a New Tool

**Option A: Standalone Tool**
1. Create `src/tools/{tool_name}/` directory
2. Add `tool.yml`, `execute.py`, `test_{tool_name}.py`
3. Register in `src/toolboxes/{toolbox_name}/toolbox.yml`

**Option B: Tool in Toolset**
1. Create `src/tools/{toolset}/{tool_name}/` directory
2. Add `tool.yml`, `execute.py`, `test_{tool_name}.py`
3. Share helpers via `{toolset}/helpers/`
4. Register in `src/toolboxes/{toolbox_name}/toolbox.yml`

Auto-discovery will find and test it automatically!

See [docs/configuration-guide.md](docs/configuration-guide.md) for complete details.

### Modifying the Framework

1. Make changes in `src/framework/`
2. Ensure all existing tests pass
3. Add new tests for new functionality
4. Update documentation if needed

## Pull Request Guidelines

1. **Test your changes**
   - All unit tests must pass: `pytest tests/ -v`
   - Run linting: `ruff check .`
   - Run type checking: `ty .`

2. **Update documentation**
   - Update relevant docs if you change functionality
   - Add docstrings for new functions/classes

3. **Keep commits focused**
   - One logical change per commit
   - Write clear commit messages

4. **Pull request description**
   - Describe what changes were made and why
   - Reference any related issues

## Code Style

- **Python 3.11+** required
- Follow PEP 8 (enforced by Ruff)
- Type hints required (checked by ty)
- Line length: 100 characters
- Use double quotes for strings

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- See [docs/development/architecture.md](docs/development/architecture.md) for design details

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

