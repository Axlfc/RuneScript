import pytest
import customtkinter as ctk
from src.ui.theme_manager import ThemeManager

def test_theme_manager_is_singleton():
    ThemeManager._instance = None
    manager1 = ThemeManager.get_instance()
    manager2 = ThemeManager.get_instance()
    assert manager1 is manager2

def test_get_current_theme_returns_valid_mode():
    ThemeManager._instance = None
    manager = ThemeManager.get_instance()
    theme = manager.get_current_theme()
    assert theme in ["Dark", "Light", "System"]

def test_set_theme_changes_appearance_mode():
    ThemeManager._instance = None
    manager = ThemeManager.get_instance()
    manager.set_theme("Dark")
    assert ctk.get_appearance_mode() == "Dark"
    manager.set_theme("Light")
    assert ctk.get_appearance_mode() == "Light"
