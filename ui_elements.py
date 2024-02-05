from tkinter import Toplevel, Label


class Tooltip:
    """
        A class to create a tooltip for a given widget.

        The Tooltip class provides a simple way to add a tooltip to any tkinter widget. It displays a small popup
        with a text message when the mouse hovers over the widget.

        Attributes:
        widget (Widget): The tkinter widget to which the tooltip is attached.
        text (str): The text displayed in the tooltip.
        tooltip (Toplevel, optional): The top-level widget used for displaying the tooltip. Initially None.

        Methods:
        enter(event): Displays the tooltip when the mouse enters the widget area.
        leave(event): Destroys the tooltip when the mouse leaves the widget area.
        """
    def __init__(self, widget, text):
        """
            Initializes the Tooltip instance.

            Parameters:
            widget (Widget): The tkinter widget to which the tooltip will be attached.
            text (str): The text to be displayed in the tooltip.

            Returns:
            None
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event):
        """
            Handles the mouse entering the widget area, displaying the tooltip.

            This method is triggered when the mouse pointer enters the widget area. It creates and positions
            the tooltip near the widget.

            Parameters:
            event (Event): The event object containing details of the mouse enter event.

            Returns:
            None
        """
        self.tooltip = Toplevel()
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def leave(self, event):
        """
            Handles the mouse leaving the widget area, hiding the tooltip.

            This method is triggered when the mouse pointer leaves the widget area. It destroys the tooltip
            window if it exists.

            Parameters:
            event (Event): The event object containing details of the mouse leave event.

            Returns:
            None
        """
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
