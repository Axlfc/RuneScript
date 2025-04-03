import tempfile
import webbrowser
from tkhtmlview import HTMLLabel

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
import os
import subprocess
import markdown
import re
from pathlib import Path
from pdf2image import convert_from_path
from PIL import ImageTk, Image

from src.views.tk_utils import my_font


class LaTeXMarkdownEditor:
    def __init__(self):
        self.window = Toplevel()
        self.window.title("LaTeX & Markdown Editor")
        self.window.geometry("1400x800")

        # Project state
        self.current_project_path = None
        self.current_file = None
        self.project_files = []
        self.modified = False
        self.temp_dir = tempfile.mkdtemp()

        # Setup UI components
        self.setup_fonts()
        self.setup_menu()
        self.setup_ui()
        self.setup_bindings()
        self.setup_context_menu()

        # Initialize last saved content
        self.last_saved_content = ""

    def setup_fonts(self):
        self.editor_font = Font(family="Consolas", size=11)
        self.tree_font = Font(family="Arial", size=10)
        self.preview_font = Font(family="Times New Roman", size=11)

    def check_latex_installed(self):
        """Check if LaTeX (pdflatex) is installed and accessible"""
        try:
            subprocess.run(['pdflatex', '--version'],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False




    def new_project(self):
        """Create a new project by clearing current files and starting fresh"""
        # Confirm if the user wants to save changes before creating a new project
        if self.modified:
            if messagebox.askyesno("Save Changes", "Do you want to save changes to the current project?"):
                self.save_current_file()

        # Reset the current project state
        self.current_project_path = None
        self.current_file = None
        self.project_files = []
        self.modified = False

        # Clear the editor and project tree
        self.editor.delete("1.0", END)
        self.update_project_tree()

        # Clear the preview and details
        #self.preview.config(state="normal")
        #self.preview.delete("1.0", END)
        #self.preview.config(state="disabled")

        self.current_file_label.config(text="None")
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", END)
        self.stats_text.config(state="disabled")
        self.errors_text.config(state="normal")
        self.errors_text.delete("1.0", END)
        self.errors_text.config(state="disabled")

        messagebox.showinfo("New Project", "A new project has been created.")

    def on_editor_change(self, event=None):
        """Handle editor content changes"""
        if self.editor.edit_modified():
            current_content = self.editor.get("1.0", "end-1c")

            # Only update if content has actually changed
            if current_content != self.last_saved_content:
                self.modified = True
                self.update_preview()
                self.update_statistics()
                self.last_saved_content = current_content

            # Reset the modified flag
            self.editor.edit_modified(False)

    def compile_selected_file(self):
        """Compile the selected file in the project tree"""
        selected = self.project_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No file selected to compile")
            return

        item = selected[0]
        file_path = self.project_tree.item(item)['values'][0]
        file_ext = Path(file_path).suffix.lower()

        # Determine whether to compile a Markdown or LaTeX file
        if file_ext in ['.md', '.markdown']:
            self.compile_markdown(file_path)
        elif file_ext in ['.tex', '.latex']:
            self.compile_latex(file_path)
        else:
            messagebox.showwarning("Warning", "Unsupported file type for compilation")

    def remove_file(self):
        """Remove the selected file from the project"""
        selected = self.project_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No file selected to remove")
            return

        # Get the selected file
        item = selected[0]
        file_path = self.project_tree.item(item)['values'][0]

        # Confirm the removal
        if messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove {os.path.basename(file_path)}?"):
            try:
                # Remove the file from the project files list
                self.project_files.remove(file_path)

                # Remove the file from the project tree
                self.project_tree.delete(item)

                # Clear the editor if the current file is removed
                if self.current_file == file_path:
                    self.editor.delete("1.0", END)
                    self.current_file = None
                    self.current_file_label.config(text="None")
                    self.preview.config(state='normal')
                    self.preview.delete("1.0", END)
                    self.preview.config(state='disabled')
                    self.stats_text.config(state='normal')
                    self.stats_text.delete("1.0", END)
                    self.stats_text.config(state='disabled')

            except ValueError:
                messagebox.showerror("Error", "File not found in the project list.")

    def setup_bindings(self):
        """Setup keyboard shortcuts and other bindings"""
        # Bind F5 to recompile the document
        self.window.bind('<F5>', lambda e: self.recompile_document())

        # Bind Ctrl+S to save the current file
        self.window.bind('<Control-s>', lambda e: self.save_current_file())

        # Bind Ctrl+N to create a new project
        self.window.bind('<Control-n>', lambda e: self.new_project())

        # Bind Ctrl+F to open the find dialog
        self.window.bind('<Control-f>', lambda e: self.show_find_dialog())

        # Bind editor modifications to update the preview and statistics
        self.editor.bind('<<Modified>>', self.on_editor_change)

        # Bind the Enter key to handle newlines correctly
        self.editor.bind('<Return>', self.handle_return_key)

    def handle_return_key(self, event=None):
        """Insert a newline character when the user presses Enter."""
        self.editor.insert("insert", "\n")
        return "break"  # Ensure default event handling is stopped

    def setup_menu(self):
        """Create a menu bar with File, Edit, View options"""
        menu_bar = Menu(self.window)

        # File Menu
        file_menu = Menu(menu_bar, tearoff=0)

        # Project options
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Add LaTeX File", command=self.create_latex_file)
        file_menu.add_command(label="Add Markdown File", command=self.create_markdown_file)

        # C Project options
        file_menu.add_command(label="Add C Source File (.c)", command=self.create_c_file)
        file_menu.add_command(label="Add Header File (.h)", command=self.create_header_file)
        file_menu.add_command(label="Add Makefile", command=self.create_makefile)

        # Python Project options
        file_menu.add_command(label="Add Python Script (.py)", command=self.create_python_file)

        # Web Project options
        file_menu.add_command(label="Add HTML File", command=self.create_html_file)
        file_menu.add_command(label="Add CSS File", command=self.create_css_file)
        file_menu.add_command(label="Add JavaScript File (.js)", command=self.create_js_file)
        file_menu.add_command(label="Add Markdown Index (index.md)", command=self.create_web_index)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # View Menu (for additional viewing options, if needed)
        view_menu = Menu(menu_bar, tearoff=0)
        #view_menu.add_command(label="Project Files", command=self.toggle_project_files)
        #view_menu.add_command(label="Preview", command=self.toggle_preview)
        #view_menu.add_command(label="File Info", command=self.toggle_file_info)
        menu_bar.add_cascade(label="View", menu=view_menu)

        self.window.config(menu=menu_bar)

    def toggle_sidebar(self):
        """Toggle the visibility of the project sidebar"""
        if self.project_tree.winfo_ismapped():
            self.main_container.forget(self.project_tree.master)  # Remove the sidebar from the layout
        else:
            self.main_container.add(self.project_tree.master, weight=1)  # Add the sidebar back to the layout

    def setup_ui(self):
        # Main container
        self.main_container = PanedWindow(self.window, orient=HORIZONTAL)
        self.main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Left panel (Project Files)
        self.setup_project_panel()

        # Right panel (Editor, Preview, Details)
        self.right_paned = PanedWindow(self.main_container, orient=HORIZONTAL)
        self.main_container.add(self.right_paned)  # eliminamos weight

        self.setup_editor_panel()
        self.setup_preview_panel()
        self.setup_details_panel()

    def setup_preview_panel(self):
        preview_frame = Frame(self.right_paned)
        self.right_paned.add(preview_frame, stretch="always")

        # Preview header
        header_frame = Frame(preview_frame)
        header_frame.pack(fill=X, pady=(0, 5))

        Label(header_frame, text="Preview", font=self.tree_font).pack(side=LEFT)
        self.preview_type_label = Label(header_frame, text="")
        self.preview_type_label.pack(side=RIGHT)

        # Preview area
        self.preview = Frame(preview_frame)
        self.preview.pack(fill=BOTH, expand=True)

        # Control buttons
        btn_frame = Frame(preview_frame)
        btn_frame.pack(fill=X, pady=5)

        self.recompile_btn = Button(btn_frame, text="RECOMPILE (F5)", command=self.recompile_document)
        self.recompile_btn.pack(side=LEFT, padx=5)

        self.export_btn = Button(btn_frame, text="Export", command=self.export_preview)
        self.export_btn.pack(side=RIGHT, padx=5)

        # Add Run Python button (initially hidden) and output display for Python files
        self.run_python_btn = Button(btn_frame, text="Run Python", command=self.run_python_script)
        self.run_python_btn.pack(side=LEFT, padx=5)
        self.run_python_btn.pack_forget()  # Hide initially, only shown for Python files

        # Python output display area
        self.output_display = Text(preview_frame, height=10, wrap=WORD, state=DISABLED, font=my_font)
        self.output_display.pack(fill=BOTH, expand=True, padx=5, pady=(5, 0))

    def run_python_script(self):
        """Run the current Python script and display output in the output_display widget."""
        if not self.current_file or not self.current_file.endswith('.py'):
            messagebox.showwarning("Warning", "No Python file is open to run.")
            return

        try:
            # Clear previous output
            self.output_display.config(state=NORMAL)
            self.output_display.delete("1.0", END)
            self.output_display.insert("1.0", "Running Python script...\n")
            self.output_display.config(state=DISABLED)

            # Run the Python file and capture output
            result = subprocess.run(
                ['python', self.current_file],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.current_file)
            )

            # Display the output in the output_display widget
            self.output_display.config(state=NORMAL)
            self.output_display.insert("end", result.stdout if result.stdout else "No output\n")
            if result.stderr:
                self.output_display.insert("end", f"\nErrors:\n{result.stderr}")
            self.output_display.config(state=DISABLED)

        except Exception as e:
            self.output_display.config(state=NORMAL)
            self.output_display.insert("end", f"Failed to run script:\n{e}")
            self.output_display.config(state=DISABLED)

    def launch_server(self):
        """Launch a Python web server or Flask server on the specified port."""
        try:
            port = int(self.port_entry.get())
            if self.current_file and self.current_file.endswith('.py'):
                # Launch a Python server with Flask or SimpleHTTPServer for web files
                command = ['python', '-m', 'http.server', str(port)]
                subprocess.Popen(command, cwd=os.path.dirname(self.current_file))
                messagebox.showinfo("Server Launched", f"Server is running at http://localhost:{port}")
            else:
                messagebox.showwarning("Warning", "Select a valid Python file to run the server.")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number.")

    def export_preview(self):
        if not self.current_file:
            return

        file_ext = Path(self.current_file).suffix.lower()

        if file_ext in ['.md', '.markdown']:
            # Export as HTML
            content = self.editor.get("1.0", "end-1c")
            html_content = markdown.markdown(content, extensions=['fenced_code'])

            export_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html")],
                initialfile=os.path.splitext(os.path.basename(self.current_file))[0] + ".html"
            )

            if export_path:
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; }}
                            code {{ font-family: Consolas, monospace; }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                    </body>
                    </html>
                    """)

                webbrowser.open(f'file://{export_path}')

        elif file_ext in ['.tex', '.latex']:
            # For LaTeX, we'll just compile and open the PDF
            if self.compile_latex():
                messagebox.showinfo("Export Complete", "PDF has been generated and opened.")

    def recompile_document(self):
        """Recompile the current document based on its file type"""
        if not self.current_file:
            messagebox.showwarning("Warning", "No file is currently open")
            return

        # Ensure the editor is editable before recompiling
        self.editor.config(state='normal')

        file_ext = Path(self.current_file).suffix.lower()

        if file_ext in ['.md', '.markdown']:
            self.compile_markdown()  # Call Markdown compilation
        elif file_ext in ['.tex', '.latex']:
            self.compile_latex()  # Call LaTeX compilation
        else:
            messagebox.showwarning("Warning", "Unsupported file type for recompilation")

    def compile_markdown(self, file_path=None):
        """Compile Markdown to HTML and display it in the preview panel"""
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = self.editor.get("1.0", "end-1c")  # If no file is provided, use the editor's content

        self.preview.config(state='normal')
        self.preview.delete("1.0", "end")

        # Convert Markdown to HTML using markdown library
        html_content = markdown.markdown(content)
        self.preview.insert("1.0", html_content)
        self.preview.config(state='disabled')

        messagebox.showinfo("Recompiled", "Markdown has been recompiled to HTML.")

    def compile_latex(self, file_path=None):
        """Compile LaTeX to PDF and display it in the preview"""
        if not self.check_latex_installed():
            error_msg = """LaTeX compiler (pdflatex) not found. Please ensure that:
        1. You have a LaTeX distribution installed (e.g., MiKTeX for Windows, TexLive for Linux/Mac)
        2. The pdflatex executable is in your system's PATH
        3. You've restarted the application after installing LaTeX"""
            self.show_compilation_error(error_msg)
            messagebox.showerror("LaTeX Not Found", "LaTeX compiler not found. Please install a LaTeX distribution.")
            return False

        if file_path:
            latex_file = file_path
        else:
            latex_file = self.current_file

        if not latex_file:
            return False

        try:
            # Save current content before compilation
            if self.modified:
                self.save_current_file()

            # Compile LaTeX to PDF using pdflatex
            working_dir = os.path.dirname(latex_file)
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', latex_file],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30  # Add timeout to prevent hanging
            )

            if result.returncode == 0:
                pdf_path = os.path.splitext(latex_file)[0] + ".pdf"
                if os.path.exists(pdf_path):
                    # Render the PDF in the preview panel
                    self.show_pdf_in_preview(pdf_path)
                    return True

            self.show_compilation_error(result.stderr)
            return False

        except subprocess.TimeoutExpired:
            self.show_compilation_error("LaTeX compilation timed out after 30 seconds")
            return False
        except Exception as e:
            self.show_compilation_error(f"Compilation error: {str(e)}")
            return False

    def show_pdf_in_preview(self, pdf_path):
        """Convert PDF pages to images and display them in the preview pane."""
        try:
            # Convertir PDF a imágenes usando pdf2image
            images = convert_from_path(pdf_path)

            # Limpiar el área de vista previa y mostrar las páginas como imágenes
            self.preview.config(state='normal')
            self.preview.delete("1.0", "end")  # Limpiar el contenido anterior en la vista previa

            # Mantener referencias a imágenes para evitar que sean recolectadas
            self.preview_image_refs = []

            for i, image in enumerate(images):
                # Redimensionar imagen para que encaje en la ventana de vista previa
                image = image.resize((600, 800), Image.Resampling.LANCZOS)

                # Convertir imagen a formato compatible con Tkinter
                tk_image = ImageTk.PhotoImage(image)
                self.preview.image_create('end', image=tk_image)
                self.preview.insert('end', f"\nPage {i + 1}\n")

                # Mantener referencia para evitar eliminación por recolección de basura
                self.preview_image_refs.append(tk_image)

            self.preview.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF preview: {str(e)}")

    def setup_syntax_highlighting(self):
        """Setup syntax highlighting for LaTeX and Markdown files"""
        # Define different tags for different types of syntax
        self.editor.tag_configure("command", foreground="blue")
        self.editor.tag_configure("environment", foreground="green")
        self.editor.tag_configure("math", foreground="purple")
        self.editor.tag_configure("comment", foreground="gray")

        # Bind the key release event to apply syntax highlighting as you type
        self.editor.bind('<KeyRelease>', self.highlight_syntax)

    def highlight_syntax(self, event=None):
        """Apply syntax highlighting to the editor content"""
        content = self.editor.get("1.0", "end-1c")  # Get the full content of the editor

        # Remove any previous syntax highlighting
        self.editor.tag_remove("command", "1.0", "end")
        self.editor.tag_remove("environment", "1.0", "end")
        self.editor.tag_remove("math", "1.0", "end")
        self.editor.tag_remove("comment", "1.0", "end")

        # LaTeX commands (e.g., \command)
        for match in re.finditer(r'\\[a-zA-Z]+', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.editor.tag_add("command", start, end)

        # LaTeX environments (e.g., \begin{environment} and \end{environment})
        for match in re.finditer(r'\\begin\{.*?\}|\\end\{.*?\}', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.editor.tag_add("environment", start, end)

        # Math mode (e.g., $...$ or \[...\])
        for match in re.finditer(r'\$.*?\$|\\\[.*?\\\]', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.editor.tag_add("math", start, end)

        # Comments (e.g., lines starting with %)
        for match in re.finditer(r'%.*$', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.editor.tag_add("comment", start, end)

    def show_find_dialog(self):
        """Open a dialog window to find text in the editor"""
        find_window = Toplevel(self.window)
        find_window.title("Find Text")
        find_window.geometry("300x100")

        Label(find_window, text="Find:").pack(anchor="w", padx=10, pady=10)

        find_entry = Entry(find_window, width=30)
        find_entry.pack(padx=10, fill=X)

        def find_text():
            """Highlight all occurrences of the search term"""
            self.editor.tag_remove('found', '1.0', END)  # Remove previous highlights
            search_term = find_entry.get()

            if search_term:
                start_pos = '1.0'
                while True:
                    start_pos = self.editor.search(search_term, start_pos, stopindex=END)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(search_term)}c"
                    self.editor.tag_add('found', start_pos, end_pos)
                    start_pos = end_pos
                self.editor.tag_config('found', foreground='white', background='blue')

        ttk.Button(find_window, text="Find", command=find_text).pack(pady=10)

        def close_find_window():
            """Close the find dialog and remove the highlights"""
            self.editor.tag_remove('found', '1.0', END)
            find_window.destroy()

        find_window.protocol("WM_DELETE_WINDOW", close_find_window)

    def setup_editor_panel(self):
        editor_frame = Frame(self.right_paned)
        self.right_paned.add(editor_frame, stretch="always")

        # Editor toolbar
        toolbar = Frame(editor_frame)
        toolbar.pack(fill=X)

        Button(toolbar, text="Save", command=self.save_current_file).pack(side=LEFT, padx=2)
        Button(toolbar, text="Find", command=self.show_find_dialog).pack(side=LEFT, padx=2)

        # Source editor with line numbers
        editor_container = Frame(editor_frame)
        editor_container.pack(fill=BOTH, expand=True)

        # Line numbers
        self.line_numbers = Text(editor_container, width=4, padx=3, takefocus=0, border=0,
                                 background='lightgray', state='disabled', font=my_font)
        self.line_numbers.pack(side=LEFT, fill=Y)

        # Main editor
        self.editor = Text(editor_container, wrap=WORD, font=self.editor_font, undo=True)
        self.editor.pack(side=LEFT, fill=BOTH, expand=True)

        # Make sure the editor is enabled
        self.editor.config(state='normal')

        # Scrollbar that controls both editor and line numbers
        editor_scroll = Scrollbar(editor_container, orient=VERTICAL)
        editor_scroll.pack(side=RIGHT, fill=Y)

        # Configure scrollbar
        self.editor['yscrollcommand'] = self.on_editor_scroll
        editor_scroll['command'] = self.on_scrollbar_scroll
        self.line_numbers['yscrollcommand'] = editor_scroll.set

        # Setup syntax highlighting
        self.setup_syntax_highlighting()

        # Bind editor changes for live preview
        self.editor.bind('<<Modified>>', self.on_editor_change)
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<Return>', self.update_line_numbers)

    def on_key_release(self, event=None):
        """Handle key release events in the editor"""
        # Update line numbers
        self.update_line_numbers()
        # Update preview in real-time
        self.update_preview()
        # Update statistics
        self.update_statistics()

    def on_editor_scroll(self, *args):
        # Sync line numbers with editor
        self.line_numbers.yview_moveto(args[0])
        return args

    def on_scrollbar_scroll(self, *args):
        # Sync both text widgets with scrollbar
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def update_line_numbers(self, event=None):
        def update():
            lines = self.editor.get("1.0", "end-1c").split("\n")
            line_numbers_text = "\n".join(str(i + 1) for i in range(len(lines)))
            self.line_numbers.config(state="normal")
            self.line_numbers.delete("1.0", "end")
            self.line_numbers.insert("1.0", line_numbers_text)
            self.line_numbers.config(state="disabled")

        # Schedule the update to happen after the key event is fully processed
        self.window.after(1, update)
        return "break"

    def setup_project_panel(self):
        project_frame = Frame(self.main_container, width=250)
        project_frame.pack_propagate(False)
        self.main_container.add(project_frame)  # eliminamos weight

        # Project tree
        tree_frame = Frame(project_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        self.project_tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.project_tree.heading('#0', text='Project Files', anchor='w')
        self.project_tree.pack(side=LEFT, fill=BOTH, expand=True)

        # Scrollbar
        tree_scroll = Scrollbar(tree_frame, orient=VERTICAL, command=self.project_tree.yview)
        tree_scroll.pack(side=RIGHT, fill=Y)
        self.project_tree.configure(yscrollcommand=tree_scroll.set)

    def setup_context_menu(self):
        """Setup right-click context menu for project tree"""
        self.context_menu = Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected_file)
        self.context_menu.add_command(label="Compile", command=self.compile_selected_file)
        self.context_menu.add_command(label="Remove", command=self.remove_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)

        self.project_tree.bind("<Button-3>", self.show_context_menu)
        self.project_tree.bind("<Double-1>", lambda e: self.open_selected_file())

    def show_context_menu(self, event):
        """Show context menu at mouse position"""
        try:
            self.project_tree.selection_set(self.project_tree.identify_row(event.y))
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def show_in_explorer(self):
        """Open file explorer showing the selected file"""
        selected = self.project_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No file selected to show in Explorer")
            return

        # Get the selected file's path
        item = selected[0]
        file_path = self.project_tree.item(item)['values'][0]
        folder_path = os.path.dirname(file_path)

        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', folder_path], check=True)  # macOS uses 'open'
            elif os.name == 'linux':  # Linux
                subprocess.run(['xdg-open', folder_path], check=True)  # Linux uses 'xdg-open'
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder. Error: {str(e)}")

    def create_folder(self):
        """Create a new folder in the project"""
        folder_name = filedialog.askdirectory(title="Select Folder")
        if folder_name:
            self.project_files.append(folder_name)
            self.update_project_tree()

    def create_markdown_file(self):
        """Create a new Markdown file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown Files", "*.md")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("# New Markdown File\n\nWrite your content here...")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_latex_file(self):
        """Create a new LaTeX file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("LaTeX Files", "*.tex")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("\\documentclass{article}\n\\begin{document}\nHello LaTeX!\n\\end{document}")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_c_file(self):
        """Create a new C source file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".c", filetypes=[("C Source Files", "*.c")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("// New C Source File\n#include <stdio.h>\n\nint main() {\n    return 0;\n}")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_header_file(self):
        """Create a new header file for C projects."""
        file_path = filedialog.asksaveasfilename(defaultextension=".h", filetypes=[("Header Files", "*.h")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("// New Header File\n")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_makefile(self):
        """Create a Makefile for C projects."""
        file_path = os.path.join(self.current_project_path, "Makefile")
        with open(file_path, 'w') as f:
            f.write(
                "CC = gcc\nCFLAGS = -Wall\n\nall: main\n\nmain: main.o\n\t$(CC) $(CFLAGS) -o main main.o\n\nclean:\n\trm -f *.o main")
        self.project_files.append(file_path)
        self.update_project_tree()

    def create_python_file(self):
        """Create a new Python file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("# New Python Script\n\nif __name__ == '__main__':\n    print('Hello, World!')")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_html_file(self):
        """Create a new HTML file for web projects."""
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Files", "*.html")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(
                    "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n<title>New HTML File</title>\n<link rel=\"stylesheet\" href=\"styles.css\">\n</head>\n<body>\n<h1>Hello World!</h1>\n</body>\n</html>")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_css_file(self):
        """Create a new CSS file for styling web projects."""
        file_path = filedialog.asksaveasfilename(defaultextension=".css", filetypes=[("CSS Files", "*.css")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("/* New CSS File */\nbody { font-family: Arial, sans-serif; }")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_js_file(self):
        """Create a new JavaScript file for web projects."""
        file_path = filedialog.asksaveasfilename(defaultextension=".js", filetypes=[("JavaScript Files", "*.js")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("// New JavaScript File\nconsole.log('Hello World');")
            self.project_files.append(file_path)
            self.update_project_tree()

    def create_web_index(self):
        """Create a new Markdown index file for web projects."""
        file_path = filedialog.asksaveasfilename(defaultextension=".md", initialfile="index.md",
                                                 filetypes=[("Markdown Files", "*.md")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("# Home Page\n\nWelcome to your website!")
            self.project_files.append(file_path)
            self.update_project_tree()
    def compile_document(self, file_path):
        """Compile the document and show the result"""
        file_ext = Path(file_path).suffix.lower()
        output_path = None

        try:
            if file_ext in ['.md', '.markdown']:
                # Compile Markdown to HTML
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                html = markdown.markdown(content)
                output_path = os.path.join(self.temp_dir, os.path.basename(file_path) + '.html')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"<html><body>{html}</body></html>")

            elif file_ext in ['.tex', '.latex']:
                # Compile LaTeX to PDF
                working_dir = os.path.dirname(file_path)
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', file_path],
                    cwd=working_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.show_compilation_error(result.stderr)
                    return
                output_path = os.path.splitext(file_path)[0] + '.pdf'

            if output_path and os.path.exists(output_path):
                webbrowser.open(f'file://{output_path}')
            else:
                raise Exception("Compilation failed to produce output file")

        except Exception as e:
            self.show_compilation_error(str(e))

    def show_compilation_error(self, error_message):
        """Display LaTeX compilation errors in the errors text widget with improved formatting"""
        self.errors_text.config(state='normal')
        self.errors_text.delete("1.0", "end")

        # Format the error message for better readability
        formatted_error = "Compilation Error:\n" + "-" * 20 + "\n"

        # Extract the most relevant parts of the error message
        if "! LaTeX Error:" in error_message:
            # Extract specific LaTeX error
            error_lines = error_message.split('\n')
            for line in error_lines:
                if "! LaTeX Error:" in line:
                    formatted_error += line.strip() + "\n\n"
                    break
        else:
            # For other types of errors, show the full message
            formatted_error += error_message

        self.errors_text.insert("1.0", formatted_error)
        self.errors_text.config(state='disabled')

        # Update preview panel to show error state
        self.preview.config(state='normal')
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", "Compilation failed. Check the Errors/Warnings panel below.")
        self.preview.config(state='disabled')

    def setup_details_panel(self):
        """Setup the details panel (third column) to show file information and errors"""
        details_frame = Frame(self.right_paned)
        self.right_paned.add(details_frame, stretch="always")

        # Current file label
        Label(details_frame, text="Current File:").pack(anchor=W, pady=5)
        self.current_file_label = Label(details_frame, text="None")
        self.current_file_label.pack(anchor=W)

        # Statistics section (lines, words, characters)
        Label(details_frame, text="Statistics:", font=self.tree_font).pack(anchor=W, pady=5)
        self.stats_text = Text(details_frame, height=5, width=30, state='disabled', font=my_font)
        self.stats_text.pack(fill=X)

        # Errors/Warnings section
        Label(details_frame, text="Errors/Warnings:", font=self.tree_font).pack(anchor=W, pady=5)
        self.errors_text = Text(details_frame, height=10, width=30, state='disabled', font=my_font)
        self.errors_text.pack(fill=X)

    def open_selected_file(self):
        selected = self.project_tree.selection()
        if not selected:
            return

        item = selected[0]
        file_path = self.project_tree.item(item)['values'][0]

        # Check if it's a directory
        if os.path.isdir(file_path):
            messagebox.showinfo("Directory", "Please select a file to open, not a directory.")
            return

        # Save the current file if it has been modified
        if self.modified:
            self.save_current_file()

        self.current_file = file_path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Always enable the editor for editing when switching files
                self.editor.config(state='normal')  # Enable editing for both LaTeX and Markdown files

                # Clear the editor and load the new content
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", content)
                self.last_saved_content = content  # Keep track of the last saved content

            # Update the current file label
            self.current_file_label.config(text=os.path.basename(file_path))
            self.modified = False

            # Show "Run Python" button if it is a Python file, otherwise hide it
            if self.current_file.endswith('.py'):
                self.run_python_btn.pack(side=LEFT, padx=5)
            else:
                self.run_python_btn.pack_forget()

            # Update the preview and statistics based on file type
            self.update_preview()
            self.update_statistics()
            self.update_line_numbers()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def update_preview(self):
        """Update the preview panel with the current editor content"""
        if not self.current_file:
            return

        content = self.editor.get("1.0", "end-1c")
        file_ext = Path(self.current_file).suffix.lower()

        try:
            if file_ext in ['.md', '.markdown']:
                self.preview_type_label.config(text="Markdown Preview")
                html_content = markdown.markdown(content, extensions=['fenced_code'])
                self.render_html_in_preview(html_content)

            elif file_ext in ['.tex', '.latex']:
                self.preview_type_label.config(text="LaTeX Preview")
                self.render_html_in_preview("LaTeX preview available after compilation (F5)")

        except Exception as e:
            self.render_html_in_preview(f"Preview Error: {str(e)}")

    def render_html_in_preview(self, html_content):
        """Render the HTML content in the preview panel."""
        # Clear any existing content in the preview
        for widget in self.preview.winfo_children():
            widget.destroy()

        # Create a new HTMLLabel widget to display the HTML content
        html_label = HTMLLabel(self.preview, html=html_content)
        html_label.pack(fill=BOTH, expand=True)

    def update_statistics(self):
        """Update the statistics in the details panel based on the editor content"""
        content = self.editor.get("1.0", "end-1c")

        # Calculate statistics
        lines = len(content.splitlines())
        words = len(content.split())
        chars = len(content)

        # Update statistics display
        self.stats_text.config(state='normal')
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", f"Lines: {lines}\n")
        self.stats_text.insert("end", f"Words: {words}\n")
        self.stats_text.insert("end", f"Characters: {chars}\n")
        self.stats_text.config(state='disabled')

    def save_current_file(self):
        if self.current_file and self.modified:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                content = self.editor.get("1.0", "end-1c")
                f.write(content)
            self.modified = False
            self.last_saved_content = content
            return True
        return False

    def update_project_tree(self):
        """Update the project tree with the current project files"""
        self.project_tree.delete(*self.project_tree.get_children())
        for file in self.project_files:
            self.project_tree.insert('', 'end', text=os.path.basename(file), values=[file])

    # Additional methods for editor, syntax highlighting, preview updates, and error handling follow.
