from tkinter import Frame
from tkinter import ttk


class TabManager:
    def __init__(self, notebook: ttk.Notebook):
        self.notebook = notebook
        self.tab_instances = {}  # Maps class -> instance
        self.tab_frames = {}     # Maps class -> Frame
        self.frame_to_class = {} # Maps Frame widget to tab class

        # Optional: track current selected tab for lifecycle events
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_selected)

    def add_tab(self, tab_class, git_window, name: str = None):
        """
        Add a new tab.
        :param tab_class: The tab class to instantiate.
        :param git_window: The GitWindow instance passed to the tab.
        :param name: Optional label. Defaults to class name without 'Tab'.
        """
        if tab_class in self.tab_instances:
            raise ValueError(f"Tab {tab_class.__name__} already exists.")

        frame = Frame(self.notebook)
        tab_instance = tab_class(frame, git_window)
        tab_name = name or tab_class.__name__.replace("Tab", "")

        self.notebook.add(frame, text=tab_name)

        self.tab_instances[tab_class] = tab_instance
        self.tab_frames[tab_class] = frame
        self.frame_to_class[frame] = tab_class

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
        selected_tab_id = self.notebook.select()
        selected_widget = self.notebook.nametowidget(selected_tab_id)

        tab_class = self.frame_to_class.get(selected_widget)
        tab_instance = self.tab_instances.get(tab_class)

        if hasattr(tab_instance, "on_focus") and callable(tab_instance.on_focus):
            tab_instance.on_focus()
