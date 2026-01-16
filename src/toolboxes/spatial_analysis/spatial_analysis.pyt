"""ArcGIS Pro Python Toolbox - Auto-loaded from YAML."""

import sys
from pathlib import Path

# Add toolbox to path
toolbox_path = Path(__file__).parent
sys.path.insert(0, str(toolbox_path.parent))

# Import framework modules
from src.framework.factory import load_and_register_tools  # noqa: E402

# Load and register all tool classes at module level (ArcGIS Pro needs them discoverable)
try:
    _toolbox_config, _tool_classes = load_and_register_tools(toolbox_path)

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
