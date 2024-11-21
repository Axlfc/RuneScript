import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import queue
import threading
import time
import uuid
from datetime import datetime


class ProjectWindow:
    def __init__(self, root=None):
        if root is None:
            root = tk.Tk()

        self.root = root
        self.root.title("AI Project Generator")
        self.root.geometry("1600x1000")

        # Project state
        self.current_project_path = None
        self.config = self.load_config()

        # UI state
        self.ui_queue = queue.Queue()
        self.setup_ui()

        # Start queue monitoring
        self.root.after(100, self.process_ui_queue)

    def load_config(self):
        """Load or create configuration file"""
        config_path = 'data/project_generator_config.json'
        default_config = {
            'recent_projects': [],
            'default_project_dir': os.path.join(os.path.expanduser('~'), 'AIProjects')
        }

        try:
            os.makedirs('data', exist_ok=True)
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return default_config
        except Exception as e:
            self.log_error(f"Config load error: {e}")
            return default_config

    def setup_ui(self):
        """Initialize the main UI components"""
        # Create main container with adjustable panels
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: Project tree
        self.setup_project_tree()

        # Right panel container
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_paned)

        # Editor area
        self.setup_editor()

        # Output and status area
        self.setup_output_area()

        # Command bar
        self.setup_command_bar()

        # Initialize styles
        self.setup_styles()

    def setup_project_tree(self):
        """Setup the project file tree panel"""
        tree_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(tree_frame)

        # Tree label
        tree_label = ttk.Label(tree_frame, text="Project Files", style='Header.TLabel')
        tree_label.pack(fill=tk.X, padx=5, pady=5)

        # Create treeview with scrollbar
        self.tree = ttk.Treeview(tree_frame, show='tree')
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-3>', self.show_context_menu)

    def setup_editor(self):
        """Setup the code editor area"""
        editor_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(editor_frame)

        # Editor label
        editor_label = ttk.Label(editor_frame, text="Editor", style='Header.TLabel')
        editor_label.pack(fill=tk.X, padx=5, pady=5)

        # Create editor with syntax highlighting
        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.editor.pack(fill=tk.BOTH, expand=True)

    def setup_output_area(self):
        """Setup the output and status area"""
        output_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(output_frame)

        # Output label
        output_label = ttk.Label(output_frame, text="Output", style='Header.TLabel')
        output_label.pack(fill=tk.X, padx=5, pady=5)

        # Create output text area
        self.output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#2d2d2d',
            fg='#cccccc'
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_command_bar(self):
        """Setup the command input area"""
        cmd_frame = ttk.Frame(self.root)
        cmd_frame.pack(fill=tk.X, padx=10, pady=5)

        # Project prompt input
        ttk.Label(cmd_frame, text="Project Prompt:").pack(side=tk.LEFT, padx=(0, 5))
        self.prompt_entry = ttk.Entry(cmd_frame, width=60)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Buttons
        self.generate_btn = ttk.Button(
            cmd_frame,
            text="Generate Project",
            command=self.start_project_generation
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            cmd_frame,
            text="Stop",
            command=self.stop_generation,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()

        # Header style
        style.configure(
            'Header.TLabel',
            font=('Segoe UI', 10, 'bold'),
            background='#2d2d2d',
            foreground='white',
            padding=5
        )

        # Button styles
        style.configure(
            'TButton',
            padding=5
        )

    def start_project_generation(self):
        """Handle project generation start"""
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter a project prompt")
            return

        # Create project directory
        project_name = f"{prompt.split()[0].lower()}_{uuid.uuid4().hex[:8]}"
        project_path = os.path.join(self.config['default_project_dir'], project_name)

        # Update UI
        self.toggle_ui_state(False)
        self.log_info(f"Starting project generation: {project_name}")
        self.update_status(f"Generating project: {project_name}")

        # Start generation in thread
        threading.Thread(
            target=self.generate_project,
            args=(project_path, prompt),
            daemon=True
        ).start()

    def generate_project(self, path, prompt):
        """Generate project structure and files"""
        try:
            # Create basic structure
            os.makedirs(path, exist_ok=True)
            for dir_name in ['src', 'tests', 'docs', 'config']:
                os.makedirs(os.path.join(path, dir_name))

            # Create initial files
            self.create_initial_files(path, prompt)

            # Update UI
            self.current_project_path = path
            self.ui_queue.put(('update_tree', None))
            self.log_success(f"Project created at: {path}")

            # Start mock AI process for demonstration
            self.simulate_ai_progress()

        except Exception as e:
            self.log_error(f"Project generation failed: {e}")
        finally:
            self.ui_queue.put(('enable_ui', None))

    def create_initial_files(self, path, prompt):
        """Create initial project files"""
        files = {
            'README.md': f"# {prompt}\n\nProject generated by AI Project Generator",
            'src/__init__.py': '',
            'tests/__init__.py': '',
            'config/settings.py': '# Project configuration',
            'docs/api.md': '# API Documentation'
        }

        for file_path, content in files.items():
            full_path = os.path.join(path, file_path)
            with open(full_path, 'w') as f:
                f.write(content)
            self.log_info(f"Created: {file_path}")

    def simulate_ai_progress(self):
        """Simulate AI progress for demonstration"""
        stages = [
            ("Analyzing project requirements...", 1),
            ("Generating project structure...", 1),
            ("Creating initial tests...", 1),
            ("Implementing core functionality...", 2),
            ("Running tests...", 1),
            ("Finalizing project...", 1)
        ]

        for message, delay in stages:
            self.update_status(message)
            self.log_info(message)
            time.sleep(delay)

    def update_tree(self):
        """Update project tree view"""
        self.tree.delete(*self.tree.get_children())

        if not self.current_project_path:
            return

        def insert_path(parent, path):
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)

                icon = "📁 " if is_dir else "📄 "
                node = self.tree.insert(
                    parent,
                    'end',
                    text=f"{icon}{item}",
                    values=(item_path,)
                )

                if is_dir:
                    insert_path(node, item_path)

        insert_path('', self.current_project_path)

    def process_ui_queue(self):
        """Process UI update queue"""
        try:
            while True:
                command, data = self.ui_queue.get_nowait()

                if command == 'log':
                    self.write_to_output(data)
                elif command == 'status':
                    self.status_var.set(data)
                elif command == 'update_tree':
                    self.update_tree()
                elif command == 'enable_ui':
                    self.toggle_ui_state(True)
                elif command == 'disable_ui':
                    self.toggle_ui_state(False)

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_ui_queue)

    def toggle_ui_state(self, enabled):
        """Toggle UI elements state"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.config(state=state)
        self.generate_btn.config(state=state)
        self.stop_btn.config(state=tk.DISABLED if enabled else tk.NORMAL)

    def write_to_output(self, message):
        """Write formatted message to output"""
        self.output.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if "[ERROR]" in message:
            tag = 'error'
            color = '#ff6b6b'
        elif "[SUCCESS]" in message:
            tag = 'success'
            color = '#69db7c'
        else:
            tag = 'info'
            color = '#cccccc'

        self.output.tag_config(tag, foreground=color)
        self.output.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def log_info(self, message):
        """Log information message"""
        self.ui_queue.put(('log', f"[INFO] {message}"))

    def log_error(self, message):
        """Log error message"""
        self.ui_queue.put(('log', f"[ERROR] {message}"))

    def log_success(self, message):
        """Log success message"""
        self.ui_queue.put(('log', f"[SUCCESS] {message}"))

    def update_status(self, message):
        """Update status bar message"""
        self.ui_queue.put(('status', message))

    def stop_generation(self):
        """Stop project generation"""
        self.log_info("Stopping project generation...")
        self.update_status("Stopping...")
        self.toggle_ui_state(True)

    def on_tree_select(self, event):
        """Handle tree item selection"""
        selection = self.tree.selection()
        if not selection:
            return

        item_path = self.tree.item(selection[0])['values'][0]
        if os.path.isfile(item_path):
            try:
                with open(item_path, 'r') as f:
                    content = f.read()
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', content)
                self.update_status(f"Opened: {os.path.basename(item_path)}")
            except Exception as e:
                self.log_error(f"Failed to open file: {e}")

    def show_context_menu(self, event):
        """Show context menu for tree items"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="New File", command=self.new_file)
        menu.add_command(label="New Folder", command=self.new_folder)
        menu.add_separator()
        menu.add_command(label="Delete", command=self.delete_item)
        menu.post(event.x_root, event.y_root)

    def new_file(self):
        """Create new file"""
        if not self.current_project_path:
            messagebox.showwarning("Warning", "No project open")
            return

        name = messagebox.askstring("New File", "Enter file name:")
        if name:
            path = os.path.join(self.current_project_path, name)
            try:
                with open(path, 'w') as f:
                    f.write('')
                self.update_tree()
                self.log_success(f"Created file: {name}")
            except Exception as e:
                self.log_error(f"Failed to create file: {e}")

    def new_folder(self):
        """Create new folder"""
        if not self.current_project_path:
            messagebox.showwarning("Warning", "No project open")
            return

        name = messagebox.askstring("New Folder", "Enter folder name:")
        if name:
            path = os.path.join(self.current_project_path, name)
            try:
                os.makedirs(path)
                self.update_tree()
                self.log_success(f"Created folder: {name}")
            except Exception as e:
                self.log_error(f"Failed to create folder: {e}")

    def delete_item(self):
        """Delete selected item"""
        selection = self.tree.selection()
        if not selection:
            return

        item_path = self.tree.item(selection[0])['values'][0]
        name = os.path.basename(item_path)

        if messagebox.askyesno("Confirm Delete", f"Delete {name}?"):
            try:
                if os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                self.update_tree()
                self.log_success(f"Deleted: {name}")
            except Exception as e:
                self.log_error(f"Failed to delete {name}: {e}")

    def run_project(self):
        """Run the current project"""
        if not self.current_project_path:
            messagebox.showwarning("Warning", "No project open")
            return

        self.log_info("Running project...")
        self.update_status("Running project...")

        # Simulate project running
        threading.Thread(target=self.simulate_project_run, daemon=True).start()

    def simulate_project_run(self):
        """Simulate project running for demonstration"""
        stages = [
            "Initializing project...",
            "Running tests...",
            "Starting application...",
            "Project running successfully!"
        ]

        for stage in stages:
            self.update_status(stage)
            self.log_info(stage)
            time.sleep(1)

        self.update_status("Ready")

    def save_current_file(self):
        """Save currently open file"""
        selection = self.tree.selection()
        if not selection:
            return

        item_path = self.tree.item(selection[0])['values'][0]
        if os.path.isfile(item_path):
            try:
                content = self.editor.get('1.0', tk.END)
                with open(item_path, 'w') as f:
                    f.write(content)
                self.log_success(f"Saved: {os.path.basename(item_path)}")
            except Exception as e:
                self.log_error(f"Failed to save file: {e}")

    def quit_application(self):
        """Quit the application"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.root.quit()

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = """AI Project Generator
Version 1.0

A tool for generating and managing AI-driven projects.
"""
        messagebox.showinfo("About", about_text)

    def create_menubar(self):
        """Create application menubar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.start_project_generation)
        file_menu.add_command(label="Save", command=self.save_current_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)

        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Project", command=self.run_project)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-s>', lambda e: self.save_current_file())
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-q>', lambda e: self.quit_application())
        self.prompt_entry.bind('<Return>', lambda e: self.start_project_generation())

    def run(self):
        """Start the application"""
        self.create_menubar()
        self.bind_shortcuts()
        self.root.mainloop()


if __name__ == '__main__':
    app = ProjectWindow()
    app.run()