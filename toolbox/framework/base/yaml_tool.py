"""Base class for YAML-configured tools."""

from pathlib import Path

import arcpy

from toolbox.framework.config.schema import ToolConfig, load_tool_config


class YAMLTool:
    """Base class for tools configured via YAML."""

    def __init__(self, tool_name: str):
        """
        Initialize tool from YAML configuration.

        Args:
            tool_name: Name of the tool (must match YAML filename without extension)
        """
        self.tool_name = tool_name

        # Load tool configuration from individual YAML file
        toolbox_path = Path(__file__).parent.parent.parent  # Go up to toolbox/
        config_path = toolbox_path / "tools" / "config" / "tools" / f"{tool_name}.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Tool config not found: {config_path}")

        # Load and validate config
        self.config: ToolConfig = load_tool_config(config_path)

        # Set tool properties from YAML
        self.label = self.config.tool.label
        self.description = self.config.tool.description
        self.category = self.config.tool.category
        self.canRunInBackground = self.config.tool.canRunInBackground

    def getParameterInfo(self):
        """Build parameters from YAML configuration."""
        # Sort parameters by index to ensure correct order
        sorted_params = sorted(self.config.parameters, key=lambda p: p.index)

        parameters = []

        for param_config in sorted_params:
            # Create parameter
            param = arcpy.Parameter(
                name=param_config.name,
                displayName=param_config.displayName,
                datatype=param_config.datatype,
                parameterType=param_config.parameterType,
                direction=param_config.direction,
            )

            # Set default value
            if param_config.defaultValue is not None:
                param.value = param_config.defaultValue

            # Set filter if provided
            if param_config.filter:
                filter_config = param_config.filter
                if filter_config.type == "Range":
                    param.filter.type = "Range"  # type: ignore
                    param.filter.list = [filter_config.min, filter_config.max]  # type: ignore
                elif filter_config.type == "ValueList":
                    param.filter.type = "ValueList"  # type: ignore
                    param.filter.list = filter_config.values  # type: ignore
                elif filter_config.type == "File":
                    param.filter.list = filter_config.fileFilters  # type: ignore

            # Set columns for ValueTable
            if param_config.columns:
                param.columns = param_config.columns

            parameters.append(param)

        return parameters

    def execute(self, parameters, messages):
        """Execute tool - must be overridden by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute() method")
