import os
import json
from tkinter import Toplevel, Frame, Button, LEFT, RIGHT, Y, X, N, S, W, E, BOTH, Label, Entry, END, Checkbutton, \
    scrolledtext, LabelFrame, messagebox, StringVar, Menu, simpledialog
from tkinter.ttk import Treeview

DEFAULT_CATEGORY_FILE = "data/prompt_categories.json"  # File for default categories


class VariableEditDialog(Toplevel):
    def __init__(self, parent, variable=None):
        super().__init__(parent)
        self.title("Edit Variable")
        self.variable = variable or {}
        self.result = None

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create and pack the form
        form = Frame(self)
        form.pack(padx=10, pady=5, fill=BOTH, expand=True)

        # Name field
        Label(form, text="Name:").grid(row=0, column=0, sticky=W, pady=2)
        self.name_var = StringVar(value=variable.get("name", ""))
        self.name_entry = Entry(form, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky=W + E, pady=2)

        # Description field
        Label(form, text="Description:").grid(row=1, column=0, sticky=W, pady=2)
        self.desc_var = StringVar(value=variable.get("description", ""))
        self.desc_entry = Entry(form, textvariable=self.desc_var)
        self.desc_entry.grid(row=1, column=1, sticky=W + E, pady=2)

        # Type field
        Label(form, text="Type:").grid(row=2, column=0, sticky=W, pady=2)
        self.type_var = StringVar(value=variable.get("type", "text"))
        self.type_entry = Entry(form, textvariable=self.type_var)
        self.type_entry.grid(row=2, column=1, sticky=W + E, pady=2)

        # Default value field
        Label(form, text="Default Value:").grid(row=3, column=0, sticky=W, pady=2)
        self.default_var = StringVar(value=variable.get("default", ""))
        self.default_entry = Entry(form, textvariable=self.default_var)
        self.default_entry.grid(row=3, column=1, sticky=W + E, pady=2)

        # Buttons
        button_frame = Frame(form)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        Button(button_frame, text="OK", command=self.ok).pack(side=LEFT, padx=5)
        Button(button_frame, text="Cancel", command=self.cancel).pack(side=LEFT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.wait_window(self)

    def ok(self):
        self.result = {
            "name": self.name_var.get(),
            "description": self.desc_var.get(),
            "type": self.type_var.get(),
            "default": self.default_var.get()
        }
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class PromptEnhancementWindow:
    def __init__(self):
        """Initialize the Prompt Enhancement Studio window."""
        self.enhancement_window = Toplevel()
        self.enhancement_window.title("Prompt Enhancement Studio")
        self.enhancement_window.geometry("1200x800")

        # Initialize data storage
        self.prompt_data = {}
        self.categories = {}  # {category_name: [prompt_title1, prompt_title2]}
        self.default_categories = self.load_default_categories()
        self.variables = []  # Store variables as a list of dictionaries
        self.prompt_folder = "data/prompts"  # Directory to save/load prompts

        # Ensure prompt directory exists
        os.makedirs(self.prompt_folder, exist_ok=True)

        # Setup UI
        self.setup_ui()

        # Load saved categories and prompts
        self.load_saved_categories()

    def load_default_categories(self):
        """Load default categories from a file."""
        if os.path.exists(DEFAULT_CATEGORY_FILE):
            with open(DEFAULT_CATEGORY_FILE, "r") as f:
                return json.load(f)
        else:
            return {}

    def create_context_menus(self):
        """Create context menus for the category tree."""
        self.category_menu = Menu(self.enhancement_window, tearoff=0)
        self.category_menu.add_command(label="New Category", command=self.new_category)
        self.category_menu.add_command(label="Rename Category", command=self.rename_category)
        self.category_menu.add_command(label="Delete Category", command=self.delete_category)

        self.prompt_menu = Menu(self.enhancement_window, tearoff=0)
        self.prompt_menu.add_command(label="Rename Prompt", command=self.rename_prompt)
        self.prompt_menu.add_command(label="Delete Prompt", command=self.delete_prompt)

        self.category_tree.bind("<Button-3>", self.show_context_menu)
    def show_context_menu(self, event):
        """Show the appropriate context menu based on the selected item."""
        item = self.category_tree.identify_row(event.y)
        if item:
            self.category_tree.selection_set(item)
            item_type = self.category_tree.item(item, "values")
            if item_type and item_type[0] == "category":
                self.category_menu.post(event.x_root, event.y_root)
            elif item_type and item_type[0] == "prompt":
                self.prompt_menu.post(event.x_root, event.y_root)

    def new_category(self):
        """Add a new category."""
        name = simpledialog.askstring("New Category", "Enter category name:")
        if name and name.strip():
            if name not in self.categories:
                self.categories[name] = {"description": "", "subcategories": {}}
                self.category_tree.insert('', 'end', text=name, values=("category",))
                self.save_categories()
            else:
                messagebox.showerror("Error", "Category already exists!")

    def rename_category(self):
        """Rename selected category."""
        selected = self.category_tree.selection()
        if not selected:
            return

        item = selected[0]
        if self.category_tree.item(item)["values"][0] != "category":
            return

        old_name = self.category_tree.item(item)["text"]
        new_name = messagebox.askstring("Rename Category", "Enter new name:", initialvalue=old_name)

        if new_name and new_name.strip() and new_name != old_name:
            if new_name not in self.categories:
                self.categories[new_name] = self.categories.pop(old_name)
                self.category_tree.item(item, text=new_name)
                self.save_categories()
            else:
                messagebox.showerror("Error", "Category already exists!")

    def delete_category(self):
        """Delete selected category and all its prompts."""
        selected = self.category_tree.selection()
        if not selected:
            return

        item = selected[0]
        if self.category_tree.item(item)["values"][0] != "category":
            return

        category = self.category_tree.item(item)["text"]
        if messagebox.askyesno("Confirm Delete", f"Delete category '{category}' and all its prompts?"):
            # Delete prompt files
            for prompt in self.categories[category]:
                try:
                    os.remove(os.path.join(self.prompt_folder, f"{prompt}.json"))
                except OSError:
                    pass

            # Delete category
            del self.categories[category]
            self.category_tree.delete(item)
            self.save_categories()

    def rename_prompt(self):
        """Rename selected prompt."""
        selected = self.category_tree.selection()
        if not selected:
            return

        item = selected[0]
        if self.category_tree.item(item)["values"][0] != "prompt":
            return

        old_name = self.category_tree.item(item)["text"]
        new_name = messagebox.askstring("Rename Prompt", "Enter new name:", initialvalue=old_name)

        if new_name and new_name.strip() and new_name != old_name:
            # Update prompt file
            old_file = os.path.join(self.prompt_folder, f"{old_name}.json")
            new_file = os.path.join(self.prompt_folder, f"{new_name}.json")

            try:
                with open(old_file, 'r') as f:
                    prompt_data = json.load(f)

                prompt_data['title'] = new_name

                with open(new_file, 'w') as f:
                    json.dump(prompt_data, f, indent=4)

                os.remove(old_file)

                # Update category listing
                category = self.category_tree.item(self.category_tree.parent(item))["text"]
                self.categories[category].remove(old_name)
                self.categories[category].append(new_name)

                self.category_tree.item(item, text=new_name)
                self.save_categories()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename prompt: {str(e)}")

    def delete_prompt(self):
        """Delete selected prompt."""
        selected = self.category_tree.selection()
        if not selected:
            return

        item = selected[0]
        if self.category_tree.item(item)["values"][0] != "prompt":
            return

        prompt = self.category_tree.item(item)["text"]
        if messagebox.askyesno("Confirm Delete", f"Delete prompt '{prompt}'?"):
            try:
                os.remove(os.path.join(self.prompt_folder, f"{prompt}.json"))
                category = self.category_tree.item(self.category_tree.parent(item))["text"]
                self.categories[category].remove(prompt)
                self.category_tree.delete(item)
                self.save_categories()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete prompt: {str(e)}")

    def search_prompt(self):
        """Search for a category or prompt in the tree."""
        query = simpledialog.askstring("Search", "Enter search term:")
        if not query:
            return

        query = query.lower()
        results = []

        # Recursive function to search through the tree
        def search_tree(item, path=""):
            text = self.category_tree.item(item, "text").lower()
            if query in text:
                results.append((item, path + text))
            for child in self.category_tree.get_children(item):
                search_tree(child, path + text + " > ")

        # Start searching from the root items
        for top_level_item in self.category_tree.get_children():
            search_tree(top_level_item)

        # Display results
        if results:
            result_text = "\n".join(f"{path}" for _, path in results)
            messagebox.showinfo("Search Results", f"Found the following matches:\n\n{result_text}")
            # Highlight the first result in the tree
            self.category_tree.selection_set(results[0][0])
            self.category_tree.focus(results[0][0])
        else:
            messagebox.showinfo("Search Results", "No matches found.")

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
        Button(toolbar, text="Search", command=self.search_prompt).pack(side=LEFT, padx=2)
        Button(toolbar, text="Help").pack(side=RIGHT, padx=2)

        # Sidebar for categories and templates
        sidebar = Frame(main_frame, width=300)
        sidebar.grid(row=1, column=0, sticky=(N, S, W, E), padx=5, pady=5)

        # Category tree
        self.category_tree = Treeview(sidebar, height=20)
        self.category_tree.heading('#0', text='Categories')
        self.category_tree.pack(fill=Y, expand=True)
        self.category_tree.bind('<<TreeviewSelect>>', self.on_treeview_select)

        # Right-click context menus
        self.create_context_menus()

        # Main prompt editing area
        editor_frame = Frame(main_frame)
        editor_frame.grid(row=1, column=1, sticky=(N, S, W, E), pady=5)

        # Title and category
        title_frame = Frame(editor_frame)
        title_frame.pack(fill=X, pady=5)
        Label(title_frame, text="Title:").pack(side=LEFT)
        self.title_entry = Entry(title_frame)
        self.title_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        category_frame = Frame(editor_frame)
        category_frame.pack(fill=X, pady=5)
        Label(category_frame, text="Category:").pack(side=LEFT)
        self.category_entry = Entry(category_frame)
        self.category_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        # Main prompt content
        self.prompt_text = scrolledtext.ScrolledText(editor_frame, height=15)
        self.prompt_text.pack(fill=BOTH, expand=True, pady=5)

        # Variable management
        var_frame = LabelFrame(editor_frame, text="Variables")
        var_frame.pack(fill=X, pady=5)

        self.var_tree = Treeview(var_frame, columns=("name", "description", "type", "default"), height=5,
                                 show="headings")
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
        """Load categories, merging default and custom categories."""
        categories_file = os.path.join(self.prompt_folder, "categories.json")
        if os.path.exists(categories_file):
            with open(categories_file, "r") as f:
                self.categories = json.load(f)

        # Combine default categories with custom categories
        combined_categories = self.default_categories.copy()
        for custom_category, prompts in self.categories.items():
            if custom_category in combined_categories:
                combined_categories[custom_category]['subcategories'] = {
                    **combined_categories[custom_category].get('subcategories', {}),
                    **prompts
                }
            else:
                combined_categories[custom_category] = {'subcategories': prompts}

        self.categories = combined_categories

        # Populate treeview
        self.populate_treeview()

    def populate_treeview(self):
        """Populate the category tree with combined categories."""
        self.category_tree.delete(*self.category_tree.get_children())
        for category, data in self.categories.items():
            category_id = self.category_tree.insert('', 'end', text=category, values=("category",))
            for subcategory, prompts in data.get("subcategories", {}).items():
                subcategory_id = self.category_tree.insert(category_id, 'end', text=subcategory,
                                                           values=("subcategory",))
                for prompt in prompts:
                    self.category_tree.insert(subcategory_id, 'end', text=prompt, values=("prompt",))

    def load_variables_into_tree(self):
        """Load all variables into the Treeview."""
        self.var_tree.delete(*self.var_tree.get_children())
        for var in self.variables:
            self.var_tree.insert("", "end", values=(var["name"], var["description"], var["type"], var.get("default", "")))

    def add_variable(self):
        """Add a new variable using the edit dialog."""
        dialog = VariableEditDialog(self.enhancement_window)
        if dialog.result:
            self.variables.append(dialog.result)
            self.load_variables_into_tree()

    def edit_variable(self):
        """Edit the selected variable using a dialog."""
        selected_item = self.var_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a variable to edit.")
            return

        item_values = self.var_tree.item(selected_item[0], "values")
        var_index = next((i for i, var in enumerate(self.variables)
                          if var["name"] == item_values[0]), None)

        if var_index is not None:
            dialog = VariableEditDialog(self.enhancement_window, self.variables[var_index])
            if dialog.result:
                self.variables[var_index] = dialog.result
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
        """Test the current prompt with variables replaced."""
        content = self.prompt_text.get("1.0", END).strip()
        if content:
            for var in self.variables:
                content = content.replace(f"{{{{{var['name']}}}}}", var.get("default", ""))
            print("Processed Prompt:")
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
