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
3. Add the toolbox: `toolbox/yaml_toolbox.pyt`

## Testing

We use a hybrid testing approach:

- **Unit tests** - Run in UV environment with mocked arcpy
- **Integration tests** - Run in ArcGIS Pro environment with real arcpy

See [docs/development/testing.md](docs/development/testing.md) for details.

## Project Structure

```
arcgispro-yaml-pyt/
├── toolbox/
│   ├── framework/              # Reusable framework (portable)
│   │   ├── factory.py         # Dynamic tool generation
│   │   ├── base/              # Base classes
│   │   ├── config/            # Pydantic schemas
│   │   ├── validation/        # Validation engine
│   │   ├── metadata/          # XML metadata generation
│   │   └── scripts/           # Dev scripts
│   └── tools/                  # Tool-specific business logic
│       ├── config/            # YAML configurations
│       ├── utils/             # Tool execution functions
│       └── helpers/           # Business helpers
├── tests/                      # Test suite
├── docs/                       # Documentation
│   ├── configuration-guide.md
│   ├── metadata-guide.md
│   ├── quickstart.md
│   └── development/           # Developer docs
│       ├── setup.md
│       ├── testing.md
│       └── architecture.md
└── pyproject.toml
```

## Architecture Principles

### Framework (toolbox/framework/)
- **Reusable, portable infrastructure**
- Zero boilerplate - tools generated dynamically at runtime
- YAML schema validation (Pydantic)
- Runtime validation engine
- Metadata XML generation
- Framework doesn't depend on Tools (clean separation)

### Tools (toolbox/tools/)
- **Application-specific business logic**
- Tool configurations (YAML files)
- Implementation functions (execute_buffer, execute_clip, etc.)
- Business-specific helpers

## Making Changes

### Adding a New Tool

1. Create YAML configuration in `toolbox/tools/config/tools/`
2. Register tool in `toolbox/tools/config/toolbox.yml`
3. Implement execution function in `toolbox/tools/utils/`
4. Add tests in `tests/`
5. Generate metadata: `python toolbox/framework/scripts/validate_config.py`

See [docs/configuration-guide.md](docs/configuration-guide.md) for complete details.

### Modifying the Framework

1. Make changes in `toolbox/framework/`
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
