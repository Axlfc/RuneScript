import json
import os
from tkinter import Toplevel, Frame, Button, LEFT, RIGHT, Y, X, N, S, W, E, BOTH, Label, Entry, END, Checkbutton, \
    scrolledtext, LabelFrame, messagebox
from tkinter.ttk import Treeview


class PromptEnhancementWindow:
    def __init__(self):
        """Initialize the Prompt Enhancement Studio window."""
        self.enhancement_window = Toplevel()
        self.enhancement_window.title("Prompt Enhancement Studio")
        self.enhancement_window.geometry("1000x700")

        # Initialize data storage
        self.prompt_data = {}
        self.categories = {}  # Category to prompt mapping: {category_name: [prompt_title1, prompt_title2]}
        self.variables = []  # Store variables as a list of dictionaries
        self.prompt_folder = "data/prompts"  # Directory to save/load prompts

        # Ensure prompt directory exists
        os.makedirs(self.prompt_folder, exist_ok=True)

        # Setup UI
        self.setup_ui()

        # Load saved categories and prompts
        self.load_saved_categories()

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
        self.category_tree.bind('<<TreeviewSelect>>', self.on_treeview_select)

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
        Label(tags_frame, text="Category:").pack(side=LEFT)
        self.category_entry = Entry(tags_frame)
        self.category_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        # Main prompt content
        self.prompt_text = scrolledtext.ScrolledText(editor_frame, height=15)
        self.prompt_text.pack(fill=BOTH, expand=True, pady=5)

        # Variable management
        var_frame = LabelFrame(editor_frame, text="Variables")
        var_frame.pack(fill=X, pady=5)

        self.var_tree = Treeview(var_frame, columns=("name", "description", "type", "default"), height=5, show="headings")
        self.var_tree.heading("name", text="Name")
        self.var_tree.heading("description", text="Description")
        self.var_tree.heading("type", text="Type")
        self.var_tree.heading("default", text="Default Value")
        self.var_tree.pack(fill=X, pady=5)

        var_button_frame = Frame(var_frame)
        var_button_frame.pack(fill=X, pady=5)
        Button(var_button_frame, text="Add Variable", command=self.add_variable).pack(side=LEFT, padx=5)
        Button(var_button_frame, text="Edit Variable", command=self.edit_variable).pack(side=LEFT, padx=5)
        Button(var_button_frame, text="Delete Variable", command=self.delete_variable).pack(side=LEFT, padx=5)

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

    def on_treeview_select(self, event):
        """Handle selection in the category tree."""
        selected_item = self.category_tree.selection()
        if not selected_item:
            return

        item_text = self.category_tree.item(selected_item, 'text')
        item_type = self.category_tree.item(selected_item, 'values')

        if item_type and item_type[0] == "prompt":
            self.load_prompt_by_title(item_text)
        elif item_type and item_type[0] == "category":
            print(f"Category '{item_text}' selected. No action for categories.")

    def save_categories(self):
        """Save categories and associated prompts."""
        with open(os.path.join(self.prompt_folder, "categories.json"), "w") as f:
            json.dump(self.categories, f, indent=4)

    def load_saved_categories(self):
        """Load saved categories and prompts."""
        categories_file = os.path.join(self.prompt_folder, "categories.json")
        if os.path.exists(categories_file):
            with open(categories_file, "r") as f:
                self.categories = json.load(f)

        # Populate the treeview with categories and prompts
        self.category_tree.delete(*self.category_tree.get_children())
        for category, prompts in self.categories.items():
            category_id = self.category_tree.insert('', 'end', text=category, values=("category",))
            for prompt in prompts:
                self.category_tree.insert(category_id, 'end', text=prompt, values=("prompt",))

    def load_variables_into_tree(self):
        """Load all variables into the Treeview."""
        self.var_tree.delete(*self.var_tree.get_children())
        for var in self.variables:
            self.var_tree.insert("", "end", values=(var["name"], var["description"], var["type"], var.get("default", "")))

    def add_variable(self):
        """Add a new variable."""
        new_var = {"name": "Variable" + str(len(self.variables) + 1), "description": "", "type": "text", "default": ""}
        self.variables.append(new_var)
        self.load_variables_into_tree()

    def edit_variable(self):
        """Edit the selected variable."""
        selected_item = self.var_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a variable to edit.")
            return

        item_values = self.var_tree.item(selected_item, "values")
        for var in self.variables:
            if var["name"] == item_values[0]:
                var["description"] = "Updated Description"  # Example edit
                var["default"] = "Default Value"
        self.load_variables_into_tree()

    def delete_variable(self):
        """Delete the selected variable."""
        selected_item = self.var_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a variable to delete.")
            return

        item_values = self.var_tree.item(selected_item, "values")
        self.variables = [var for var in self.variables if var["name"] != item_values[0]]
        self.load_variables_into_tree()

    def save_prompt(self):
        """Save the current prompt template to file."""
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        content = self.prompt_text.get("1.0", END).strip()

        if title and content and category:
            self.prompt_data = {
                "title": title,
                "category": category,
                "content": content,
                "variables": self.variables,
            }

            prompt_filename = os.path.join(self.prompt_folder, f"{title}.json")
            with open(prompt_filename, "w") as f:
                json.dump(self.prompt_data, f, indent=4)

            if category not in self.categories:
                self.categories[category] = []
                category_id = self.category_tree.insert('', 'end', text=category, values=("category",))
            else:
                category_id = [item for item in self.category_tree.get_children() if self.category_tree.item(item, 'text') == category][0]

            if title not in self.categories[category]:
                self.categories[category].append(title)
                self.category_tree.insert(category_id, 'end', text=title, values=("prompt",))
                self.save_categories()
        else:
            messagebox.showerror("Error", "Title, category, and content cannot be empty.")

    def load_prompt(self):
        """Load a prompt selected from the Treeview."""
        selected_item = self.category_tree.selection()
        if selected_item:
            item_text = self.category_tree.item(selected_item, 'text')
            item_type = self.category_tree.item(selected_item, 'values')

            if item_type and item_type[0] == "prompt":
                self.load_prompt_by_title(item_text)
            else:
                messagebox.showinfo("Info", "Please select a valid prompt to load.")
        else:
            messagebox.showinfo("Info", "No prompt selected.")

    def load_prompt_by_title(self, title):
        """Load a prompt by its title."""
        prompt_filename = os.path.join(self.prompt_folder, f"{title}.json")
        try:
            with open(prompt_filename, "r") as f:
                self.prompt_data = json.load(f)

            self.title_entry.delete(0, END)
            self.title_entry.insert(0, self.prompt_data['title'])

            self.category_entry.delete(0, END)
            self.category_entry.insert(0, self.prompt_data.get('category', ''))

            self.prompt_text.delete("1.0", END)
            self.prompt_text.insert("1.0", self.prompt_data['content'])

            self.variables = self.prompt_data.get("variables", [])
            self.load_variables_into_tree()

            print(f"Prompt '{title}' loaded successfully.")
        except FileNotFoundError:
            print(f"No saved prompt found with the title '{title}'.")

    def export_prompt(self):
        """Export the current prompt to a file."""
        title = self.title_entry.get().strip()
        content = self.prompt_text.get("1.0", END).strip()

        if title and content:
            export_filename = os.path.join(self.prompt_folder, f"{title}.txt")
            with open(export_filename, "w") as f:
                f.write(content)
            print(f"Prompt exported as {export_filename}")
        else:
            print("Title and content cannot be empty.")

    def test_prompt(self):
        """Test the current prompt template with variables replaced."""
        content = self.prompt_text.get("1.0", END).strip()
        if content:
            # Replace variables in the content with their default values
            for var in self.variables:
                placeholder = f"{{{{{var['name']}}}}}"  # Example: "{{variable_name}}"
                default_value = var.get("default", "")
                content = content.replace(placeholder, default_value)

            print("Testing prompt with variables interpreted:")
            print(content)
        else:
            print("Prompt content is empty.")

    def new_prompt(self):
        """Clear fields to create a new prompt."""
        self.title_entry.delete(0, END)
        self.category_entry.delete(0, END)
        self.prompt_text.delete("1.0", END)
        self.variables = []  # Clear variables
        self.var_tree.delete(*self.var_tree.get_children())  # Clear the variable treeview
        self.prompt_data = {}
