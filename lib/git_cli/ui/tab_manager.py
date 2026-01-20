from tkinter import Frame
from tkinter import ttk


class TabManager:
    def __init__(self, notebook: ttk.Notebook):
        self.notebook = notebook
        self.tab_instances = {}  # Maps class -> instance
        self.tabs = self.tab_instances
        self.tab_frames = {}  # Maps class -> Frame
        self.frame_to_class = {}  # Maps Frame widget to tab class

        # Optional: track current selected tab for lifecycle events
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_selected)

    def add_tab(self, tab_class, *args, name=None, **kwargs):
        frame = Frame(self.notebook)
        frame.pack(fill="both", expand=True)

        tab_instance = tab_class(frame, *args, **kwargs)
        tab_instance.pack(fill="both", expand=True)  # ahora sÃ­, porque heredan de Frame

        self.notebook.add(frame, text=name if name else tab_class.__name__)
        return tab_instance

    def remove_tab(self, tab_class):
        """Remove a tab by its class."""
        if tab_class not in self.tab_instances:
            raise ValueError(f"Tab {tab_class.__name__} not found.")

        frame = self.tab_frames[tab_class]
        self.notebook.forget(frame)

        del self.tab_instances[tab_class]
        del self.tab_frames[tab_class]
        del self.frame_to_class[frame]

    def get_tab(self, tab_class):
        """Get the instance of a tab class."""
        return self.tab_instances.get(tab_class)

    def get_all_tabs(self):
        """Return a dict of all active tab instances."""
        return dict(self.tab_instances)

    def _on_tab_selected(self, event):
        """Handler for tab selection events"""
        try:
            selected_tab_id = self.notebook.select()
            if not selected_tab_id:  # No tab selected
                return

            selected_widget = self.notebook.nametowidget(selected_tab_id)

            tab_class = self.frame_to_class.get(selected_widget)
            if not tab_class:  # Unknown widget
                return

            tab_instance = self.tab_instances.get(tab_class)
            if not tab_instance:  # Unknown instance
                return

            # Call the focus handler if it exists
            if hasattr(tab_instance, "on_focus") and callable(tab_instance.on_focus):
                tab_instance.on_focus()
        except Exception as e:
            print(f"Error in tab selection handler: {e}")
