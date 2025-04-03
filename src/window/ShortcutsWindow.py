from tkinter import Toplevel, Label, Frame, LEFT, RIGHT, Canvas, Scrollbar, VERTICAL, YES, BOTH, X, NW, ttk
from tkinter import font
import platform


class ShortcutsWindow:
    def __init__(self):
        """Initialize the Shortcuts Window with comprehensive keyboard shortcut details for all OS."""
        self.shortcuts_window = Toplevel()
        self.shortcuts_window.title("Keyboard Shortcuts")
        self.shortcuts_window.geometry("800x600")
        self.shortcuts_window.resizable(True, True)
        self.center_window(800, 600)

        # Detect operating system
        self.os_system = platform.system().lower()

        self.setup_ui()

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.shortcuts_window.winfo_screenwidth()
        screen_height = self.shortcuts_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.shortcuts_window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Set up the UI with all keyboard shortcuts organized by categories."""
        notebook = ttk.Notebook(self.shortcuts_window)
        notebook.pack(fill='both', expand=True)

        # Create tabs for different categories
        os_tab = Frame(notebook)
        browser_tab = Frame(notebook)
        powertoys_tab = Frame(notebook)

        notebook.add(os_tab, text='Operating Systems')
        notebook.add(browser_tab, text='Browser Shortcuts')
        notebook.add(powertoys_tab, text='PowerToys')

        # Setup scrollable content for each tab
        self.setup_os_tab(os_tab)
        self.setup_browser_tab(browser_tab)
        self.setup_powertoys_tab(powertoys_tab)

    def setup_os_tab(self, parent):
        """Set up the OS tab with nested tabs for each operating system."""
        os_notebook = ttk.Notebook(parent)
        os_notebook.pack(fill='both', expand=True)

        # Create sub-tabs for each OS
        windows_tab = Frame(os_notebook)
        mac_tab = Frame(os_notebook)
        linux_tab = Frame(os_notebook)

        os_notebook.add(windows_tab, text='Windows')
        os_notebook.add(mac_tab, text='macOS')
        os_notebook.add(linux_tab, text='Linux')

        # Setup content for each OS
        self.setup_scrollable_content(windows_tab, self.get_windows_shortcuts())
        self.setup_scrollable_content(mac_tab, self.get_mac_shortcuts())
        self.setup_scrollable_content(linux_tab, self.get_linux_shortcuts())

    def setup_browser_tab(self, parent):
        """Set up the browser shortcuts tab."""
        self.setup_scrollable_content(parent, self.get_firefox_shortcuts())

    def setup_powertoys_tab(self, parent):
        """Set up the PowerToys shortcuts tab."""
        self.setup_scrollable_content(parent, self.get_powertoys_shortcuts())

    def setup_scrollable_content(self, parent, shortcuts_data):
        """Set up scrollable content for any tab."""
        # Create Canvas and Scrollbar
        canvas = Canvas(parent, borderwidth=0)
        scrollbar = Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill='y')
        canvas.pack(side=LEFT, fill='both', expand=True)

        # Create content frame
        content_frame = Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor=NW)
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Define fonts
        heading_font = font.Font(family="Arial", size=14, weight="bold")
        content_font = font.Font(family="Arial", size=10)

        # Add shortcuts for each category
        for category, shortcuts in shortcuts_data.items():
            self.add_category(content_frame, category, heading_font)
            self.add_shortcuts(content_frame, shortcuts, content_font)

    def add_category(self, parent, category_name, font_style):
        """Add a category heading."""
        Label(parent, text=category_name, font=font_style, anchor="w", pady=10).pack(fill='x', padx=10)

    def add_shortcuts(self, parent, shortcuts, font_style):
        """Add shortcuts to the content frame."""
        for action, shortcut in shortcuts:
            row_frame = Frame(parent)
            row_frame.pack(fill="x", pady=2, padx=20)

            action_label = Label(row_frame, text=action + ":", font=font_style, anchor="w", width=50)
            action_label.pack(side=LEFT)

            shortcut_label = Label(row_frame, text=shortcut, font=font_style, anchor="w")
            shortcut_label.pack(side=LEFT, fill='x', expand=True)

    def get_windows_shortcuts(self):
        """Return Windows-specific shortcuts."""
        return {
            "Essential Shortcuts": [
                ("Select all", "Ctrl + A (Ctrl + E)"),
                ("Copy text", "Ctrl + C"),
                ("Cut text", "Ctrl + X"),
                ("Paste text", "Ctrl + V"),
                ("Undo action", "Ctrl + Z"),
                ("Redo undo action", "Ctrl + Y"),
                ("Create new folder/document/window", "Ctrl + Shift + N"),
                ("Rename file/folder", "F2"),
                ("Delete selected item", "Ctrl + D"),
                ("Delete selected item skipping Recycle Bin", "Shift + Del"),
                ("Close active window", "Alt + F4"),
                ("Refresh current window", "Ctrl + R"),
                ("View open apps", "Ctrl + Alt + Tab"),
                ("Switch app", "Alt + Tab"),
                ("Switch app backwards", "Alt + Shift + Tab"),
                ("Cycle through open windows", "Alt + Esc"),
                ("Cycle through open windows backwards", "Alt + Shift + Esc"),
            ],
            "System Controls": [
                ("Take screenshot", "Windows + Shift + S"),
                ("Open File Explorer", "Windows + E"),
                ("Open Task Manager", "Ctrl + Shift + Esc"),
                ("Open Search", "Windows + S"),
                ("Open Settings", "Windows + I"),
                ("Open Clipboard bin", "Windows + V"),
                ("Open emoji panel", "Windows + ."),
                ("Multiple purpose keyboard combination", "Ctrl + Alt + Del"),
                ("Open Run command", "Windows + R"),
                ("Zoom in (magnifier)", "Windows + +"),
                ("Zoom out (magnifier)", "Windows + -"),
                ("Exit magnifier", "Windows + Esc"),
            ],
            "Desktop Management": [
                ("Open Start menu", "Windows"),
                ("Change Start menu size", "Ctrl + Arrow keys"),
                ("Open hidden menu", "Windows + X"),
                ("Opens the System Properties dialog box", "Windows + Pause/Break"),
                ("Open favorite app", "Windows + Number (0-9)"),
                ("Display and hide Desktop", "Windows + D"),
                ("Temporarily peek at the desktop", "Windows + ,"),
                ("Stretch desktop window", "Windows + Shift + Up arrow key"),
                ("Maximize/minimize vertically", "Windows + Shift + Down arrow key"),
                ("Move window to left monitor", "Windows + Shift + Left arrow key"),
                ("Move window to right monitor", "Windows + Shift + Right arrow key"),
                ("Snap app or window left", "Windows + Left arrow key"),
                ("Snap app or window right", "Windows + Right arrow key"),
                ("Maximize app windows", "Windows + Up arrow key"),
                ("Minimize app windows", "Windows + Down arrow key"),
                ("Domain network search", "Windows + Ctrl + F"),
                ("System Properties", "Windows + Ctrl + Pause"),
                ("Lock computer", "Windows + L"),
            ],
            "Text Manipulation": [
                ("Move to previous word", "Ctrl + Left arrow key"),
                ("Move to next word", "Ctrl + Right arrow key"),
                ("Move to previous paragraph", "Ctrl + Up arrow key"),
                ("Move to next paragraph", "Ctrl + Down arrow key"),
                ("Select block of text", "Ctrl + Shift + Arrow key"),
                ("Select multiple items", "Shift + Arrow keys"),
                ("Move cursor page up", "Page Up"),
                ("Move cursor page down", "Page Down"),
                ("Search", "Ctrl + F"),
                ("Scroll to top", "Ctrl + Home"),
                ("Scroll to bottom", "Ctrl + End"),
                ("Bold text", "Ctrl + B"),
                ("Italic text", "Ctrl + I"),
                ("Underline text", "Ctrl + U"),
                ("Save", "Ctrl + S"),
                ("Print", "Ctrl + P"),
            ],
        }

    def get_mac_shortcuts(self):
        """Return macOS shortcuts."""
        return {
            "Essential Commands": [
                ("Select all", "⌘ + A"),
                ("Copy", "⌘ + C"),
                ("Cut", "⌘ + X"),
                ("Paste", "⌘ + V"),
                ("Undo", "⌘ + Z"),
                ("Redo", "⌘ + Shift + Z"),
                ("Force quit", "⌘ + Option + Esc"),
                ("Switch applications", "⌘ + Tab"),
                ("Close window", "⌘ + W"),
                ("Quit application", "⌘ + Q"),
            ],
            "System Controls": [
                ("Lock screen", "⌘ + Control + Q"),
                ("Spotlight search", "⌘ + Space"),
                ("System Preferences", "⌘ + ,"),
                ("Mission Control", "Control + Up"),
                ("Application windows", "Control + Down"),
                ("Screenshot menu", "⌘ + Shift + 5"),
                ("Full screenshot", "⌘ + Shift + 3"),
                ("Selection screenshot", "⌘ + Shift + 4"),
            ],
        }

    def get_linux_shortcuts(self):
        """Return Linux shortcuts."""
        return {
            "Essential Commands": [
                ("Select all", "Ctrl + A"),
                ("Copy", "Ctrl + C"),
                ("Cut", "Ctrl + X"),
                ("Paste", "Ctrl + V"),
                ("Undo", "Ctrl + Z"),
                ("Redo", "Ctrl + Shift + Z"),
                ("Switch applications", "Alt + Tab"),
                ("Close window", "Alt + F4"),
            ],
            "System Controls": [
                ("Lock screen", "Super + L"),
                ("Terminal", "Ctrl + Alt + T"),
                ("Screenshot tool", "PrtSc"),
                ("Area screenshot", "Shift + PrtSc"),
                ("Window screenshot", "Alt + PrtSc"),
            ],
        }

    def get_firefox_shortcuts(self):
        """Return Firefox shortcuts."""
        return {
            "Developer Tools": [
                ("Open Toolbox", "Ctrl + Shift + I"),
                ("Open Web Console", "Ctrl + Shift + K"),
                ("Pick element", "Ctrl + Shift + C"),
                ("Style Editor", "Shift + F7"),
                ("Network Monitor", "Ctrl + Shift + E"),
                ("Responsive Design Mode", "Ctrl + Shift + M"),
                ("Browser Console", "Ctrl + Shift + J"),
                ("Open Debugger", "Ctrl + Shift + Z"),
                ("Cycle tools left to right", "Ctrl + ]"),
                ("Cycle tools right to left", "Ctrl + ["),
                ("Toggle toolbox docking", "Ctrl + Shift + D"),
                ("Increase font size", "Ctrl + +"),
                ("Decrease font size", "Ctrl + -"),
                ("Reset font size", "Ctrl + 0"),
            ],
            "Tab Management": [
                ("Open previously closed tab", "Ctrl + Shift + T"),
                ("Open specific tab (1-8)", "Ctrl + (1-8)"),
                ("Open last tab", "Ctrl + 9"),
                ("Close current tab", "Ctrl + W"),
                ("Close all tabs", "Ctrl + Shift + W"),
                ("Move tab right", "Ctrl + Shift + Page Down"),
                ("Move tab left", "Ctrl + Shift + Page Up"),
                ("Go to right tab", "Ctrl + Page Down"),
                ("Go to left tab", "Ctrl + Page Up"),
                ("New tab", "Ctrl + T"),
                ("New window", "Ctrl + N"),
                ("New private window", "Ctrl + Shift + P"),
            ],
            "Navigation": [
                ("Refresh page", "F5 or Ctrl + R"),
                ("Hard refresh", "Ctrl + F5 or Ctrl + Shift + R"),
                ("Stop loading", "Esc"),
                ("Go back", "Alt + Left Arrow or Backspace"),
                ("Go forward", "Alt + Right Arrow or Shift + Backspace"),
                ("History", "Ctrl + H"),
                ("Downloads", "Ctrl + J"),
                ("Bookmark manager", "Ctrl + Shift + O"),
                ("Add bookmark", "Ctrl + D"),
                ("Full screen", "F11"),
                ("Reader mode", "F9"),
                ("Caret browsing", "F7"),
                ("View source", "Ctrl + U"),
                ("Find in page", "Ctrl + F"),
                ("Find next", "F3 or Ctrl + G"),
                ("Find previous", "Shift + F3 or Ctrl + Shift + G"),
                ("Address bar", "Ctrl + L or Alt + D"),
            ],
        }

    def get_powertoys_shortcuts(self):
        """Return PowerToys shortcuts."""
        return {
            "General Commands": [
                ("Show commands", "Shift + Windows + Ç"),
                ("Manage window display (FancyZones)", "Windows + `"),
                ("Quick launcher (PowerToys Run)", "ALT + Space"),
                ("Identify colors (Color Picker)", "Shift + Windows Key + C"),
                ("Find mouse", "Left CTRL (x2)"),
                ("Toggle window focus", "Windows Key + CTRL + T"),
                ("Measure pixels", "Shift + Windows Key + M"),
                ("Copy text from screen", "Shift + Windows Key + T"),
                ("Preview files", "CTRL + Space"),
                ("Crop window", "Shift + CTRL + Windows Key + T"),
            ],
            "Video Conference": [
                ("Silence camera and microphone", "Shift + Windows Key + Q"),
                ("Silence microphone", "Shift + Windows Key + A"),
                ("Push to Talk", "Shift + Windows Key + I"),
                ("Silence camera", "Shift + Windows Key + O"),
            ],
            "Utilities": [
                ("Bulk rename files", "Right-click > PowerRename"),
                ("Resize images", "Right-click > Resize Pictures"),
                ("Check file usage", "Right-click > What's using this file?"),
                ("Paste as plain text", "CTRL + ALT + Windows Key + V"),
            ],
        }