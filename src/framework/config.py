"""Pydantic schemas for YAML configuration validation."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ToolboxMetadata(BaseModel):
    """Toolbox-level metadata."""

    label: str = Field(..., description="Display name of the toolbox")
    alias: str = Field(
        ...,
        description="Internal alias for the toolbox (alphanumeric only, must start with letter)",
    )
    description: str = Field(..., description="Toolbox description")
    version: str = Field(default="1.0.0", description="Toolbox version")

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, v: str) -> str:
        """Validate alias meets ArcGIS Pro requirements."""
        if not v:
            raise ValueError("Alias cannot be empty")
        if not v[0].isalpha():
            raise ValueError("Alias must start with a letter")
        if not v.isalnum():
            raise ValueError(
                "Alias can only contain letters and numbers (no underscores or special characters)"
            )
        return v


class ToolboxDocumentation(BaseModel):
    """Toolbox-level documentation metadata for ArcGIS Pro."""

    summary: str = Field(..., description="Purpose/summary of the toolbox")
    description: str = Field(..., description="Abstract/detailed description")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    credits: str = Field(default="", description="Credits and attribution")
    use_limitations: str = Field(default="", description="Use limitations and restrictions")


class ToolReference(BaseModel):
    """Reference to a tool configuration file."""

    name: str = Field(..., description="Tool identifier (must match tool.name in config)")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    config: str = Field(..., description="Path to tool YAML config (relative to config/)")

    @field_validator("config")
    @classmethod
    def validate_config_path(cls, v: str) -> str:
        """Ensure config path uses forward slashes and .yml extension."""
        if not v.endswith(".yml"):
            raise ValueError(f"Config path must end with .yml: {v}")
        return v.replace("\\", "/")


class ToolboxConfig(BaseModel):
    """Complete toolbox configuration (toolbox.yml)."""

    toolbox: ToolboxMetadata
    tools: list[ToolReference] = Field(
        default_factory=list,
        description="List of tools to include (optional in catalog mode, required in standalone)",
    )
    documentation: ToolboxDocumentation | None = Field(
        default=None, description="Optional documentation metadata for the toolbox"
    )

    @field_validator("tools")
    @classmethod
    def validate_unique_names(cls, v: list[ToolReference]) -> list[ToolReference]:
        """Ensure tool names are unique."""
        names = [tool.name for tool in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate tool names found: {set(duplicates)}")
        return v


class FilterConfig(BaseModel):
    """Parameter filter configuration."""

    type: Literal["Range", "ValueList", "File"]
    min: float | None = None
    max: float | None = None
    values: list[str | int | float] | None = None
    fileFilters: list[str] | None = None


class ParameterConfig(BaseModel):
    """Individual parameter definition."""

    name: str = Field(..., description="Parameter identifier")
    displayName: str = Field(..., description="Display name in tool dialog")
    datatype: str = Field(..., description="ArcGIS datatype (e.g., GPFeatureLayer)")
    parameterType: Literal["Required", "Optional", "Derived"]
    direction: Literal["Input", "Output"]
    index: int = Field(..., description="Parameter position (0-based index)", ge=0)
    description: str = Field(default="", description="Parameter description")
    defaultValue: str | int | float | bool | None = None
    filter: FilterConfig | None = None
    columns: list[list[str]] | None = None  # For GPValueTable
    validation: list["ValidationCheck"] | None = Field(
        default=None, description="Runtime validation checks for this parameter"
    )


class ValidationCheck(BaseModel):
    """Individual validation check."""

    type: Literal[
        "greater_than", "less_than", "min_value", "max_value", "one_of", "not_empty", "regex"
    ]
    value: float | int | str | None = None
    values: list[str | int | float] | None = None  # For one_of
    pattern: str | None = None  # For regex
    message: str | None = None


class ImplementationConfig(BaseModel):
    """Tool implementation details."""

    executeFunction: str = Field(..., description="Fully qualified execute function path")


class ParameterSyntax(BaseModel):
    """Parameter-level syntax documentation for ArcGIS Pro."""

    dialog_explanation: str = Field(..., description="Explanation for dialog/GUI usage")
    scripting_explanation: str = Field(..., description="Explanation for scripting/Python usage")


class CodeSample(BaseModel):
    """Code sample documentation."""

    title: str = Field(..., description="Code sample title")
    description: str = Field(..., description="Description of what the code does")
    code: str = Field(..., description="Actual code content")


class ToolDocumentation(BaseModel):
    """Tool documentation metadata for ArcGIS Pro XML metadata."""

    summary: str = Field(..., description="Abstract/summary of tool functionality")
    usage: str = Field(..., description="Detailed usage information and best practices")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    credits: str = Field(default="", description="Credits and attribution")
    use_limitations: str = Field(default="", description="Use limitations and restrictions")
    parameter_syntax: dict[str, ParameterSyntax] = Field(
        default_factory=dict,
        description="Parameter-level documentation keyed by parameter name",
    )
    code_samples: list[CodeSample] = Field(default_factory=list, description="Example code samples")


class ToolMetadata(BaseModel):
    """Tool-level metadata."""

    name: str = Field(..., description="Tool identifier (must match filename)")
    label: str = Field(..., description="Display name of the tool")
    description: str = Field(..., description="Tool description")
    category: str = Field(default="General", description="Tool category")
    canRunInBackground: bool = Field(default=False, description="Background execution support")


class ToolConfig(BaseModel):
    """Individual tool configuration (tools/*.yml)."""

    tool: ToolMetadata
    implementation: ImplementationConfig
    parameters: list[ParameterConfig]
    documentation: ToolDocumentation | None = Field(
        default=None, description="Optional documentation metadata for ArcGIS Pro"
    )

    @model_validator(mode="after")
    def validate_parameter_indices(self) -> "ToolConfig":
        """Ensure parameter indices are unique, start at 0, and have no gaps."""
        if not self.parameters:
            return self

        indices = [p.index for p in self.parameters]

        # Check for duplicates
        if len(indices) != len(set(indices)):
            duplicates = [idx for idx in set(indices) if indices.count(idx) > 1]
            raise ValueError(f"Duplicate parameter indices found: {duplicates}")

        # Check that indices start at 0 and have no gaps
        expected_indices = set(range(len(self.parameters)))
        actual_indices = set(indices)

        if actual_indices != expected_indices:
            missing = expected_indices - actual_indices
            extra = actual_indices - expected_indices
            msg = []
            if missing:
                msg.append(f"Missing indices: {sorted(missing)}")
            if extra:
                msg.append(
                    f"Invalid indices (should be 0-{len(self.parameters) - 1}): {sorted(extra)}"
                )
            raise ValueError("; ".join(msg))

        return self


def load_toolbox_config(config_dir: Path) -> ToolboxConfig:
    """Load and validate toolbox configuration."""
    import yaml

    toolbox_path = config_dir / "toolbox.yml"
    with open(toolbox_path) as f:
        data = yaml.safe_load(f)

    config = ToolboxConfig(**data)

    # Validate that all referenced tool configs exist
    for tool_ref in config.tools:
        tool_config_path = config_dir / tool_ref.config
        if not tool_config_path.exists():
            raise FileNotFoundError(
                f"Tool config not found: {tool_config_path} (referenced by {tool_ref.name})"
            )

    return config


def load_tool_config(config_path: Path) -> ToolConfig:
    """Load and validate individual tool configuration."""
    import yaml

    with open(config_path) as f:
        data = yaml.safe_load(f)

    config = ToolConfig(**data)

    # Validate tool name matches filename or parent directory
    # Support both legacy naming (buffer_analysis.yml) and new folder structure (buffer_analysis/tool.yml)
    if config_path.stem == "tool":
        # New folder-per-tool structure: tool name should match parent directory
        expected_name = config_path.parent.name
    else:
        # Legacy flat structure: tool name should match filename
        expected_name = config_path.stem

    if config.tool.name != expected_name:
        raise ValueError(
            f"Tool name '{config.tool.name}' doesn't match expected '{expected_name}' (from path: {config_path})"
        )

    return config
