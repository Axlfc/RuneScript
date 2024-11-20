import tkinter as tk
from time import strftime
import datetime


class ClockWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Elegant Digital Clock")
        self.geometry("600x300")
        self.configure(background='black')

        # Configure grid to be fully expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame to center the clock
        self.clock_frame = tk.Frame(self, bg='black')
        self.clock_frame.grid(row=0, column=0, sticky='nsew')
        self.clock_frame.grid_rowconfigure(0, weight=1)
        self.clock_frame.grid_rowconfigure(1, weight=1)
        self.clock_frame.grid_columnconfigure(0, weight=1)

        # Time Label with dynamic font sizing
        self.time_label = tk.Label(
            self.clock_frame,
            font=('DS-Digital', 60, 'bold'),
            background='black',
            foreground='#00FF00',
            anchor='center'
        )
        self.time_label.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)

        # Date Label with dynamic font sizing
        self.date_label = tk.Label(
            self.clock_frame,
            font=('Arial', 20, 'bold'),
            background='black',
            foreground='#00FF00',
            anchor='center'
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
        time_font_size = min(int(width / 15), int(height / 4))
        date_font_size = min(int(width / 30), int(height / 10))

        self.time_label.config(font=('DS-Digital', time_font_size, 'bold'))
        self.date_label.config(font=('Arial', date_font_size, 'bold'))

    def update_clock(self):
        # Get current time and format
        current_time = strftime('%H:%M:%S %p')
        current_date = datetime.datetime.now().strftime('%A, %B %d, %Y')

        # Update labels
        self.time_label.config(text=current_time)
        self.date_label.config(text=current_date)

        # Schedule next update
        self.after(1000, self.update_clock)