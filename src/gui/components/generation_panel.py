"""Generation Panel - Generate Python toolbox files."""

from pathlib import Path

import flet as ft

from src.catalog import CatalogService, GeneratorService
from src.gui.utils import show_snack_bar


class GenerationPanel:
    """Panel for generating Python toolbox files."""

    def __init__(self, catalog_service: CatalogService, generator_service: GeneratorService):
        """
        Initialize the generation panel.

        Args:
            catalog_service: Catalog service instance
            generator_service: Generator service instance
        """
        self.catalog_service = catalog_service
        self.generator_service = generator_service

        # UI components
        self.toolbox_cards: ft.Column | None = None
        self.generate_metadata_switch: ft.Switch | None = None

    def build(self) -> ft.Control:
        """Build the generation panel UI."""
        # Header
        header = ft.Row(
            controls=[
                ft.Text("Generate Toolboxes", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Generate All", icon=ft.Icons.ROCKET_LAUNCH, on_click=self._on_generate_all
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Options
        self.generate_metadata_switch = ft.Switch(label="Generate XML metadata", value=True)

        options_row = ft.Row(
            controls=[
                self.generate_metadata_switch,
            ],
            spacing=20,
        )

        # Toolbox cards
        self.toolbox_cards = ft.Column(
            controls=[], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )

        # Initial load
        self.refresh()

        return ft.Column(
            controls=[
                header,
                ft.Divider(),
                options_row,
                ft.Container(height=10),
                self.toolbox_cards,
            ],
            expand=True,
            spacing=10,
        )

    def refresh(self):
        """Refresh the toolbox list."""
        if not self.toolbox_cards:
            return

        toolboxes = {t.id: t for t in self.catalog_service.list_toolboxes()}
        self.toolbox_cards.controls.clear()

        if not toolboxes:
            self.toolbox_cards.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2, size=64, color=ft.Colors.GREY),
                            ft.Text(
                                "No toolboxes to generate",
                                size=16,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Create toolboxes in the Toolboxes tab first",
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
                self.toolbox_cards.controls.append(self._build_toolbox_card(toolbox))

        try:
            if self.toolbox_cards and self.toolbox_cards.page:
                self.toolbox_cards.update()
        except (RuntimeError, AttributeError):
            pass

    def _build_toolbox_card(self, toolbox) -> ft.Card:
        """Build a card for a toolbox."""
        tool_count = len(toolbox.tools) if toolbox.tools else 0

        # Validate toolbox
        is_valid, errors = self.generator_service.validate_toolbox(toolbox.id)

        # Status indicator
        if is_valid:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=20)
            status_text = ft.Text("Ready to generate", color=ft.Colors.GREEN, size=12)
        else:
            status_icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=20)
            status_text = ft.Text(f"{len(errors)} error(s)", color=ft.Colors.RED, size=12)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INVENTORY_2, size=32, color=ft.Colors.PURPLE),
                                ft.Column(
                                    controls=[
                                        ft.Text(toolbox.name, size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text(str(toolbox.path), size=11, color=ft.Colors.GREY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                status_icon,
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                status_text,
                                ft.Container(expand=True),
                                ft.Text(
                                    f"{tool_count} tool{'s' if tool_count != 1 else ''}",
                                    size=12,
                                    color=ft.Colors.GREY,
                                ),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Generate",
                                    icon=ft.Icons.PLAY_ARROW,
                                    disabled=not is_valid,
                                    on_click=lambda e, tb=toolbox: self._on_generate_single(e, tb),
                                ),
                                ft.OutlinedButton(
                                    "Show Validation",
                                    icon=ft.Icons.INFO_OUTLINE,
                                    disabled=is_valid,
                                    on_click=lambda e, errs=errors: self._on_show_validation(
                                        e, errs
                                    ),
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

    def _on_generate_single(self, e, toolbox):
        """Handle generate single toolbox."""
        page = e.page if hasattr(e, "page") else e.control.page
        generate_metadata = (
            self.generate_metadata_switch.value if self.generate_metadata_switch else True
        )

        # Show progress dialog
        progress_text = ft.Text("Generating toolbox...")
        progress_ring = ft.ProgressRing()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Generating"),
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
            # Generate toolbox
            output_path = self.generator_service.generate_toolbox(
                toolbox.id, toolbox.path, generate_metadata=generate_metadata
            )

            # Close progress dialog
            dlg.open = False
            page.update()

            # Show success dialog
            self._show_success_dialog(page, str(output_path))

        except Exception as ex:
            dlg.open = False
            page.update()
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Error generating toolbox: {ex}"), bgcolor=ft.Colors.RED
            )
            page.snack_bar = snack_bar
            snack_bar.open = True
            page.update()

    def _on_generate_all(self, e):
        """Handle generate all toolboxes."""
        page = e.page if hasattr(e, "page") else e.control.page
        generate_metadata = (
            self.generate_metadata_switch.value if self.generate_metadata_switch else True
        )

        # Get output directory
        def on_directory_result(e: ft.FilePickerResultEvent):
            if not e.path:
                return

            output_dir = Path(e.path)

            # Show progress dialog
            progress_text = ft.Text("Generating all toolboxes...")
            progress_ring = ft.ProgressRing()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Generating"),
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
                # Generate all toolboxes
                output_paths = self.generator_service.generate_all_toolboxes(
                    output_dir, generate_metadata=generate_metadata
                )

                # Close progress dialog
                dlg.open = False
                page.update()

                # Show success message
                show_snack_bar(page, f"Generated {len(output_paths)} toolbox(es)", ft.Colors.GREEN)

            except Exception as ex:
                dlg.open = False
                page.update()
                show_snack_bar(page, f"Error: {ex}", ft.Colors.RED)

        file_picker = ft.FilePicker(on_result=on_directory_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path(dialog_title="Select output directory")

    def _on_show_validation(self, e, errors):
        """Show validation errors dialog."""
        page = e.page if hasattr(e, "page") else e.control.page

        def close_dlg(e):
            dlg.open = False
            page.update()

        error_items = [ft.Text(f"• {error}", size=12) for error in errors]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED),
                    ft.Text("Validation Errors"),
                ]
            ),
            content=ft.Container(
                content=ft.Column(controls=error_items, scroll=ft.ScrollMode.AUTO, spacing=8),
                width=500,
                height=300,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _show_success_dialog(self, page, output_path: str):
        """Show success dialog after generation."""

        def close_dlg(e):
            dlg.open = False
            page.update()

        def open_folder(e):
            import os
            import subprocess

            folder = str(Path(output_path).parent)
            if os.name == "nt":  # Windows
                subprocess.Popen(f'explorer /select,"{output_path}"')
            else:
                subprocess.Popen(["xdg-open", folder])

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN),
                    ft.Text("Generation Complete!"),
                ]
            ),
            content=ft.Column(
                controls=[
                    ft.Text("Toolbox generated successfully:", weight=ft.FontWeight.BOLD),
                    ft.Text(output_path, size=12, selectable=True),
                    ft.Divider(),
                    ft.Text("Next steps:", weight=ft.FontWeight.BOLD),
                    ft.Text("1. Open ArcGIS Pro", size=12),
                    ft.Text("2. Add the toolbox to your project", size=12),
                    ft.Text("3. Run the tools!", size=12),
                ],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Open Folder", on_click=open_folder),
                ft.ElevatedButton("Done", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()
