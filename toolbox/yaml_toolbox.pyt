"""ArcGIS Pro Python Toolbox - Auto-loaded from YAML."""

import importlib
import sys
from pathlib import Path

# Add toolbox to path
toolbox_path = Path(__file__).parent
sys.path.insert(0, str(toolbox_path.parent))

# Import after path setup to ensure module can be found
from toolbox.framework import factory  # noqa: E402
from toolbox.framework.base import yaml_tool  # noqa: E402
from toolbox.framework.config import schema  # noqa: E402

# Force reload modules when toolbox is refreshed (important for development)
importlib.reload(schema)
importlib.reload(yaml_tool)
importlib.reload(factory)

# Import function after reload
from toolbox.framework.factory import load_and_register_tools  # noqa: E402

# Load and register all tool classes at module level (ArcGIS Pro needs them discoverable)
try:
    _toolbox_config, _tool_classes = load_and_register_tools(toolbox_path / "tools" / "config")

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

        # Reference the pre-loaded tool classes (critical for ArcGIS Pro discovery)
        self.tools = _tool_classes

        print(f"Toolbox initialized: {len(self.tools)} tools -> {[t.__name__ for t in self.tools]}")
