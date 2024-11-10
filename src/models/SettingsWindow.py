import json
import os
from tkinter import (
    Toplevel,
    Label,
    Entry,
    Button,
    StringVar,
    messagebox,
    Frame,
    font,
    BOTH,
    LEFT,
    X,
    BooleanVar,
    BOTTOM, Checkbutton
)
from tkinter.ttk import Notebook, Combobox

from src.controllers.parameters import read_config_parameter, write_config_parameter
from src.models.LanguageManager import LanguageManager
from src.views.tk_utils import style
from src.views.ui_elements import ScrollableFrame


class SettingsWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.language_code_map = None
        self.title("ScriptsEditor Settings")
        self.geometry("800x600")
        self.style = style

        # Configuration file paths
        self.default_config_file = "data/config.json"
        self.user_config_file = "data/user_config.json"
        self.config_file_to_use = self.user_config_file if os.path.exists(
            self.user_config_file) else self.default_config_file

        # Load configuration
        self.config_data = self.load_config()
        if not self.config_data:
            self.destroy()
            return

        # Initialize UI components
        self.setting_entries = {}
        self.setup_ui()

    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file_to_use, "r") as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Config file ({self.config_file_to_use}) not found.")
            return None
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Error decoding config file ({self.config_file_to_use}).")
            return None

    def load_themes_from_json(self, file_path):
        """Load themes from JSON file."""
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                return data.get("themes", [])
        except FileNotFoundError:
            messagebox.showerror("Error", "Themes file not found.")
            return []
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error decoding themes file.")
            return []

    def setup_ui(self):
        """Setup the main UI components."""
        # Main frame
        self.main_frame = Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Notebook for tabs
        self.notebook = Notebook(self.main_frame)
        self.notebook.pack(fill=BOTH, expand=True)

        # Bottom frame for buttons
        self.bottom_frame = Frame(self)
        self.bottom_frame.pack(fill=X, side=BOTTOM, padx=10, pady=10)

        self.create_settings_sections()
        self.create_buttons()

    def create_settings_sections(self):
        """Create settings sections in the notebook."""
        for section, options in self.config_data["options"].items():
            section_frame = Frame(self.notebook)
            self.notebook.add(section_frame, text=section.capitalize())

            scrollable_frame = ScrollableFrame(section_frame)
            scrollable_frame.pack(fill=BOTH, expand=True)

            self.create_option_widgets(scrollable_frame, section, options)

    def create_option_widgets(self, scrollable_frame, section, options):
        """Create widgets for each option in a section."""
        for row, (option_name, default_value) in enumerate(options.items()):
            label = Label(
                scrollable_frame.scrollable_frame,
                text=option_name.replace("_", " ").capitalize()
            )
            label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

            widget, var = self.create_appropriate_widget(
                scrollable_frame.scrollable_frame,
                option_name,
                default_value
            )

            if widget:
                widget.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
                scrollable_frame.scrollable_frame.grid_columnconfigure(1, weight=1)
                self.setting_entries[section, option_name] = var

    def create_appropriate_widget(self, parent, option_name, default_value):
        """Create appropriate widget based on option type."""
        if option_name.lower() == "language":
            lang_manager = LanguageManager()
            available_languages = lang_manager.get_available_languages()

            # Create list of language names for display
            language_display_list = [lang[1] for lang in available_languages]

            # Create mapping of display names to language codes
            self.language_code_map = {lang[1]: lang[0] for lang in available_languages}

            # Get the current language name from code
            current_lang_name = next(
                (lang[1] for lang in available_languages if lang[0] == default_value),
                language_display_list[0]
            )

            var = StringVar(value=current_lang_name)
            widget = Combobox(parent, textvariable=var, values=language_display_list)

            # Store the reverse mapping for saving
            self._orig_language_var = var
            var = StringVar()

            def on_language_select(*args):
                selected_name = self._orig_language_var.get()
                var.set(self.language_code_map.get(selected_name, "en"))

            self._orig_language_var.trace('w', on_language_select)
            return widget, var

        elif option_name.lower() == "font_family":
            font_families = font.families()
            default_font = default_value if default_value in font_families else "Courier New"
            var = StringVar(value=default_font)
            widget = Combobox(parent, textvariable=var, values=font_families)
            return widget, var

        elif option_name.lower() == "theme":
            themes = self.load_themes_from_json("data/themes.json")
            default_theme = default_value if default_value in themes else themes[0]
            var = StringVar(value=default_theme)
            widget = Combobox(parent, textvariable=var, values=themes)
            return widget, var

        elif isinstance(default_value, bool):
            var = BooleanVar(value=default_value)
            widget = Checkbutton(parent, variable=var)
            return widget, var

        elif isinstance(default_value, (str, int)):
            var = StringVar(value=str(default_value))
            widget = Entry(parent, textvariable=var)
            return widget, var

        return None, None

    def create_buttons(self):
        """Create save and reset buttons."""
        save_button = Button(self.bottom_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(side=LEFT, padx=5)

        reset_button = Button(self.bottom_frame, text="Reset Settings", command=self.reset_settings)
        reset_button.pack(side=LEFT, padx=5)

    def save_settings(self):
        """Save settings to user config file."""
        updated_config_data = {"options": {}}
        for (section, option_name), var in self.setting_entries.items():
            value = var.get()
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            updated_config_data["options"].setdefault(section, {})[option_name] = value

        with open(self.user_config_file, "w") as user_config:
            json.dump(updated_config_data, user_config, indent=4)

        # Apply theme if available
        theme = updated_config_data["options"].get("theme_appearance", {}).get("theme", None)
        if theme:
            try:
                self.style.theme_use(theme)
            except Exception as e:
                messagebox.showerror("Theme Error", f"The theme '{theme}' is not available. ({e})")

        # Save language and font settings
        write_config_parameter("options.editor_settings.language",
                               updated_config_data["options"]["editor_settings"]["language"])
        write_config_parameter("options.editor_settings.font_family",
                               updated_config_data["options"]["editor_settings"]["font_family"])

        messagebox.showinfo("Settings Saved", "Settings saved successfully!")

    def reset_settings(self):
        """Reset settings to defaults."""
        for (section, option_name), var in self.setting_entries.items():
            default_value = self.config_data["options"][section][option_name]
            if isinstance(var, BooleanVar):
                var.set(default_value)
            elif isinstance(var, StringVar):
                var.set(str(default_value))

        if os.path.exists(self.user_config_file):
            os.remove(self.user_config_file)

        # default_theme = self.config_data["options"].get("theme_appearance", {}).get("theme", "default")
        default_theme = read_config_parameter("options.theme_appearance.theme")
        try:
            self.style.theme_use(default_theme)
        except Exception as e:
            messagebox.showerror("Theme Error", f"The default theme '{default_theme}' is not available. ({e}")

        messagebox.showinfo("Reset Settings", "Settings reset to defaults. User configuration file deleted.")