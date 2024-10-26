from tkinter import Toplevel, Label, Frame, Scrollbar, Canvas, LEFT, BOTH, VERTICAL, Y


class HelpWindow:
    def __init__(self):
        """Initialize the Help Window to display detailed keyboard shortcuts."""
        self.help_window = Toplevel()
        self.help_window.title("Help - Keyboard Shortcuts")
        self.help_window.geometry("600x600")
        self.center_window(600, 600)
        self.setup_ui()

    def center_window(self, width, height):
        """Center the window on the screen."""
        x = (self.help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.help_window.winfo_screenheight() // 2) - (height // 2)
        self.help_window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Set up the UI with categorized shortcut information."""
        Label(self.help_window, text="Keyboard Shortcuts", font=("Arial", 14, "bold")).pack(pady=10)

        # Scrollable frame for large content
        canvas = Canvas(self.help_window)
        scroll_y = Scrollbar(self.help_window, orient=VERTICAL, command=canvas.yview)
        frame = Frame(canvas)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=LEFT, fill=Y)

        # Categories and shortcuts data
        categories = {
            "File Operations": [
                ("New File", "Ctrl + N"),
                ("Open File", "Ctrl + O"),
                ("Close File", "Ctrl + W"),
                ("Save File", "Ctrl + S"),
                ("Save As...", "Ctrl + Shift + S"),
                ("Move/Rename File", "F2"),
                ("Print Document", "Ctrl + P"),
            ],
            "Edit Operations": [
                ("Undo", "Ctrl + Z"),
                ("Redo", "Ctrl + Y"),
                ("Cut", "Ctrl + X"),
                ("Copy", "Ctrl + C"),
                ("Paste", "Ctrl + V"),
                ("Duplicate", "Ctrl + D"),
                ("Find", "Ctrl + F"),
                ("Find And Replace", "Ctrl+R"),
                ("Find In Files", "Ctrl+H")
            ],
            "View Controls": [
                ("Toggle Directory Pane", "Ctrl + Shift + D"),
                ("Toggle File Pane", "Ctrl + Shift + F"),
                ("Script Arguments Dialog", "Ctrl + Shift + A"),
                ("Run Script", "Ctrl + Shift + R"),
                ("Set Timeout", "Ctrl + Shift + T"),
                ("Toggle Interactive Mode", "Ctrl + Shift + I"),
                ("Open Filesystem Explorer", "Ctrl + Shift + E"),
            ],
            "Tools and Utilities": [
                ("AI Assistant", "Ctrl + Alt + A"),
                ("Generate Audio", "Ctrl + Alt + G"),
                ("Calculator", "Ctrl + Alt + C"),
                ("Translator", "Ctrl + Alt + T"),
                ("Prompt Enhancement", "Ctrl + Alt + P"),
                ("Kanban Board", "Ctrl + Alt + K"),
                ("LaTeX/Markdown Editor", "Ctrl + Alt + L"),
                ("Git Console", "Ctrl + Alt + G"),
                ("System Shell", "Ctrl + Alt + S"),
                ("Python Shell", "Ctrl + Alt + Y"),
                ("Notebooks", "Ctrl + Alt + N"),
                ("Options/Settings", "Ctrl + ,"),
            ],
            "System Commands": [
                ("Open Winget Window", "Ctrl + Alt + W"),
                ("System Info", "Ctrl + Alt + I"),
            ],
            "Jobs": [
                ("New 'at' Job", "Ctrl + Alt + Shift + A"),
                ("New 'crontab' Job", "Ctrl + Alt + Shift + C"),
                ("Manage Scheduled Tasks", "Ctrl + Alt + Shift + S"),
            ],
            "Help and Support": [
                ("Help Contents", "F1"),
                ("About Text Editor Pro", "Ctrl + Alt + H"),
            ]
        }

        # Populate categories and shortcuts in the frame
        for category, shortcuts in categories.items():
            Label(frame, text=category, font=("Arial", 12, "bold")).pack(anchor="w", pady=5, padx=10)
            for action, shortcut in shortcuts:
                row_frame = Frame(frame)
                row_frame.pack(fill="x", pady=2)
                Label(row_frame, text=f"{action}:", anchor="w", width=30).pack(side=LEFT, padx=10)
                Label(row_frame, text=shortcut, anchor="e", width=20).pack(side=LEFT)
