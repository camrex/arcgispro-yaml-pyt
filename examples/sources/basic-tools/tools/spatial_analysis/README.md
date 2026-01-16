# Spatial Analysis Toolset

This folder demonstrates a **toolset pattern** - a collection of related tools that share common functionality through helpers.

## Structure

```
spatial_analysis/
├── buffer_analysis/      # Buffer tool
├── clip_features/        # Clip tool
└── helpers/              # Shared utilities (spatial reference checks, etc.)
```

## Pattern: Related Tools with Shared Helpers

When you have multiple tools that:
- Operate in the same domain (e.g., spatial analysis)
- Share common operations
- Naturally belong together

You can organize them as a **toolset** with shared helpers.

## Contrast with Standalone Tools

Compare this to `load_tool_metadata/` which is a **standalone tool** with no helpers. That tool is self-contained and doesn't need to share code with others.

## Usage

Tools in this set can import from the shared helpers:

```python
from src.tools.spatial_analysis.helpers.geoprocessing import (
    check_spatial_reference,
    get_feature_count
)
```

