# Testing Guide

## Python Environments

This project requires different Python environments for different purposes:

### 1. Development Environment (UV)

**Purpose**: Development, unit testing, linting, type checking

**Location**: `.venv/` directory

**Setup**:
```powershell
# Create and activate UV environment
uv venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install pydantic>=2.5.0 pyyaml>=6.0
uv pip install pytest>=7.4.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 ruff>=0.1.0
```

**Contains**:
- Pydantic (schema validation)
- PyYAML (configuration loading)
- pytest, pytest-cov, pytest-mock (testing)
- ruff (linting/formatting)
- ty (type checking)

**Does NOT contain**:
- arcpy (ArcGIS Pro's proprietary module)

### 2. ArcGIS Pro Environment

**Purpose**: Integration testing with real arcpy, running toolbox in ArcGIS Pro

**Location**: ArcGIS Pro's Python installation (typically `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\`)

**Setup**: Installed with ArcGIS Pro

**Contains**:
- arcpy and all ArcGIS Pro Python modules
- May need to install dev dependencies:
  ```powershell
  # From ArcGIS Pro Python Command Prompt
  conda install pytest pytest-cov pytest-mock ruff
  ```

## Running Tests

### Unit Tests (No arcpy required)

Use the UV environment for unit tests. Tests are marked with `@pytest.mark.unit` and use mocked arcpy:

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run all tests (arcpy is mocked in conftest.py)
pytest tests/ -v

# Run only unit tests
pytest tests/ -v -m unit

# Run with coverage
pytest tests/ --cov=toolbox --cov-report=html
```

**How arcpy mocking works**:
- `tests/conftest.py` installs a mock arcpy module in `sys.modules['arcpy']` before any test imports
- This allows tests to import `toolbox.utils.buffer`, `toolbox.utils.clip`, etc. without requiring real arcpy
- The mock provides test doubles for `arcpy.Parameter`, `arcpy.analysis.Buffer`, etc.

### Integration Tests (Real arcpy required)

Use the ArcGIS Pro environment for integration tests marked with `@pytest.mark.slow`:

```powershell
# Option 1: From ArcGIS Pro Python Command Prompt
cd E:\DevProjects\rmi-agp-pytoolbox-yaml
pytest tests/ -v -m slow

# Option 2: Specify full path to ArcGIS Pro Python
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pytest tests/ -v -m slow
```

## Test Structure

### Auto-Discovery

Tests automatically discover all tools and toolboxes:

```python
# tests/conftest.py provides dynamic fixtures
def test_all_tools_have_valid_config(all_tools):
    """Validates ALL discovered tools automatically."""
    for tool_path, tool_name in all_tools:
        config_path = tool_path / "tool.yml"
        assert config_path.exists()
        # Validate...

# Factory fixtures for specific tools
def test_buffer_tool(get_tool):
    tool_path = get_tool("spatial_analysis/buffer_analysis")
    # Test specific tool...
```

**Benefits:**
- Add new tool → automatically tested
- No hardcoded fixture updates needed
- Validates ALL tools consistently

### Test Markers

```python
@pytest.mark.unit     # Unit tests - use mocked arcpy
@pytest.mark.slow     # Integration tests - require real arcpy
```

### Example Unit Test

```python
import pytest

def test_buffer_validation(mock_arcpy):
    """Test parameter validation logic - no real arcpy needed."""
    from src.utils.buffer import execute_buffer
    # Test validation logic with mocked arcpy
```

### Example Integration Test

```python
import pytest

@pytest.mark.slow
def test_buffer_with_real_data():
    """Test buffer with real ArcGIS Pro data - requires arcpy."""
    import arcpy  # Real arcpy, not mocked
    # Test with real feature classes
```

## Validation

### YAML Configuration Validation

Validates toolbox and tool YAML files against Pydantic schemas:

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Run validation script
python src/scripts/validate_config.py
```

This checks:
- Schema compliance (required fields, types, constraints)
- Parameter index uniqueness and continuity
- Validation rule syntax
- Implementation function references

## Linting and Type Checking

Both work in the UV environment (no arcpy needed):

```powershell
# Activate UV environment
.\.venv\Scripts\Activate.ps1

# Lint with Ruff
ruff check .

# Format with Ruff
ruff format .

# Type check with ty
ty .
```

## VS Code Tasks

The workspace includes pre-configured tasks (use `Ctrl+Shift+B`):

- **Lint with Ruff**: `ruff check .`
- **Format with Ruff**: `ruff format .`
- **Type Check with ty**: `ty .`
- **Run Tests**: `pytest tests/ -v`
- **Test with Coverage**: `pytest tests/ --cov=toolbox --cov-report=html`
- **Validate YAML Config**: `python src/scripts/validate_config.py`

All tasks except integration tests use the UV environment.

## Troubleshooting

### "ModuleNotFoundError: No module named 'pydantic'"

**Problem**: Running tests without activating UV environment

**Solution**: 
```powershell
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

### "ModuleNotFoundError: No module named 'arcpy'" in production

**Problem**: Trying to run toolbox in UV environment

**Solution**: Toolbox must run in ArcGIS Pro's Python environment (happens automatically when loaded in ArcGIS Pro)

### Tests fail with real arcpy errors

**Problem**: Integration tests running without ArcGIS Pro environment

**Solution**: Use ArcGIS Pro's Python for integration tests:
```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pytest tests/ -v -m slow
```

## Summary

| Task | Environment | Command |
|------|-------------|---------|
| Unit tests | UV (.venv) | `pytest tests/ -v` |
| Integration tests | ArcGIS Pro | `pytest tests/ -v -m slow` (from AGP prompt) |
| Linting/formatting | UV (.venv) | `ruff check .` / `ruff format .` |
| Type checking | UV (.venv) | `ty .` |
| Validation | UV (.venv) | `python src/scripts/validate_config.py` |
| Run toolbox | ArcGIS Pro | Load `.pyt` file in ArcGIS Pro |

