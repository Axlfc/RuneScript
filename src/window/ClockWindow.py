import tkinter as tk
import customtkinter as ctk
from time import strftime
import datetime
from src.ui.themed_window import ThemedWindow


class ClockWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Elegant Digital Clock")
        self.geometry("600x300")

        # Use a consistent background from theme if possible, but clock often looks better black
        # self.configure(background='black')

        # Configure grid to be fully expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame to center the clock
        self.clock_frame = ctk.CTkFrame(self)
        self.clock_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        self.clock_frame.grid_rowconfigure(0, weight=1)
        self.clock_frame.grid_rowconfigure(1, weight=1)
        self.clock_frame.grid_columnconfigure(0, weight=1)

        # Time Label with dynamic font sizing
        self.time_label = ctk.CTkLabel(
            self.clock_frame,
            text="",
            font=('Arial', 60, 'bold'), # Default font if DS-Digital missing
            text_color='#00FF00'
        )
        self.time_label.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)

        # Date Label with dynamic font sizing
        self.date_label = ctk.CTkLabel(
            self.clock_frame,
            text="",
            font=('Arial', 20, 'bold'),
            text_color='#00FF00'
        )
        self.date_label.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)

        # Bind resize event to adjust font sizes
        self.bind('<Configure>', self.adjust_font_sizes)

        # Update clock periodically
        self.update_clock()

    def adjust_font_sizes(self, event=None):
        # Dynamically adjust font sizes based on window dimensions
        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate font sizes dynamically
        time_font_size = min(int(width / 10), int(height / 3))
        date_font_size = min(int(width / 25), int(height / 8))

        if time_font_size > 0:
            self.time_label.configure(font=('Arial', time_font_size, 'bold'))
        if date_font_size > 0:
            self.date_label.configure(font=('Arial', date_font_size, 'bold'))

    def update_clock(self):
        # Get current time and format
        now = datetime.datetime.now()
        current_time = now.strftime('%H:%M:%S %p')
        current_date = now.strftime('%A, %B %d, %Y')

        # Update labels
        self.time_label.configure(text=current_time)
        self.date_label.configure(text=current_date)

        # Schedule next update
        self.after(1000, self.update_clock)
