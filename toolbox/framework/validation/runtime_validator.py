"""Runtime validation from YAML configuration."""

import re
from typing import Any

from toolbox.framework.config.schema import ToolConfig, ValidationCheck


class ValidationError(Exception):
    """Raised when runtime validation fails."""

    pass


def validate_parameter(param_name: str, value: Any, config: ToolConfig, messages=None) -> None:
    """
    Validate a parameter value against rules defined in YAML.

    Args:
        param_name: Parameter name to validate
        value: The value to validate
        config: Tool configuration containing validation rules
        messages: Optional ArcGIS messages object for warnings

    Raises:
        ValidationError: If validation fails
    """
    # Find parameter config with this name
    param_config = next(
        (p for p in config.parameters if p.name == param_name),
        None,
    )

    if not param_config or not param_config.validation:
        return

    # Run each validation check
    for check in param_config.validation:
        _run_check(param_name, value, check, messages)


def _run_check(param_name: str, value: Any, check: ValidationCheck, messages=None) -> None:
    """Run a single validation check."""
    error_msg = check.message or f"Validation failed for {param_name}"

    if check.type == "greater_than":
        if value is None or value <= check.value:
            raise ValidationError(f"{error_msg} (must be > {check.value}, got {value})")

    elif check.type == "less_than":
        if value is None or value >= check.value:
            raise ValidationError(f"{error_msg} (must be < {check.value}, got {value})")

    elif check.type == "min_value":
        if value is None or value < check.value:
            raise ValidationError(f"{error_msg} (must be >= {check.value}, got {value})")

    elif check.type == "max_value":
        if value is None or value > check.value:
            raise ValidationError(f"{error_msg} (must be <= {check.value}, got {value})")

    elif check.type == "one_of":
        if value not in check.values:
            raise ValidationError(f"{error_msg} (must be one of {check.values}, got {value})")

    elif check.type == "not_empty":
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{error_msg} (value cannot be empty)")

    elif check.type == "regex":
        if not isinstance(value, str) or not check.pattern or not re.match(check.pattern, value):
            raise ValidationError(f"{error_msg} (must match pattern {check.pattern})")


def validate_all_parameters(parameters, config: ToolConfig, messages=None) -> None:
    """
    Validate all parameters with rules defined in YAML.

    Args:
        parameters: ArcGIS tool parameters
        config: Tool configuration containing validation rules
        messages: Optional ArcGIS messages object

    Raises:
        ValidationError: If any validation fails
    """
    # Iterate through parameter configs with validation rules
    for param_config in config.parameters:
        if not param_config.validation:
            continue

        param = parameters[param_config.index]

        # Use .value for proper type (numbers, booleans)
        # ArcGIS automatically converts to correct Python type
        value = param.value

        for check in param_config.validation:
            _run_check(param_config.name, value, check, messages)
