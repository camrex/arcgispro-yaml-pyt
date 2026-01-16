"""Tools Panel - Browse discovered tools."""

import flet as ft

from src.catalog import CatalogService


class ToolsPanel:
    """Panel for browsing discovered tools."""

    def __init__(self, catalog_service: CatalogService):
        """
        Initialize the tools panel.

        Args:
            catalog_service: Catalog service instance
        """
        self.catalog_service = catalog_service

        # UI components
        self.tools_grid: ft.GridView | None = None
        self.search_field: ft.TextField | None = None
        self.source_filter: ft.Dropdown | None = None
        self.all_tools: list = []
        self.filtered_tools: list = []

    def build(self) -> ft.Control:
        """Build the tools panel UI."""
        # Header
        header = ft.Text("Discovered Tools", size=24, weight=ft.FontWeight.BOLD)

        # Search and filter controls
        self.search_field = ft.TextField(
            hint_text="Search tools...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
        )
        self.search_field.on_change = self._on_search_change

        self.source_filter = ft.Dropdown(
            label="Source",
            hint_text="All sources",
            options=[],
            width=200,
        )
        self.source_filter.on_change = self._on_filter_change

        filter_row = ft.Row(
            controls=[
                self.search_field,
                self.source_filter,
            ],
            spacing=10,
        )

        # Tools grid
        self.tools_grid = ft.GridView(
            runs_count=3,
            max_extent=350,
            child_aspect_ratio=1.2,
            spacing=15,
            run_spacing=15,
            expand=True,
        )

        # Initial load
        self.refresh()

        return ft.Column(
            controls=[header, ft.Divider(), filter_row, ft.Container(height=10), self.tools_grid],
            expand=True,
            spacing=10,
        )

    def refresh(self):
        """Refresh the tools display."""
        if not self.tools_grid:
            return

        # Get all discovered tools from all sources
        sources = self.catalog_service.list_sources()
        self.all_tools = []

        # Import DiscoveryService to scan sources
        from src.catalog.discovery import DiscoveryService

        discovery_service = DiscoveryService(self.catalog_service)

        for source in sources:
            if source.enabled and source.discovered_tools > 0:
                try:
                    # Scan source to get actual discovered tools
                    discovered_tools, _ = discovery_service.scan_source(source.id)

                    for discovered_tool in discovered_tools:
                        self.all_tools.append(
                            {
                                "tool_ref": discovered_tool,
                                "source": source,
                                "toolbox": None,  # Not assigned to any toolbox yet
                            }
                        )
                except Exception as e:
                    # If scanning fails, skip this source
                    print(f"Warning: Could not scan source {source.name}: {e}")
                    continue

        # Update source filter dropdown
        if self.source_filter:
            source_options = [ft.dropdown.Option(key="", text="All sources")]
            for source in sources:
                if source.enabled and source.discovered_tools > 0:
                    source_options.append(ft.dropdown.Option(key=source.id, text=source.name))
            self.source_filter.options = source_options
            try:
                if self.source_filter.page:
                    self.source_filter.update()
            except (RuntimeError, AttributeError):
                pass

        # Apply current filters
        self._apply_filters()

    def _apply_filters(self):
        """Apply search and source filters."""
        search_text = (self.search_field.value or "").lower()
        selected_source = self.source_filter.value if self.source_filter else None

        # Filter tools
        self.filtered_tools = []
        for item in self.all_tools:
            tool_ref = item["tool_ref"]
            source = item["source"]

            # Source filter
            if selected_source and source.id != selected_source:
                continue

            # Search filter
            if search_text:
                # Handle both DiscoveredTool and ToolReference objects
                if hasattr(tool_ref, "name"):  # DiscoveredTool
                    tool_name = tool_ref.name
                    tool_description = (
                        tool_ref.config.tool.description
                        if tool_ref.config and hasattr(tool_ref.config, "tool")
                        else ""
                    )
                    search_fields = [
                        tool_name.lower(),
                        tool_description.lower(),
                        source.name.lower(),
                    ]
                else:  # ToolReference
                    tool_name = tool_ref.alias or tool_ref.tool_path
                    search_fields = [tool_name.lower(), source.name.lower()]

                if not any(search_text in field for field in search_fields):
                    continue

            self.filtered_tools.append(item)

        # Update grid
        self._update_grid()

    def _update_grid(self):
        """Update the tools grid display."""
        if not self.tools_grid:
            return

        self.tools_grid.controls.clear()

        if not self.filtered_tools:
            # Show empty state
            self.tools_grid.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF, size=64, color=ft.Colors.GREY),
                            ft.Text(
                                "No tools found",
                                size=16,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Try adjusting your search or filters",
                                size=12,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                )
            )
        else:
            # Display tools
            for item in self.filtered_tools:
                self.tools_grid.controls.append(
                    self._build_tool_card(item["tool_ref"], item["source"])
                )

        try:
            if self.tools_grid and self.tools_grid.page:
                self.tools_grid.update()
        except (RuntimeError, AttributeError):
            pass

    def _build_tool_card(self, tool_ref, source) -> ft.Card:
        """Build a card for a tool reference or discovered tool."""
        # Handle both DiscoveredTool and ToolReference objects
        if hasattr(tool_ref, "name"):  # DiscoveredTool
            tool_name = tool_ref.name
            tool_path = (
                str(tool_ref.path.relative_to(source.path))
                if source.path and tool_ref.path
                else tool_ref.tool_id
            )
            description = (
                tool_ref.config.tool.description
                if tool_ref.config and hasattr(tool_ref.config, "tool")
                else "No description"
            )
        else:  # ToolReference
            tool_name = (
                tool_ref.alias or tool_ref.tool_path.split("/")[-1].replace("_", " ").title()
            )
            tool_path = tool_ref.tool_path
            description = f"Path: {tool_ref.tool_path}"

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BUILD_CIRCLE, size=24, color=ft.Colors.BLUE),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            tool_name,
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            description,
                                            size=10,
                                            color=ft.Colors.GREY,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Text(
                            f"Source: {source.name}",
                            size=11,
                            color=ft.Colors.GREY_700,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Container(expand=True),
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                ft.TextButton(
                                    "View Details",
                                    icon=ft.Icons.INFO_OUTLINE,
                                    on_click=lambda e, t=tool_ref, s=source: self._on_view_details(
                                        e, t, s
                                    ),
                                ),
                            ]
                        ),
                    ],
                    spacing=8,
                ),
                padding=12,
            ),
            elevation=2,
        )

    def _on_view_details(self, e, tool_ref, source):
        """Show tool details dialog."""
        page = e.page if hasattr(e, "page") else e.control.page

        def close_dlg(e):
            dlg.open = False
            page.update()

        # Build details content
        if hasattr(tool_ref, "name"):  # DiscoveredTool
            tool_name = tool_ref.name
            details = [
                ft.Row(
                    [
                        ft.Text("Tool Name:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(tool_ref.name, selectable=True, expand=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Tool ID:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(tool_ref.tool_id, selectable=True, expand=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Path:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(str(tool_ref.path), selectable=True, expand=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Source:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(source.name, selectable=True),
                    ]
                ),
            ]

            if tool_ref.config and hasattr(tool_ref.config, "tool"):
                details.extend(
                    [
                        ft.Divider(),
                        ft.Text("Description:", weight=ft.FontWeight.BOLD),
                        ft.Text(tool_ref.config.tool.description, selectable=True),
                    ]
                )
        else:  # ToolReference
            tool_name = tool_ref.alias or tool_ref.tool_path.split("/")[-1]
            details = [
                ft.Row(
                    [
                        ft.Text("Tool Path:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(tool_ref.tool_path, selectable=True, expand=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Source:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(source.name, selectable=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Source Type:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text(source.type.value, selectable=True),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Enabled:", weight=ft.FontWeight.BOLD, width=120),
                        ft.Text("Yes" if tool_ref.enabled else "No"),
                    ]
                ),
            ]

            if tool_ref.alias:
                details.insert(
                    0,
                    ft.Row(
                        [
                            ft.Text("Alias:", weight=ft.FontWeight.BOLD, width=120),
                            ft.Text(tool_ref.alias, selectable=True),
                        ]
                    ),
                )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.BUILD_CIRCLE),
                    ft.Text(tool_name),
                ]
            ),
            content=ft.Container(
                content=ft.Column(controls=details, scroll=ft.ScrollMode.AUTO, spacing=8),
                width=600,
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _on_search_change(self, e):
        """Handle search field changes."""
        self._apply_filters()

    def _on_filter_change(self, e):
        """Handle source filter changes."""
        self._apply_filters()
