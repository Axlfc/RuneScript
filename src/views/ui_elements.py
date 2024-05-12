from tkinter import Toplevel, Label, Canvas


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event):
        if not self.tooltip:
            self.show_tooltip(event)

    def leave(self, event):
        self.destroy_tooltip()

    def motion(self, event):
        if self.tooltip:
            self.adjust_tooltip_position(event.x_root, event.y_root)

    def adjust_tooltip_position(self, x, y):
        # Get screen width and height
        screen_width = self.tooltip.winfo_screenwidth()
        screen_height = self.tooltip.winfo_screenheight()

        # Tooltip dimensions (guessing a size, will adjust after widget update)
        tooltip_width = 200
        tooltip_height = 50

        # Offset from cursor position to avoid directly covering it
        offset_x = 14
        offset_y = 14

        # Adjust position to keep tooltip inside screen boundaries
        x = min(x + offset_x, screen_width - tooltip_width)
        y = min(y + offset_y, screen_height - tooltip_height)

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def show_tooltip(self, event):
        self.tooltip = Toplevel()
        # Set initial position offscreen to avoid flicker on Windows
        self.tooltip.wm_geometry("+0+0")
        self.tooltip.wm_overrideredirect(True)
        label = Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

        # Adjust position now that we have the widget
        self.adjust_tooltip_position(event.x_root, event.y_root)

    def destroy_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
