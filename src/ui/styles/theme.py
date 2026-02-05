import ttkbootstrap as tb
from ttkbootstrap.constants import *

class IDEStyle:
    """
    Centralized theme and style configuration for the IDE.
    Uses ttkbootstrap for modern components.
    """

    THEME_NAME = "darkly"

    @classmethod
    def apply_styles(cls, root):
        """Initializes the theme and global styles."""
        style = tb.Style(theme=cls.THEME_NAME)

        # Custom styling for specific components if needed
        style.configure('TopBar.TFrame', background='#1e1e1e')
        style.configure('Telemetry.TLabel', font=('Segoe UI', 10), foreground='#cccccc')
        style.configure('StatusBadge.TLabel', font=('Segoe UI', 10, 'bold'))

        # Severity Colors
        # These will be used by individual components
        cls.COLORS = {
            'critical': '#e53e3e',
            'warning': '#d69e2e',
            'info': '#3182ce',
            'resolved': '#38a169',
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3d3d3d',
            'text_main': '#ffffff',
            'text_dim': '#aaaaaa'
        }

        return style

    @classmethod
    def get_severity_color(cls, severity):
        return cls.COLORS.get(severity.lower(), cls.COLORS['info'])
