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
    - Automatically registers for theme updates
    - Provides a refresh_theme method for in-place updates
    - Unregisters on destroy
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._theme_manager = ThemeManager.get_instance()

        # Register for theme updates
        self._theme_manager.register_window(self)

        logger.debug(f"ThemedWindow created: {self.__class__.__name__}")

    def refresh_theme(self) -> None:
        """
        Actualiza TODOS los widgets de esta ventana con el nuevo tema.
        Override this in subclasses for custom component updates.
        """
        logger.debug(f"Refreshing theme for {self.__class__.__name__}")
        self._theme_manager.refresh_widget_recursive(self)
        self.update_idletasks()

    def destroy(self):
        """Clean up before destroying."""
        # Unregister from theme manager
        self._theme_manager.unregister_window(self)
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

        # Register for theme updates
        self._theme_manager.register_window(self)

    def refresh_theme(self) -> None:
        """Refresh theme for this frame and its children."""
        self._theme_manager.refresh_widget_recursive(self)

    def destroy(self):
        """Clean up before destroying."""
        self._theme_manager.unregister_window(self)
        super().destroy()


class ThemedApp(ctk.CTk):
    """
    Base class for themed main application window.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._theme_manager = ThemeManager.get_instance()

        # Register for theme updates
        self._theme_manager.register_window(self)

        logger.debug(f"ThemedApp created: {self.__class__.__name__}")

    def refresh_theme(self) -> None:
        """Refresh theme for the main app window."""
        logger.debug(f"Refreshing theme for {self.__class__.__name__}")
        self._theme_manager.refresh_widget_recursive(self)
        self.update_idletasks()

    def destroy(self):
        """Clean up before destroying."""
        self._theme_manager.unregister_window(self)
        super().destroy()
