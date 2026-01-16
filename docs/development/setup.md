# Development Setup Guide

## Environment Strategy (Hybrid Approach)

This project uses **two separate environments**:

### 1. UV Environment (Development & Unit Tests)
- **Purpose**: Linting, formatting, type checking, unit tests
- **No arcpy required**
- **Fast and lightweight**

### 2. ArcGIS Pro Environment (Integration Tests & Toolbox)
- **Purpose**: Running tools in ArcGIS Pro, integration tests with arcpy
- **Has arcpy available**
- **Location**: Your ArcGIS Pro Python environment (typically in `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\`)

## Initial Setup

### UV Environment Setup (for unit tests and development)

1. **Install UV** (if not already installed):
   ```powershell
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   See [UV documentation](https://docs.astral.sh/uv/) for other platforms.

2. **Create UV environment**:
   ```powershell
   # Create virtual environment
   uv venv
   
   # Activate it
   .venv\Scripts\Activate.ps1  # Windows PowerShell
   # or
   .venv\Scripts\activate.bat  # Windows CMD
   ```

3. **Install dependencies**:
   ```powershell
   # Core dependencies
   uv pip install pydantic>=2.5.0 pyyaml>=6.0
   
   # Development tools
   uv pip install pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 ruff>=0.1.0
   ```

### ArcGIS Pro Environment Setup (for integration tests)

1. **Locate your ArcGIS Pro Python environment**:
   - Default location: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\`
   - Or use a cloned environment if you prefer

2. **Activate the environment**:
   ```powershell
   # Using conda (from ArcGIS Pro Python Command Prompt)
   conda activate arcgispro-py3
   
   # Or use full path
   conda activate "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3"
   ```

3. **Install dependencies**:
   ```powershell
   # Core dependencies
   pip install pydantic>=2.5.0 pyyaml>=6.0
   
   # Development tools (optional, for running tests in this environment)
   pip install pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 ruff>=0.1.0
   ```

## Development Commands

### Using UV Environment (Recommended for daily development)

```powershell
# Activate UV environment
.venv\Scripts\activate

# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues automatically
ruff check . --fix

# Run unit tests only (fast, no arcpy)
pytest tests/ -m unit

# Run all tests you can (unit tests)
pytest tests/ -v
```

### Using ArcGIS Pro Environment (For integration tests)

```powershell
# Activate your ArcGIS Pro environment (adjust path as needed)
conda activate arcgispro-py3

# Run integration tests (requires arcpy)
python -m pytest tests/ -m slow

# Run all tests (unit + integration)
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=toolbox --cov-report=html
```

### Validation

```powershell
# Validate YAML configurations (either environment)
# UV environment:
.venv\Scripts\activate
$env:PYTHONPATH = "$PWD"; python src/framework/scripts/validate_config.py

# Or ArcGIS Pro environment:
$env:PYTHONPATH = "$PWD"; python src/framework/scripts/validate_config.py
```

## Using the Toolbox in ArcGIS Pro

1. Open ArcGIS Pro
2. In the Catalog pane, right-click **Toolboxes**
3. Select **Add Toolbox**
4. Navigate to `src/yaml_toolbox.pyt`
### UV Environment (.venv/)
- **Use for**: Daily development, linting, formatting, unit tests
- **Advantages**: Fast, lightweight, doesn't require ArcGIS Pro
- **Limitations**: No arcpy, can't run integration tests
- **Activate**: `.venv\Scripts\activate`

### ArcGIS Pro Environment
- **Use for**: Running tools in ArcGIS Pro, integration tests
- **Advantages**: Has arcpy, matches production environment
- **Limitations**: Slower, requires ArcGIS Pro installation
- **Activate**: `conda activate arcgispro-py3` (or your environment name)

### When to Use Which

| Task | Environment |
|------|-------------|
| Code formatting | UV (`.venv`) |
| Linting | UV (`.venv`) |
| Type checking | UV (`.venv`) |
| Unit tests (`@pytest.mark.unit`) | UV (`.venv`) |
| Integration tests (`@pytest.mark.slow`) | ArcGIS Pro |
| Running tools in ArcGIS Pro | ArcGIS Pro |
| YAML validation | Either |
- `src/tools/` - Tool utilities (business logic)
- `src/utils/` - Business logic
- `src/helpers/` - Reusable utilities
- `src/models/` - Pydantic validation models
- `tests/` - Test suite

## VS Code Tasks

Available tasks (Ctrl+Shift+P → "Tasks: Run Task"):
- Lint with Ruff
- Format with Ruff
- Run Tests
- Test with Coverage
- Validate YAML Config

## Environment Notes

**ArcGIS Pro Python Environment:**
- Use for running tools in ArcGIS Pro
- Use for integration tests (with arcpy)
- Required for arcpy imports

**Testing:**
- Unit tests (`@pytest.mark.unit`) - No arcpy required, run anywhere
- Integration tests (`@pytest.mark.slow`) - Requires arcpy, run in ArcGIS Pro environment

## Common Issues

**Import errors with arcpy:**
- Ensure ArcGIS Pro environment is activated
- VS Code should use the ArcGIS Pro Python interpreter (see .vscode/settings.json)

**Tests fail:**
- Run unit tests only: `pytest tests/ -m unit`
- Integration tests require ArcGIS Pro environment

**YAML validation fails:**
- Check YAML syntax in config files
- Ensure parameter mappings match parameters
- Run: `python src/scripts/validate_config.py`

