"""
Base class for all themed windows.

All windows should inherit from this to get automatic theme support.
"""

import customtkinter as ctk
from .theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class ThemedWindow(ctk.CTkToplevel):
    """
    Base class for themed windows.

    Features:
    - Automatically applies current theme
    - Registers for theme updates
    - Unregisters on destroy
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._theme_manager = ThemeManager.get_instance()

        # Apply current theme
        self._apply_theme(self._theme_manager.get_current_theme())

        # Register for theme updates
        self._theme_manager.register_callback(self._on_theme_change)

        logger.debug(f"ThemedWindow created: {self.__class__.__name__}")

    def _apply_theme(self, theme: str) -> None:
        """
        Apply theme to this window.

        Override this in subclasses to apply custom theming.
        """
        # Base implementation: CustomTkinter handles most styling automatically
        logger.debug(f"Applying theme '{theme}' to {self.__class__.__name__}")

    def _on_theme_change(self, new_theme: str) -> None:
        """Called when theme changes."""
        logger.debug(f"Theme changed to '{new_theme}' in {self.__class__.__name__}")
        self._apply_theme(new_theme)

    def destroy(self):
        """Clean up before destroying."""
        # Unregister from theme manager
        self._theme_manager.unregister_callback(self._on_theme_change)
        logger.debug(f"ThemedWindow destroying: {self.__class__.__name__}")

        # Call default destroy
        super().destroy()


class ThemedFrame(ctk.CTkFrame):
    """
    Base class for themed frames (for main window content).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._theme_manager = ThemeManager.get_instance()

        # Apply current theme
        self._apply_theme(self._theme_manager.get_current_theme())

        # Register for theme updates
        self._theme_manager.register_callback(self._on_theme_change)

    def _apply_theme(self, theme: str) -> None:
        """Apply theme to this frame."""
        # Override in subclasses if needed
        pass

    def _on_theme_change(self, new_theme: str) -> None:
        """Called when theme changes."""
        self._apply_theme(new_theme)

    def destroy(self):
        """Clean up before destroying."""
        self._theme_manager.unregister_callback(self._on_theme_change)
        super().destroy()


class ThemedApp(ctk.CTk):
    """
    Base class for themed main application window.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._theme_manager = ThemeManager.get_instance()

        # Apply current theme
        self._apply_theme(self._theme_manager.get_current_theme())

        # Register for theme updates
        self._theme_manager.register_callback(self._on_theme_change)

        logger.debug(f"ThemedApp created: {self.__class__.__name__}")

    def _apply_theme(self, theme: str) -> None:
        """Apply theme to this window."""
        logger.debug(f"Applying theme '{theme}' to {self.__class__.__name__}")

    def _on_theme_change(self, new_theme: str) -> None:
        """Called when theme changes."""
        logger.debug(f"Theme changed to '{new_theme}' in {self.__class__.__name__}")
        self._apply_theme(new_theme)

    def destroy(self):
        """Clean up before destroying."""
        self._theme_manager.unregister_callback(self._on_theme_change)
        super().destroy()
