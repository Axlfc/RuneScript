"""
Central theme manager for the application.

Handles:
- Theme storage and retrieval
- Theme application to CustomTkinter
- Theme change notifications to all windows
"""

import customtkinter as ctk
from pathlib import Path
from typing import Callable, List, Literal, Any, Union
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)

ThemeMode = Literal["Dark", "Light", "System"]

class ThemeManager:
    """
    Singleton theme manager.

    Responsibilities:
    - Store current theme preference
    - Apply theme to CustomTkinter
    - Notify windows when theme changes
    """

    _instance = None
    _observers: List[Any] = []
    _callbacks: List[Callable[[str], None]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._observers = []
        self._callbacks = []
        self._current_mode: ThemeMode = "Dark"
        self._current_theme_name: str = "blue"

        # Load theme from config if available
        self._load_theme_from_config()

        # Apply initial theme
        ctk.set_appearance_mode(self._current_mode)
        # Note: set_default_color_theme should be called before widget creation
        # but here we are in init, so it's mostly for first window

        logger.info(f"ThemeManager initialized with mode: {self._current_mode}, theme: {self._current_theme_name}")

    @classmethod
    def get_instance(cls) -> 'ThemeManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme_name

    def get_current_mode(self) -> ThemeMode:
        """Get the current appearance mode."""
        return self._current_mode

    def register_window(self, window: Any) -> None:
        """Registra una ventana para recibir notificaciones de cambio de tema"""
        if window not in self._observers:
            self._observers.append(window)
            logger.debug(f"Registered window: {window.__class__.__name__}")

    def unregister_window(self, window: Any) -> None:
        """Desregistra una ventana"""
        if window in self._observers:
            self._observers.remove(window)
            logger.debug(f"Unregistered window: {window.__class__.__name__}")

    def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for backward compatibility."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """Unregister a callback for backward compatibility."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def apply_theme(self, theme_name: str, appearance_mode: ThemeMode) -> None:
        """
        Aplica el tema a TODAS las ventanas registradas.
        """
        logger.info(f"Applying theme: {theme_name}, mode: {appearance_mode}")

        from src.controllers.parameters import get_theme_path
        theme_path = get_theme_path(theme_name)

        # Update internal state
        self._current_theme_name = theme_name
        self._current_mode = appearance_mode

        # Apply to CustomTkinter
        ctk.set_appearance_mode(appearance_mode)
        try:
            ctk.set_default_color_theme(theme_path)
        except Exception as e:
            logger.error(f"Error loading theme {theme_name}: {e}")
            ctk.set_default_color_theme("blue")

        # Save to config
        self._save_theme_to_config()

        # Notify all observers (Windows)
        for window in list(self._observers):
            try:
                if hasattr(window, "winfo_exists") and window.winfo_exists():
                    if hasattr(window, "refresh_theme"):
                        window.refresh_theme()
                    elif hasattr(window, "_on_theme_change"):
                        window._on_theme_change(appearance_mode)
                else:
                    self.unregister_window(window)
            except Exception as e:
                logger.error(f"Error refreshing window {window}: {e}")

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(appearance_mode)
            except Exception as e:
                logger.error(f"Error in theme callback: {e}")

    def set_theme(self, mode: ThemeMode) -> None:
        """Legacy method, delegates to apply_theme with current theme name."""
        self.apply_theme(self._current_theme_name, mode)

    def refresh_widget_recursive(self, widget: Any) -> None:
        """
        Actualiza recursivamente todos los widgets de una ventana.
        """
        try:
            if not hasattr(widget, "winfo_exists") or not widget.winfo_exists():
                return
        except Exception:
            return

        self._apply_theme_to_single_widget(widget)

        # Special handling for CTkTabview which doesn't show children in winfo_children
        if isinstance(widget, ctk.CTkTabview):
            try:
                for tab_name in widget._tab_dict.keys():
                    self.refresh_widget_recursive(widget.tab(tab_name))
            except Exception:
                pass

        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self.refresh_widget_recursive(child)

    def _apply_theme_to_single_widget(self, widget: Any) -> None:
        """Applies the current theme colors to a single CTk widget."""
        widget_type = type(widget).__name__
        theme_data = ctk.ThemeManager.theme

        if widget_type in theme_data:
            # Mapping of widget class to its themeable attributes
            config_map = {
                "CTkFrame": ["fg_color", "top_fg_color", "border_color"],
                "CTkButton": ["fg_color", "hover_color", "text_color", "border_color"],
                "CTkLabel": ["text_color", "fg_color"],
                "CTkEntry": ["fg_color", "border_color", "text_color", "placeholder_text_color"],
                "CTkCheckBox": ["fg_color", "border_color", "text_color", "checkmark_color"],
                "CTkSwitch": ["fg_color", "progress_color", "button_color", "button_hover_color", "text_color"],
                "CTkRadioButton": ["fg_color", "border_color", "text_color"],
                "CTkProgressBar": ["fg_color", "progress_color", "border_color"],
                "CTkSlider": ["fg_color", "progress_color", "button_color", "button_hover_color"],
                "CTkOptionMenu": ["fg_color", "button_color", "button_hover_color", "text_color"],
                "CTkComboBox": ["fg_color", "border_color", "button_color", "button_hover_color", "text_color"],
                "CTkScrollbar": ["fg_color", "button_color", "button_hover_color"],
                "CTkTextbox": ["fg_color", "border_color", "text_color"],
                "CTkTabview": ["fg_color", "segmented_button_fg_color", "segmented_button_selected_color", "segmented_button_selected_hover_color", "segmented_button_unselected_color", "segmented_button_unselected_hover_color", "text_color"],
                "CTkSegmentedButton": ["fg_color", "selected_color", "selected_hover_color", "unselected_color", "unselected_hover_color", "text_color"],
            }

            if widget_type in config_map:
                update_args = {}
                for attr in config_map[widget_type]:
                    if attr in theme_data[widget_type]:
                        update_args[attr] = theme_data[widget_type][attr]

                if update_args:
                    try:
                        widget.configure(**update_args)
                    except Exception as e:
                        # Some widgets might not support all theme keys in configure
                        pass

    def _load_theme_from_config(self) -> None:
        """Load theme preference from config file."""
        try:
            from src.controllers.parameters import read_config_parameter, get_appearance_mode, load_theme_setting
            self._current_theme_name = load_theme_setting()
            self._current_mode = get_appearance_mode(self._current_theme_name)
        except Exception as e:
            logger.warning(f"Could not load theme from config: {e}")

    def _save_theme_to_config(self) -> None:
        """Save theme preference to config file."""
        try:
            from src.controllers.parameters import write_config_parameter
            write_config_parameter("options.theme_appearance.theme", self._current_theme_name)
            write_config_parameter("options.theme_appearance.mode", self._current_mode)
        except Exception as e:
            logger.warning(f"Could not save theme to config: {e}")
