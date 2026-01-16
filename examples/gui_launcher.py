"""
Launch the ArcGIS Pro Catalog Manager GUI

This script demonstrates how to launch the Flet-based GUI for managing
tool catalogs, discovering tools, building toolboxes, and generating .pyt files.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gui import CatalogManagerApp


def main():
    """Launch the Catalog Manager GUI."""
    print("=" * 60)
    print("ArcGIS Pro Catalog Manager GUI")
    print("=" * 60)
    print()
    print("Starting application...")
    print()

    # Option 1: Create a new in-memory catalog
    # app = CatalogManagerApp()

    # Option 2: Use a specific catalog file
    catalog_path = Path("examples/demo_catalog.yml")

    if catalog_path.exists():
        print(f"Loading catalog: {catalog_path}")
    else:
        print(f"Creating new catalog: {catalog_path}")

    app = CatalogManagerApp(catalog_path)

    print()
    print("=" * 60)
    print("GUI Features:")
    print("  • Sources Tab: Add sources and scan for tools")
    print("  • Tools Tab: Browse discovered tools")
    print("  • Toolboxes Tab: Create and manage toolboxes")
    print("  • Generate Tab: Generate .pyt files")
    print("=" * 60)
    print()

    # Run the application
    app.run()


if __name__ == "__main__":
    main()
