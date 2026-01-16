"""Validate all YAML configurations."""

from pathlib import Path

from src.framework.schema import load_tool_config, load_toolbox_config


def validate_all_configs():
    """Validate all toolbox and tool configurations."""
    # Get src directory
    src_dir = Path(__file__).parent.parent / "src"
    toolboxes_dir = src_dir / "toolboxes"

    print("Validating toolbox configurations...")
    print("=" * 60)
    
    all_valid = True
    
    # Find all toolboxes
    toolboxes = [d for d in toolboxes_dir.iterdir() if d.is_dir() and (d / "toolbox.yml").exists()]
    
    if not toolboxes:
        print("✗ No toolboxes found!")
        return False
    
    for toolbox_dir in toolboxes:
        print(f"\nToolbox: {toolbox_dir.name}")
        print("-" * 60)
        
        try:
            toolbox_config = load_toolbox_config(toolbox_dir)
            print(f"✓ {toolbox_config.toolbox.label} ({toolbox_config.toolbox.alias})")
            print(f"  Version: {toolbox_config.toolbox.version}")
            print(f"  Tools: {len(toolbox_config.tools)} registered")
            
            # Validate each tool referenced in this toolbox
            for tool_ref in toolbox_config.tools:
                # config path is relative to the toolbox.yml file
                tool_config_path = toolbox_dir / tool_ref.config
                
                try:
                    tool_config = load_tool_config(tool_config_path)
                    status = "✓" if tool_ref.enabled else "○"
                    enabled_text = "enabled" if tool_ref.enabled else "disabled"
                    print(f"    {status} {tool_ref.name} ({enabled_text})")
                    print(f"       Label: {tool_config.tool.label}")
                    print(f"       Parameters: {len(tool_config.parameters)}")
                except Exception as e:
                    print(f"    ✗ {tool_ref.name}: {e}")
                    all_valid = False
                    
        except Exception as e:
            print(f"✗ Toolbox validation failed: {e}")
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All configurations valid!")
    else:
        print("✗ Some configurations have errors")

    return all_valid


if __name__ == "__main__":
    import sys

    success = validate_all_configs()
    sys.exit(0 if success else 1)
