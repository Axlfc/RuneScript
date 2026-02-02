import pytest
import customtkinter as ctk
from src.ui.theme_manager import ThemeManager

def test_theme_manager_is_singleton():
    ThemeManager._instance = None
    manager1 = ThemeManager.get_instance()
    manager2 = ThemeManager.get_instance()
    assert manager1 is manager2

def test_get_current_mode_returns_valid_mode():
    ThemeManager._instance = None
    manager = ThemeManager.get_instance()
    mode = manager.get_current_mode()
    assert mode in ["Dark", "Light", "System"]

def test_apply_theme_changes_appearance_mode():
    ThemeManager._instance = None
    manager = ThemeManager.get_instance()
    manager.apply_theme("blue", "Dark")
    ctk.set_appearance_mode.assert_called_with("Dark")
    manager.apply_theme("blue", "Light")
    ctk.set_appearance_mode.assert_called_with("Light")
