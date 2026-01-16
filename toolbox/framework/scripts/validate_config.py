"""Validate all YAML configurations."""

from pathlib import Path

from toolbox.framework.config.schema import load_tool_config, load_toolbox_config


def validate_all_configs():
    """Validate toolbox and all tool configurations."""
    config_dir = Path(__file__).parent.parent.parent / "tools" / "config"

    print("Validating toolbox configuration...")
    try:
        toolbox_config = load_toolbox_config(config_dir)
        print(f"✓ Toolbox: {toolbox_config.toolbox.label}")
        print(f"  Found {len(toolbox_config.tools)} tool references")
    except Exception as e:
        print(f"✗ Toolbox validation failed: {e}")
        return False

    print("\nValidating individual tool configurations...")
    all_valid = True
    for tool_ref in toolbox_config.tools:
        tool_config_path = config_dir / tool_ref.config
        try:
            tool_config = load_tool_config(tool_config_path)
            status = "✓ (enabled)" if tool_ref.enabled else "○ (disabled)"
            print(f"{status} {tool_ref.name}: {tool_config.tool.label}")
            print(f"      {len(tool_config.parameters)} parameters")
        except Exception as e:
            print(f"✗ {tool_ref.name}: {e}")
            all_valid = False

    if all_valid:
        print("\n✓ All configurations valid!")
    else:
        print("\n✗ Some configurations have errors")

    return all_valid


if __name__ == "__main__":
    import sys

    success = validate_all_configs()
    sys.exit(0 if success else 1)
