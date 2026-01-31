import pytest
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow
from src.ui.theme_manager import ThemeManager

def test_themed_window_registers_with_theme_manager():
    ThemeManager._instance = None
    manager = ThemeManager.get_instance()
    initial_callbacks = len(manager._callbacks)
    root = ctk.CTk()
    window = ThemedWindow(root)
    assert len(manager._callbacks) > initial_callbacks
    window.destroy()
    root.destroy()
