"""
Central theme manager for the application.

Handles:
- Theme storage and retrieval
- Theme application to CustomTkinter
- Theme change notifications to all windows
"""

import customtkinter as ctk
from pathlib import Path
from typing import Callable, List, Literal
import logging

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
        self._callbacks = []
        self._current_theme = "Dark"  # Default

        # Load theme from config if available
        self._load_theme_from_config()

        # Apply initial theme
        ctk.set_appearance_mode(self._current_theme)

        logger.info(f"ThemeManager initialized with theme: {self._current_theme}")

    @classmethod
    def get_instance(cls) -> 'ThemeManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_current_theme(self) -> ThemeMode:
        """Get the current theme mode."""
        return self._current_theme

    def set_theme(self, theme: ThemeMode) -> None:
        """
        Set the theme and notify all registered windows.

        Args:
            theme: "Dark", "Light", or "System"
        """
        if theme not in ["Dark", "Light", "System"]:
            logger.warning(f"Invalid theme: {theme}, using Dark")
            theme = "Dark"

        logger.info(f"Setting theme to: {theme}")

        # Update internal state
        self._current_theme = theme

        # Apply to CustomTkinter
        ctk.set_appearance_mode(theme)

        # Save to config
        self._save_theme_to_config()

        # Notify all registered callbacks
        self._notify_callbacks(theme)

    def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when theme changes.

        Args:
            callback: Function that takes theme name as argument
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"Registered theme callback")

    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """
        Unregister a callback.

        Args:
            callback: The callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Unregistered theme callback: {callback}")

    def _notify_callbacks(self, theme: str) -> None:
        """Notify all registered callbacks of theme change."""
        logger.debug(f"Notifying {len(self._callbacks)} callbacks of theme change")

        for callback in self._callbacks:
            try:
                callback(theme)
            except Exception as e:
                logger.error(f"Error in theme callback: {e}")

    def _load_theme_from_config(self) -> None:
        """Load theme preference from config file."""
        try:
            from src.core.config import Config
            config = Config.load()

            if hasattr(config, 'theme'):
                self._current_theme = config.theme
                logger.info(f"Loaded theme from config: {self._current_theme}")
            else:
                logger.debug("No theme in config, using default")
        except Exception as e:
            logger.warning(f"Could not load theme from config: {e}")

    def _save_theme_to_config(self) -> None:
        """Save theme preference to config file."""
        try:
            from src.core.config import Config
            config = Config.load()

            # Add theme field if not present (pydantic model handles this if we updated it)
            config.theme = self._current_theme

            config.save(Path(".rgr/config.yaml"))
            logger.debug(f"Saved theme to config: {self._current_theme}")
        except Exception as e:
            logger.warning(f"Could not save theme to config: {e}")
