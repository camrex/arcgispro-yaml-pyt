"""Toolbox Panel - Build and manage toolboxes."""

from collections.abc import Callable
from pathlib import Path

import flet as ft

from src.catalog import CatalogService
from src.gui.utils import show_snack_bar


class ToolboxPanel:
    """Panel for building and managing toolboxes."""

    def __init__(self, catalog_service: CatalogService, on_update: Callable | None = None):
        """
        Initialize the toolbox panel.

        Args:
            catalog_service: Catalog service instance
            on_update: Callback when catalog is updated
        """
        self.catalog_service = catalog_service
        self.on_update = on_update

        # UI components
        self.toolbox_list: ft.Column | None = None

    def build(self) -> ft.Control:
        """Build the toolbox panel UI."""
        # Header with add button
        header = ft.Row(
            controls=[
                ft.Text("Toolboxes", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Create Toolbox", icon=ft.Icons.ADD, on_click=self._on_create_toolbox
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Toolbox list
        self.toolbox_list = ft.Column(
            controls=[], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )

        # Initial load
        self.refresh()

        return ft.Column(
            controls=[header, ft.Divider(), self.toolbox_list], expand=True, spacing=20
        )

    def refresh(self):
        """Refresh the toolbox list."""
        if not self.toolbox_list:
            return

        toolboxes = {t.id: t for t in self.catalog_service.list_toolboxes()}
        self.toolbox_list.controls.clear()

        if not toolboxes:
            self.toolbox_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2, size=64, color=ft.Colors.GREY),
                            ft.Text(
                                "No toolboxes created",
                                size=16,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Create a toolbox to organize your tools",
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
            for toolbox in toolboxes.values():
                self.toolbox_list.controls.append(self._build_toolbox_card(toolbox))

        try:
            if self.toolbox_list and self.toolbox_list.page:
                self.toolbox_list.update()
        except (RuntimeError, AttributeError):
            pass

    def _build_toolbox_card(self, toolbox) -> ft.Card:
        """Build a card for a toolbox."""
        tool_count = len(toolbox.tools) if toolbox.tools else 0

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INVENTORY_2, size=32, color=ft.Colors.PURPLE),
                                ft.Column(
                                    controls=[
                                        ft.Text(toolbox.name, size=18, weight=ft.FontWeight.BOLD),
                                        ft.Text(str(toolbox.path), size=12, color=ft.Colors.GREY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Text(
                            toolbox.description or "No description",
                            size=13,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"{tool_count} tool{'s' if tool_count != 1 else ''}",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Manage Tools",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, tb=toolbox: self._on_manage_tools(e, tb),
                                ),
                                ft.OutlinedButton(
                                    "Edit",
                                    icon=ft.Icons.SETTINGS,
                                    on_click=lambda e, tb=toolbox: self._on_edit_toolbox(e, tb),
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED,
                                    tooltip="Delete Toolbox",
                                    on_click=lambda e, tb=toolbox: self._on_delete_toolbox(e, tb),
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

    def _on_create_toolbox(self, e):
        """Handle create toolbox button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        # Input fields
        name_field = ft.TextField(
            label="Toolbox Name", hint_text="e.g., My Spatial Analysis Tools", autofocus=True
        )

        id_field = ft.TextField(label="Toolbox ID", hint_text="e.g., my-spatial-tools")

        name_field = ft.TextField(label="Name", hint_text="e.g., My Spatial Tools", autofocus=True)

        output_field = ft.TextField(
            label="Output Filename", hint_text="e.g., my_tools.pyt", value=".pyt"
        )

        description_field = ft.TextField(
            label="Description",
            hint_text="Describe this toolbox...",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        def close_dlg(e):
            dlg.open = False
            page.update()

        def create_toolbox(e):
            # Validate inputs
            if not name_field.value:
                name_field.error_text = "Name is required"
                name_field.update()
                return

            if not id_field.value:
                id_field.error_text = "Toolbox ID is required"
                id_field.update()
                return

            if not output_field.value:
                output_field.error_text = "Output filename is required"
                output_field.update()
                return

            try:
                # Create toolbox
                self.catalog_service.add_toolbox(
                    id=id_field.value,
                    path=Path(output_field.value),
                    name=name_field.value,
                    description=description_field.value or None,
                )

                # Close dialog and refresh
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                # Show success message
                show_snack_bar(page, f"Created toolbox: {name_field.value}", ft.Colors.GREEN)
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar = snack_bar
                snack_bar.open = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Toolbox"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        id_field,
                        name_field,
                        output_field,
                        description_field,
                    ],
                    tight=True,
                    spacing=15,
                ),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Create", on_click=create_toolbox),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _on_manage_tools(self, e, toolbox):
        """Handle manage tools button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        # Get all tools from all toolboxes as available tools
        toolboxes = self.catalog_service.list_toolboxes()
        sources = {s.id: s for s in self.catalog_service.list_sources()}

        available_tools = {}

        # Collect all tools that are currently in any toolbox
        for tb in toolboxes:
            for tool_ref in tb.tools:
                if tool_ref.source_id in sources:
                    source = sources[tool_ref.source_id]
                    tool_key = f"{tool_ref.source_id}:{tool_ref.tool_path}"
                    tool_name = tool_ref.alias or tool_ref.tool_path.split("/")[-1]
                    available_tools[tool_key] = {
                        "tool_ref": tool_ref,
                        "source": source,
                        "display_name": f"{tool_name} ({source.name})",
                    }

        if not available_tools:
            # Show message if no tools found
            snack_bar = ft.SnackBar(
                content=ft.Text("No tools found. Add sources and scan for tools first."),
                bgcolor=ft.Colors.ORANGE,
            )
            page.snack_bar = snack_bar
            snack_bar.open = True
            page.update()
            return

        # Current toolbox tools (by key)
        current_tool_keys = (
            {f"{tr.source_id}:{tr.tool_path}" for tr in toolbox.tools} if toolbox.tools else set()
        )

        # Create checkboxes for each available tool
        tool_checkboxes = []
        for tool_key, tool_data in sorted(
            available_tools.items(), key=lambda x: x[1]["display_name"]
        ):
            checkbox = ft.Checkbox(
                label=tool_data["display_name"],
                value=tool_key in current_tool_keys,
                data=tool_key,
            )
            tool_checkboxes.append(checkbox)

        def close_dlg(e):
            dlg.open = False
            page.update()

        def save_tools(e):
            try:
                # Get selected tool keys
                selected_tool_keys = {cb.data for cb in tool_checkboxes if cb.value}

                # Clear current tools and rebuild from selection
                toolbox.tools.clear()

                # Add selected tools back
                for tool_key in selected_tool_keys:
                    if tool_key in available_tools:
                        tool_data = available_tools[tool_key]
                        original_tool_ref = tool_data["tool_ref"]

                        # Create new ToolReference for this toolbox
                        from src.catalog.models import ToolReference

                        new_tool_ref = ToolReference(
                            source_id=original_tool_ref.source_id,
                            tool_path=original_tool_ref.tool_path,
                            enabled=True,
                            alias=original_tool_ref.alias,
                        )
                        toolbox.tools.append(new_tool_ref)

                self.catalog_service.save()

                # Close dialog and refresh
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                # Show success message
                show_snack_bar(page, f"Updated tools for {toolbox.name}", ft.Colors.GREEN)
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar = snack_bar
                snack_bar.open = True
                page.update()

        # Build dialog content
        if not tool_checkboxes:
            content = ft.Column(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color=ft.Colors.GREY),
                    ft.Text("No tools available", text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        "Add sources and scan for tools first",
                        size=12,
                        color=ft.Colors.GREY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )
        else:
            content = ft.Column(controls=tool_checkboxes, scroll=ft.ScrollMode.AUTO, spacing=5)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Manage Tools - {toolbox.name}"),
            content=ft.Container(content=content, width=500, height=400),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.ElevatedButton("Save", on_click=save_tools, disabled=not tool_checkboxes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _on_edit_toolbox(self, e, toolbox):
        """Handle edit toolbox button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        snack_bar = ft.SnackBar(content=ft.Text("Edit toolbox feature coming soon"))
        page.snack_bar = snack_bar
        snack_bar.open = True
        page.update()

    def _on_delete_toolbox(self, e, toolbox):
        """Handle delete toolbox button click."""
        page = e.page if hasattr(e, "page") else e.control.page

        def close_dlg(e):
            dlg.open = False
            page.update()

        def confirm_delete(e):
            try:
                self.catalog_service.remove_toolbox(toolbox.id)
                dlg.open = False
                page.update()
                self.refresh()

                if self.on_update:
                    self.on_update()

                snack_bar = ft.SnackBar(
                    content=ft.Text(f"Deleted toolbox: {toolbox.name}"), bgcolor=ft.Colors.GREEN
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
            title=ft.Text("Delete Toolbox?"),
            content=ft.Text(
                f"Are you sure you want to delete '{toolbox.name}'?\n\n"
                "This will remove the toolbox from the catalog."
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
