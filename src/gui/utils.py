"""Utility functions for GUI components."""

import flet as ft


def show_snack_bar(page: ft.Page, message: str, color: str = ft.Colors.BLUE):
    """
    Show a snackbar notification.

    Args:
        page: Flet page object
        message: Message to display
        color: Background color for the snackbar
    """
    snack = ft.SnackBar(content=ft.Text(message), bgcolor=color, action="OK")
    page.snack_bar = snack
    snack.open = True
    page.update()
