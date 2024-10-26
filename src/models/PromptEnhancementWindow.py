import json
import os
from tkinter import Toplevel, Frame, Button, LEFT, RIGHT, Y, X, N, S, W, E, BOTH, Label, Entry, END, Checkbutton, \
    scrolledtext, LabelFrame
from tkinter.ttk import Treeview


class PromptEnhancementWindow:
    def __init__(self):
        """Initialize the Prompt Enhancement Studio window."""
        self.enhancement_window = Toplevel()
        self.enhancement_window.title("Prompt Enhancement Studio")
        self.enhancement_window.geometry("1000x700")

        # Initialize data storage
        self.prompt_data = {}
        self.prompt_folder = "data/prompts"  # Directory to save/load prompts

        # Ensure prompt directory exists
        os.makedirs(self.prompt_folder, exist_ok=True)

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI layout."""
        main_frame = Frame(self.enhancement_window)
        main_frame.grid(row=0, column=0, sticky=(N, W, E, S))
        self.enhancement_window.columnconfigure(0, weight=1)
        self.enhancement_window.rowconfigure(0, weight=1)

        # Toolbar
        toolbar = Frame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=(W, E))
        Button(toolbar, text="New", command=self.new_prompt).pack(side=LEFT, padx=2)
        Button(toolbar, text="Save", command=self.save_prompt).pack(side=LEFT, padx=2)
        Button(toolbar, text="Load", command=self.load_prompt).pack(side=LEFT, padx=2)
        Button(toolbar, text="Export", command=self.export_prompt).pack(side=LEFT, padx=2)
        Button(toolbar, text="Settings").pack(side=LEFT, padx=2)
        Button(toolbar, text="Help").pack(side=RIGHT, padx=2)

        # Sidebar for categories and templates
        sidebar = Frame(main_frame, width=200)
        sidebar.grid(row=1, column=0, sticky=(N, S, W, E), padx=5, pady=5)

        # Category tree
        self.category_tree = Treeview(sidebar, height=10)
        self.category_tree.heading('#0', text='Categories')
        self.category_tree.pack(fill=Y, expand=True)

        # Add default categories
        categories = ['General', 'Code', 'Writing', 'Analysis']
        for category in categories:
            self.category_tree.insert('', 'end', text=category)

        # Main prompt editing area
        editor_frame = Frame(main_frame)
        editor_frame.grid(row=1, column=1, sticky=(N, S, W, E), pady=5)

        # Title and tags
        title_frame = Frame(editor_frame)
        title_frame.pack(fill=X, pady=5)
        Label(title_frame, text="Title:").pack(side=LEFT)
        self.title_entry = Entry(title_frame)
        self.title_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        tags_frame = Frame(editor_frame)
        tags_frame.pack(fill=X, pady=5)
        Label(tags_frame, text="Tags:").pack(side=LEFT)
        self.tags_entry = Entry(tags_frame)
        self.tags_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        # Main prompt content
        self.prompt_text = scrolledtext.ScrolledText(editor_frame, height=15)
        self.prompt_text.pack(fill=BOTH, expand=True, pady=5)

        # Variable management
        var_frame = LabelFrame(editor_frame, text="Variables")
        var_frame.pack(fill=X, pady=5)

        # Variable list with columns
        self.var_tree = Treeview(var_frame, columns=("name", "description", "type"), height=3)
        self.var_tree.heading("name", text="Name")
        self.var_tree.heading("description", text="Description")
        self.var_tree.heading("type", text="Type")
        self.var_tree.pack(fill=X, pady=5)

        # Enhancement options
        options_frame = LabelFrame(editor_frame, text="Enhancement Options")
        options_frame.pack(fill=X, pady=5)
        Checkbutton(options_frame, text="Add context retention").pack(anchor=W)
        Checkbutton(options_frame, text="Include conversation history").pack(anchor=W)
        Checkbutton(options_frame, text="Auto-format response").pack(anchor=W)

        # Bottom action buttons
        button_frame = Frame(editor_frame)
        button_frame.pack(fill=X, pady=5)
        Button(button_frame, text="Test Prompt", command=self.test_prompt).pack(side=LEFT, padx=5)
        Button(button_frame, text="Save Version", command=self.save_prompt).pack(side=LEFT, padx=5)
        Button(button_frame, text="Export", command=self.export_prompt).pack(side=LEFT, padx=5)

    def new_prompt(self):
        """Clear fields to create a new prompt."""
        self.title_entry.delete(0, END)
        self.tags_entry.delete(0, END)
        self.prompt_text.delete("1.0", END)
        self.var_tree.delete(*self.var_tree.get_children())
        self.prompt_data = {}

    def save_prompt(self):
        """Save the current prompt template to file."""
        title = self.title_entry.get().strip()
        tags = self.tags_entry.get().strip()
        content = self.prompt_text.get("1.0", END).strip()

        if title and content:
            self.prompt_data = {
                'title': title,
                'tags': tags,
                'content': content
            }

            # Save prompt to a JSON file named after the title in data/prompts
            prompt_filename = os.path.join(self.prompt_folder, f"{title}.json")

            with open(prompt_filename, 'w') as f:
                json.dump(self.prompt_data, f, indent=4)
            print(f"Prompt saved successfully to {prompt_filename}.")
        else:
            print("Title and content cannot be empty.")

    def load_prompt(self):
        """Load a saved prompt template."""
        title = self.title_entry.get().strip()
        if not title:
            print("Please enter the title of the prompt you want to load.")
            return

        prompt_filename = os.path.join(self.prompt_folder, f"{title}.json")

        try:
            with open(prompt_filename, 'r') as f:
                self.prompt_data = json.load(f)

            # Populate the UI with the loaded data
            self.title_entry.delete(0, END)
            self.title_entry.insert(0, self.prompt_data['title'])

            self.tags_entry.delete(0, END)
            self.tags_entry.insert(0, self.prompt_data.get('tags', ''))

            self.prompt_text.delete("1.0", END)
            self.prompt_text.insert("1.0", self.prompt_data['content'])

            print(f"Prompt '{title}' loaded successfully.")
        except FileNotFoundError:
            print(f"No saved prompt found with the title '{title}'.")

    def test_prompt(self):
        """Test the current prompt template."""
        content = self.prompt_text.get("1.0", END).strip()
        if content:
            # Placeholder for testing logic
            print("Testing prompt:", content)
        else:
            print("Prompt content is empty.")

    def export_prompt(self):
        """Export the current prompt to a file."""
        title = self.title_entry.get().strip()
        content = self.prompt_text.get("1.0", END).strip()

        if title and content:
            export_filename = os.path.join(self.prompt_folder, f"{title}.txt")
            with open(export_filename, 'w') as f:
                f.write(content)
            print(f"Prompt exported as {export_filename}")
        else:
            print("Title and content cannot be empty.")
