"""Dynamic tool class factory."""

import importlib
from pathlib import Path

from toolbox.framework.base.yaml_tool import YAMLTool
from toolbox.framework.config.schema import load_tool_config, load_toolbox_config


def create_tool_class(tool_name: str, config_path: Path, execute_func):
    """
    Dynamically create a tool class from YAML config.

    Makes debugging easier by:
    - Setting proper __module__ and __qualname__
    - Preserving execute function reference
    - Adding source location in docstring

    Args:
        tool_name: Name of the tool (must match YAML filename)
        config_path: Path to the tool's YAML configuration file
        execute_func: The execute function to call when tool runs

    Returns:
        Dynamically created tool class
    """

    # Create a proper class using class statement for correct closure
    class DynamicTool(YAMLTool):
        """Dynamically generated tool class."""

        def __init__(self):
            super().__init__(tool_name)
            # Store for debugging
            self._execute_func = execute_func
            self._config_path = config_path

        def execute(self, parameters, messages):
            """Execute tool - delegates to configured execute function."""
            try:
                # Call the actual execute function with context
                execute_func(parameters, messages, self.config)
            except Exception as e:
                # Add context to errors for easier debugging
                messages.addErrorMessage(f"Error in {self.label} (config: {config_path.name}): {e}")
                raise

    # Set class name and metadata
    class_name = f"{tool_name.title().replace('_', '')}Tool"
    DynamicTool.__name__ = class_name
    DynamicTool.__qualname__ = class_name
    DynamicTool.__module__ = "toolbox.factory"
    DynamicTool.__doc__ = (
        f"Auto-generated from: {config_path.name}\n"
        f"Execute function: {execute_func.__module__}.{execute_func.__name__}\n"
        f"Tool name: {tool_name}"
    )

    return DynamicTool


def load_and_register_tools(config_dir: Path):
    """
    Load all enabled tools from YAML configuration.

    This function handles:
    - Loading toolbox configuration
    - Creating tool classes for all enabled tools
    - Importing execute functions dynamically

    Args:
        config_dir: Path to the config directory containing toolbox.yml

    Returns:
        Tuple of (toolbox_config, list of tool classes)
    """
    tool_classes = []

    # Load toolbox configuration
    toolbox_config = load_toolbox_config(config_dir)
    print(f"Loading {len(toolbox_config.tools)} tools from config...")

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
            tool_class = create_tool_class(tool_config.tool.name, tool_config_path, execute_func)
            tool_classes.append(tool_class)

            print(f"  ✓ Registered: {tool_class.__name__} -> {tool_config.tool.label}")

        except Exception as e:
            print(f"  ✗ Error loading tool {tool_ref.name}: {e}")
            import traceback

            traceback.print_exc()

    print(f"Successfully loaded {len(tool_classes)} tool classes")
    return toolbox_config, tool_classes
