"""Sources Panel - Manage tool sources and trigger discovery."""

from collections.abc import Callable
from pathlib import Path

import flet as ft

from src.catalog import CatalogService, DiscoveryService
from src.catalog.models import SourceType
from src.gui.utils import show_snack_bar


class SourcesPanel:
    """Panel for managing tool sources and discovering tools."""

    def __init__(
        self,
        catalog_service: CatalogService,
        discovery_service: DiscoveryService,
        on_update: Callable | None = None,
    ):
        """
        Initialize the sources panel.

        Args:
            catalog_service: Catalog service instance
            discovery_service: Discovery service instance
            on_update: Callback when catalog is updated
        """
        self.catalog_service = catalog_service
        self.discovery_service = discovery_service
        self.on_update = on_update

        # UI components
        self.sources_list: ft.Column | None = None
        self.page: ft.Page | None = None

    def build(self) -> ft.Control:
        """Build the sources panel UI."""
        # Header with add button
        header = ft.Row(
            controls=[
                ft.Text("Tool Sources", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Source", icon=ft.Icons.ADD, on_click=self._on_add_source),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Sources list
        self.sources_list = ft.Column(
            controls=[], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True
        )

        # Initial load
        self.refresh()

        return ft.Column(
            controls=[header, ft.Divider(), self.sources_list], expand=True, spacing=20
        )

    def refresh(self):
        """Refresh the sources list."""
        if not self.sources_list:
            return

        sources = {s.id: s for s in self.catalog_service.list_sources()}
        self.sources_list.controls.clear()

        if not sources:
            self.sources_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY),
                            ft.Text(
                                "No sources configured",
                                size=16,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Add a source to discover tools",
                                size=12,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        else:
            for source in sources.values():
                self.sources_list.controls.append(self._build_source_card(source))

        # Only update if already added to page
        try:
            if self.sources_list.page:
                self.sources_list.update()
        except RuntimeError:
            # Control not yet added to page - that's okay during init
            pass

    def _build_source_card(self, source) -> ft.Card:
        """Build a card for a source."""
        # Source type badge
        type_colors = {
            SourceType.LOCAL: ft.Colors.BLUE,
            SourceType.GIT: ft.Colors.PURPLE,
            SourceType.NETWORK: ft.Colors.ORANGE,
        }

        type_badge = ft.Container(
            content=ft.Text(
                source.type.value.upper(),
                size=10,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=type_colors.get(source.type, ft.Colors.GREY),
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        # Tool counts
        tools_discovered = source.discovered_tools or 0

        # Last scan info
        last_scan = "Never" if not source.last_sync else source.last_sync.strftime("%Y-%m-%d %H:%M")

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.FOLDER, size=32),
                                ft.Column(
                                    controls=[
                                        ft.Text(source.name, size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text(str(source.path), size=12, color=ft.Colors.GREY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                type_badge,
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Tools Discovered", size=10, color=ft.Colors.GREY),
                                        ft.Text(
                                            str(tools_discovered),
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.VerticalDivider(),
                                ft.Column(
                                    controls=[
                                        ft.Text("Last Scan", size=10, color=ft.Colors.GREY),
                                        ft.Text(last_scan, size=12),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Scan",
                                    icon=ft.Icons.SEARCH,
                                    on_click=lambda e, src=source: self._on_scan_source(e, src),
                                ),
                                ft.OutlinedButton(
                                    "Edit",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, src=source: self._on_edit_source(e, src),
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED,
                                    tooltip="Delete Source",
                                    on_click=lambda e, src=source: self._on_delete_source(e, src),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

    def _on_add_source(self, e):
        """Handle add source button click."""
        page = e.page if hasattr(e, "page") else e.control.page
        self.page = page

        # Input fields
        name_field = ft.TextField(label="Source Name", hint_text="e.g., my-tools", autofocus=True)

        type_dropdown = ft.Dropdown(
            label="Source Type",
            options=[
                ft.dropdown.Option("local", "Local Folder"),
                ft.dropdown.Option("git", "Git Repository"),
                ft.dropdown.Option("network", "Network Path"),
            ],
            value="local",
        )

        path_field = ft.TextField(
            label="Path/URL", hint_text="Path to tools directory", expand=True
        )

        def pick_folder(e):
            def on_result(e: ft.FilePickerResultEvent):
                if e.path:
                    path_field.value = e.path
                    path_field.update()

            file_picker = ft.FilePicker(on_result=on_result)
            page.overlay.append(file_picker)
            page.update()
            file_picker.get_directory_path()

        browse_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN, tooltip="Browse", on_click=pick_folder
        )

        def close_dlg(e):
            dlg.open = False
            page.update()

        def save_source(e):
            # Validate inputs
            if not name_field.value:
                name_field.error_text = "Name is required"
                name_field.update()
                return

            if not path_field.value:
                path_field.error_text = "Path is required"
                path_field.update()
                return

            try:
                # Add source to catalog
                source_type = SourceType(type_dropdown.value)
                self.catalog_service.add_source(
                    id=name_field.value,
                    name=name_field.value,
                    type=source_type,
                    path=Path(path_field.value),
                )

                # Close dialog and refresh
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                # Show success message
                show_snack_bar(page, f"Added source: {name_field.value}", ft.Colors.GREEN)
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar = snack_bar
                snack_bar.open = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Tool Source"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        name_field,
                        type_dropdown,
                        ft.Row(controls=[path_field, browse_button], spacing=5),
                    ],
                    tight=True,
                    spacing=15,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Add Source", on_click=save_source),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _on_scan_source(self, e, source):
        """Handle scan source button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        # Show progress dialog
        progress_text = ft.Text("Scanning source...")
        progress_ring = ft.ProgressRing()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Discovering Tools"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        progress_ring,
                        progress_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                width=300,
                padding=20,
            ),
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

        try:
            # Perform discovery
            result = self.discovery_service.scan_source(source.id)

            # Close progress dialog
            dlg.open = False
            page.update()

            # Refresh UI
            self.refresh()
            if self.on_update:
                self.on_update()

            # Show results
            show_snack_bar(
                page,
                f"Found {result.tools_found} tools and {result.toolboxes_found} toolboxes",
                ft.Colors.GREEN,
            )
        except Exception as ex:
            dlg.open = False
            page.update()
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Error scanning source: {ex}"), bgcolor=ft.Colors.RED
            )
            page.snack_bar = snack_bar
            snack_bar.open = True
            page.update()

    def _on_edit_source(self, e, source):
        """Handle edit source button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        # Create form fields pre-populated with current values
        name_field = ft.TextField(
            label="Source Name", value=source.name, hint_text="e.g., my-tools", autofocus=True
        )

        type_dropdown = ft.Dropdown(
            label="Source Type",
            value=source.type.value,
            options=[
                ft.dropdown.Option("local", "Local Folder"),
                ft.dropdown.Option("git", "Git Repository"),
                ft.dropdown.Option("network", "Network Path"),
            ],
        )

        # Set initial path/URL value
        initial_path = ""
        if source.type == SourceType.GIT and source.url:
            initial_path = source.url
        elif source.path:
            initial_path = str(source.path)

        path_field = ft.TextField(
            label="Path/URL", value=initial_path, hint_text="Path to tools directory", expand=True
        )

        # Git-specific fields
        branch_field = ft.TextField(
            label="Branch (Git only)",
            value=source.branch or "main",
            hint_text="Git branch name",
        )

        enabled_checkbox = ft.Checkbox(label="Enabled", value=source.enabled)

        def close_dlg(e):
            dlg.open = False
            page.update()

        def save_changes(e):
            # Validate inputs
            if not name_field.value:
                name_field.error_text = "Name is required"
                name_field.update()
                return

            if not path_field.value:
                path_field.error_text = "Path is required"
                path_field.update()
                return

            try:
                # Update source properties
                source_type = SourceType(type_dropdown.value)

                # Update the source object
                source.name = name_field.value
                source.type = source_type
                source.enabled = enabled_checkbox.value

                if source_type == SourceType.GIT:
                    source.url = path_field.value
                    source.branch = branch_field.value or "main"
                    source.path = None
                else:
                    source.path = Path(path_field.value)
                    source.url = None
                    source.branch = None

                # Save catalog
                self.catalog_service.save()

                # Close dialog and refresh
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                # Show success message
                show_snack_bar(page, f"Updated source: {source.name}", ft.Colors.GREEN)
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar = snack_bar
                snack_bar.open = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Edit Source: {source.name}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        name_field,
                        type_dropdown,
                        path_field,
                        branch_field,
                        enabled_checkbox,
                    ],
                    tight=True,
                    spacing=15,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Save Changes", on_click=save_changes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _on_delete_source(self, e, source):
        """Handle delete source button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        def close_dlg(e):
            dlg.open = False
            page.update()

        def confirm_delete(e):
            try:
                self.catalog_service.remove_source(source.id)
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                snack_bar = ft.SnackBar(
                    content=ft.Text(f"Deleted source: {source.name}"), bgcolor=ft.Colors.GREEN
                )
                page.snack_bar = snack_bar
                snack_bar.open = True
                page.update()
            except Exception as ex:
                error_snack = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar = error_snack
                error_snack.open = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Source?"),
            content=ft.Text(
                f"Are you sure you want to delete '{source.name}'?\n\n"
                "This will remove the source and all discovered tools from the catalog."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton(
                    "Delete", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=confirm_delete
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()
