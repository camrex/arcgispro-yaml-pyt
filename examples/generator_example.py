"""
Example: Complete catalog workflow from discovery to generation.

This example demonstrates:
1. Creating a catalog
2. Adding sources
3. Discovering tools
4. Creating toolboxes
5. Assigning tools
6. Generating .pyt files
"""

from pathlib import Path

from src.catalog import CatalogService, DiscoveryService, GeneratorService, SourceType

# Paths
CATALOG_PATH = Path("examples/demo_catalog.yml")
SOURCE_PATH = Path("examples/sources/basic-tools")
OUTPUT_DIR = Path("examples/generated_toolboxes")

# Clean up from previous runs
if CATALOG_PATH.exists():
    CATALOG_PATH.unlink()
if OUTPUT_DIR.exists():
    for file in OUTPUT_DIR.glob("*.pyt*"):
        file.unlink()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    """Run the complete workflow."""
    print("=" * 60)
    print("ArcGIS Pro YAML-PYT Framework")
    print("Catalog to Toolbox Generation Example")
    print("=" * 60)

    # Step 1: Create catalog
    print("\n1. Creating catalog...")
    catalog_service = CatalogService(CATALOG_PATH)
    catalog_service.create_new()
    print(f"   ✓ Catalog created at {CATALOG_PATH}")

    # Step 2: Add source
    print("\n2. Adding tool source...")
    catalog_service.add_source(
        "basic-tools",
        "Basic Tools",
        SourceType.LOCAL,
        path=SOURCE_PATH,
    )
    print(f"   ✓ Added source: basic-tools ({SOURCE_PATH})")

    # Step 3: Discover tools
    print("\n3. Discovering tools...")
    discovery_service = DiscoveryService(catalog_service)
    tools, toolboxes = discovery_service.scan_source("basic-tools")
    print(f"   ✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"     - {tool.tool_id} ({tool.name})")
    print(f"   ✓ Found {len(toolboxes)} toolboxes:")
    for toolbox in toolboxes:
        print(f"     - {toolbox.toolbox_id} ({toolbox.name})")

    # Step 4: Create custom toolbox
    print("\n4. Creating custom toolbox...")
    catalog_service.add_toolbox(
        "my-spatial-tools",
        "My Spatial Analysis Tools",
        Path("my_spatial_tools.pyt"),
        "Custom toolbox with selected spatial analysis tools",
    )
    print("   ✓ Toolbox created: my-spatial-tools")

    # Step 5: Assign tools
    print("\n5. Assigning tools to toolbox...")
    catalog_service.add_tool_to_toolbox(
        "my-spatial-tools",
        "basic-tools",
        "tools/spatial_analysis/buffer_analysis",
    )
    print("   ✓ Added: buffer_analysis")

    catalog_service.add_tool_to_toolbox(
        "my-spatial-tools",
        "basic-tools",
        "tools/spatial_analysis/clip_features",
    )
    print("   ✓ Added: clip_features")

    # Step 6: Validate generation
    print("\n6. Validating toolbox...")
    generator_service = GeneratorService(catalog_service)
    is_valid, errors = generator_service.validate_toolbox("my-spatial-tools")
    if is_valid:
        print("   ✓ Toolbox is valid and ready to generate")
    else:
        print("   ✗ Toolbox has errors:")
        for error in errors:
            print(f"     - {error}")
        return

    # Step 7: Generate .pyt file
    print("\n7. Generating Python toolbox...")
    output_path = OUTPUT_DIR / "my_spatial_tools.pyt"
    generated = generator_service.generate_toolbox(
        "my-spatial-tools",
        output_path,
        generate_metadata=True,
    )
    print(f"   ✓ Generated: {generated}")
    print(f"   ✓ Metadata:  {generated.with_suffix('.pyt.xml')}")

    # Summary
    print("\n" + "=" * 60)
    print("Generation complete!")
    print("=" * 60)
    print(f"\nCatalog:  {CATALOG_PATH}")
    print(f"Toolbox:  {generated}")
    print("\nNext steps:")
    print("1. Open ArcGIS Pro")
    print(f"2. Add toolbox: {generated.absolute()}")
    print("3. Run the tools!")
    print()


if __name__ == "__main__":
    main()
