"""
Main Flet GUI Application for Catalog Manager

Provides a multi-tab interface for:
- Managing sources and discovering tools
- Browsing discovered tools
- Building and managing toolboxes
- Generating Python toolbox files
"""

from pathlib import Path

import flet as ft

from src.catalog import CatalogService, DiscoveryService, GeneratorService

from .components.generation_panel import GenerationPanel
from .components.sources_panel import SourcesPanel
from .components.toolbox_panel import ToolboxPanel
from .components.tools_panel import ToolsPanel


class CatalogManagerApp:
    """Main application class for the Catalog Manager GUI."""

    def __init__(self, catalog_path: Path | None = None, workspace_path: Path | None = None):
        """
        Initialize the catalog manager application.

        Args:
            catalog_path: Path to existing catalog file, or None for workspace default
            workspace_path: Path to workspace directory, or None for default
        """
        self.catalog_path = catalog_path
        self.workspace_path = workspace_path
        self.catalog_service: CatalogService | None = None
        self.discovery_service: DiscoveryService | None = None
        self.generator_service: GeneratorService | None = None

        # UI components (will be created in build)
        self.page: ft.Page | None = None
        self.sources_panel: SourcesPanel | None = None
        self.tools_panel: ToolsPanel | None = None
        self.toolbox_panel: ToolboxPanel | None = None
        self.generation_panel: GenerationPanel | None = None
        self.tabs: ft.Tabs | None = None

    def main(self, page: ft.Page):
        """
        Main entry point for the Flet application.

        Args:
            page: Flet page object
        """
        self.page = page
        page.title = "ArcGIS Pro Catalog Manager"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.window.width = 1200
        page.window.height = 800
        page.window.min_width = 900
        page.window.min_height = 600

        # Initialize services
        self._initialize_services()

        # Build UI
        self._build_ui()

        page.update()

    def _initialize_services(self):
        """Initialize or load catalog services."""
        # Initialize catalog service with workspace support
        self.catalog_service = CatalogService(
            catalog_path=self.catalog_path, workspace_path=self.workspace_path
        )

        # Try to load existing catalog, create default if needed
        try:
            self.catalog_service.load()
        except Exception:
            # Create new catalog with workspace settings
            catalog = self.catalog_service.create_new()
            self.catalog_service.save(catalog)

        # Initialize discovery and generator services
        self.discovery_service = DiscoveryService(self.catalog_service)
        self.generator_service = GeneratorService(self.catalog_service)

    def _build_ui(self):
        """Build the main user interface."""
        # Create panels
        self.sources_panel = SourcesPanel(
            catalog_service=self.catalog_service,
            discovery_service=self.discovery_service,
            on_update=self._on_catalog_update,
        )

        self.tools_panel = ToolsPanel(catalog_service=self.catalog_service)

        self.toolbox_panel = ToolboxPanel(
            catalog_service=self.catalog_service, on_update=self._on_catalog_update
        )

        self.generation_panel = GenerationPanel(
            catalog_service=self.catalog_service, generator_service=self.generator_service
        )

        # Create tabs using NavigationRail for better compatibility
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.FOLDER_OPEN, selected_icon=ft.Icons.FOLDER, label="Sources"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.BUILD_OUTLINED, selected_icon=ft.Icons.BUILD, label="Tools"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INVENTORY_2_OUTLINED,
                    selected_icon=ft.Icons.INVENTORY_2,
                    label="Toolboxes",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                    selected_icon=ft.Icons.PLAY_CIRCLE,
                    label="Generate",
                ),
            ],
            on_change=self._on_tab_change,
        )

        # Create tab content separately
        self.tab_contents = [
            ft.Container(content=self.sources_panel.build(), padding=20, expand=True),
            ft.Container(content=self.tools_panel.build(), padding=20, expand=True),
            ft.Container(content=self.toolbox_panel.build(), padding=20, expand=True),
            ft.Container(content=self.generation_panel.build(), padding=20, expand=True),
        ]

        # App bar
        app_bar = ft.AppBar(
            leading=ft.Icon(ft.Icons.APPS),
            leading_width=40,
            title=ft.Text("ArcGIS Pro Catalog Manager"),
            center_title=False,
            bgcolor=ft.Colors.BLUE_GREY_100,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.SAVE, tooltip="Save Catalog", on_click=self._on_save_catalog
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Reload Catalog",
                    on_click=self._on_reload_catalog,
                ),
                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE, tooltip="About", on_click=self._on_show_about
                ),
            ],
        )

        # Content container that changes with tab selection
        self.content_container = ft.Container(
            content=self.tab_contents[0],  # Start with first tab
            expand=True,
        )

        # Main layout with NavigationRail
        main_content = ft.Row(
            controls=[
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.content_container,
            ],
            expand=True,
        )

        self.page.add(ft.Column(controls=[app_bar, main_content], spacing=0, expand=True))

    def _on_tab_change(self, e):
        """Handle tab change events."""
        tab_index = e.control.selected_index

        # Update content container
        if self.content_container and tab_index < len(self.tab_contents):
            self.content_container.content = self.tab_contents[tab_index]
            self.content_container.update()

        # Refresh panel data when switching tabs
        if tab_index == 0:  # Sources
            self.sources_panel.refresh()
        elif tab_index == 1:  # Tools
            self.tools_panel.refresh()
        elif tab_index == 2:  # Toolboxes
            self.toolbox_panel.refresh()
        elif tab_index == 3:  # Generate
            self.generation_panel.refresh()

    def _on_catalog_update(self):
        """Called when catalog is updated - refresh all panels."""
        if self.sources_panel:
            self.sources_panel.refresh()
        if self.tools_panel:
            self.tools_panel.refresh()
        if self.toolbox_panel:
            self.toolbox_panel.refresh()
        if self.generation_panel:
            self.generation_panel.refresh()

    def _on_save_catalog(self, e):
        """Save the current catalog."""
        if self.catalog_path:
            try:
                self.catalog_service.save()
                self._show_snackbar("Catalog saved successfully", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error saving catalog: {ex}", ft.Colors.RED)
        else:
            self._show_snackbar("No file path - catalog is in memory only", ft.Colors.ORANGE)

    def _on_reload_catalog(self, e):
        """Reload the catalog from file."""
        if self.catalog_path and self.catalog_path.exists():
            try:
                self.catalog_service.load()
                self._on_catalog_update()
                self._show_snackbar("Catalog reloaded", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error reloading catalog: {ex}", ft.Colors.RED)
        else:
            self._show_snackbar("No file to reload", ft.Colors.ORANGE)

    def _on_show_about(self, e):
        """Show about dialog."""

        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("About ArcGIS Pro Catalog Manager"),
            content=ft.Column(
                controls=[
                    ft.Text("Version 0.1.0", weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("A tool for managing ArcGIS Pro Python Toolboxes"),
                    ft.Text("using YAML configuration files."),
                    ft.Text(""),
                    ft.Text("Features:", weight=ft.FontWeight.BOLD),
                    ft.Text("• Discover tools from multiple sources"),
                    ft.Text("• Build custom toolboxes"),
                    ft.Text("• Generate .pyt files automatically"),
                    ft.Text(""),
                    ft.Text("© 2026 Cameron Rex", size=12, italic=True),
                ],
                tight=True,
                spacing=5,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _show_snackbar(self, message: str, color: str = ft.Colors.BLUE):
        """Show a snackbar notification."""
        if self.page:
            snack = ft.SnackBar(content=ft.Text(message), bgcolor=color, action="OK")
            self.page.snack_bar = snack
            snack.open = True
            self.page.update()

    def run(self):
        """Run the application."""
        ft.app(target=self.main)


def launch_gui(catalog_path: Path | None = None, workspace_path: Path | None = None):
    """
    Convenience function to launch the GUI application.

    Args:
        catalog_path: Path to existing catalog file, or None for workspace default
        workspace_path: Path to workspace directory, or None for default
    """
    app = CatalogManagerApp(catalog_path, workspace_path)
    app.run()


if __name__ == "__main__":
    # Launch with default workspace
    launch_gui()
