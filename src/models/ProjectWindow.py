import os
import re
import shutil
import string
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import json
import queue
import threading
import time
import uuid
from datetime import datetime


def _check_duplicates(content, existing_features, log_func=None):
    """Check for duplicate function or class definitions."""
    # Ensure content is a string
    if not isinstance(content, str):
        content = str(content)

    # Regex pattern for function/class definitions
    pattern = r'\b(def|class)\s+(\w+)\b'
    new_definitions = set(re.findall(pattern, content))

    for feature in existing_features:
        if not isinstance(feature, str):  # Skip non-string features
            continue
        existing_definitions = set(re.findall(pattern, feature))
        if new_definitions & existing_definitions:  # Overlap of names
            if log_func:
                log_func(f"[WARNING] Duplicate function/class detected: {new_definitions & existing_definitions}")
            return True
    return False


def _validate_names(content):
    """Ensure function and variable names are descriptive and meaningful."""
    invalid_names = re.findall(r'\bdef\s+(f|x|y|temp|tmp|test)\b', content)  # Example pattern for poor names
    if invalid_names:
        raise ValueError(f"Found invalid or undescriptive names: {', '.join(invalid_names)}")


class InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, callback):
        super().__init__(parent)
        self.title(title)
        self.callback = callback

        self.label = ttk.Label(self, text=prompt)
        self.label.pack(padx=10, pady=10)

        self.entry = ttk.Entry(self)
        self.entry.pack(padx=10, pady=10)
        self.entry.focus()

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=10)

        self.ok_button = ttk.Button(self.button_frame, text="OK", command=self.on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Center the window
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
        self.transient(parent)
        self.grab_set()  # Optional: make the dialog modal to the parent window

    def on_ok(self):
        value = self.entry.get()
        self.callback(value)
        self.destroy()

    def on_cancel(self):
        self.callback(None)
        self.destroy()


class ProjectAnalyzer:
    """Analyzes project requirements and generates appropriate structures."""

    def __init__(self, prompt):
        self.prompt = prompt.lower()
        self.keywords = self._extract_keywords()
        self.features = self._analyze_prompt()
        self.feature_backlog = self._generate_feature_backlog()

    def _generate_feature_backlog(self):
        """Generate a feature backlog based on the prompt."""
        # Example: Analyze the prompt to extract features
        # You can enhance this logic to make it more comprehensive
        features = [
            {"name": "Create API Endpoints", "status": "pending"},
            {"name": "Build Data Models", "status": "pending"},
            {"name": "Implement UI", "status": "pending"},
            {"name": "Add Utility Functions", "status": "pending"}
        ]
        return features

    def _extract_keywords(self):
        """Extract relevant keywords from the prompt."""
        # Common development patterns and their related keywords
        patterns = {
            'web': ['web', 'http', 'api', 'rest', 'flask', 'django', 'server'],
            'data': ['database', 'sql', 'nosql', 'data', 'analysis', 'processing'],
            'gui': ['gui', 'interface', 'ui', 'desktop', 'window', 'tkinter', 'qt'],
            'cli': ['command', 'cli', 'terminal', 'console'],
            'ai': ['ai', 'ml', 'machine learning', 'neural', 'prediction'],
        }

        found_patterns = set()
        for category, keywords in patterns.items():
            if any(keyword in self.prompt for keyword in keywords):
                found_patterns.add(category)

        return found_patterns

    def _analyze_prompt(self):
        """Extract required features from the project prompt."""
        # This would typically use AI to analyze the prompt
        # For now, using a simple implementation
        features = []

        # Core features every project needs
        features.extend([
            'Configuration',
            'Logging',
            'ErrorHandling'
        ])

        # Extract additional features from prompt
        # This is where you'd integrate more sophisticated AI analysis
        words = self.prompt.lower().split()
        if 'api' in words:
            features.extend(['APIEndpoints', 'RequestHandling'])
        if 'database' in words:
            features.extend(['DatabaseConnection', 'DataModels'])
        if 'user' in words:
            features.extend(['UserAuthentication', 'UserManagement'])

        return features

    def get_feature_list(self):
        """Get the list of features to implement."""
        return self.features.copy()

    def _generate_routes(self):
        """Generate API routes template."""
        return '''
from flask import Blueprint, jsonify, request

api = Blueprint('api', __name__)

@api.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@api.route('/api/v1/resource', methods=['GET'])
def get_resource():
    """Get resource endpoint"""
    return jsonify({"message": "Resource retrieved"})

@api.route('/api/v1/resource', methods=['POST'])
def create_resource():
    """Create resource endpoint"""
    data = request.get_json()
    return jsonify({"message": "Resource created", "data": data}), 201
'''

    def _generate_models(self):
        """Generate database models template."""
        return '''
from datetime import datetime
from typing import Optional, Dict, Any

class BaseModel:
    """Base model class"""
    def __init__(self):
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Resource(BaseModel):
    """Example resource model"""
    def __init__(self, name: str, description: Optional[str] = None):
        super().__init__()
        self.name = name
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "description": self.description
        })
        return base_dict
'''

    def _generate_processors(self):
        """Generate data processors template."""
        return '''
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Base data processor class"""

    def __init__(self):
        self.logger = logger

    def process(self, data: Any) -> Dict[str, Any]:
        """Process input data"""
        self.logger.info("Processing data")
        return self._process_implementation(data)

    def _process_implementation(self, data: Any) -> Dict[str, Any]:
        """Implementation of data processing"""
        raise NotImplementedError("Subclasses must implement processing logic")

class JsonProcessor(DataProcessor):
    """JSON data processor"""

    def _process_implementation(self, data: Any) -> Dict[str, Any]:
        """Process JSON data"""
        if isinstance(data, dict):
            return {"processed": data}
        raise ValueError("Input must be a dictionary")
'''

    def _generate_windows(self):
        """Generate UI windows template."""
        return '''
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

class BaseWindow:
    """Base window class"""

    def __init__(self, title: str = "Window", geometry: str = "800x600"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(geometry)
        self.setup_ui()

    def setup_ui(self):
        """Setup UI components"""
        raise NotImplementedError("Subclasses must implement UI setup")

    def run(self):
        """Run the window"""
        self.root.mainloop()

class MainWindow(BaseWindow):
    """Main application window"""

    def setup_ui(self):
        """Setup main window UI"""
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Menu bar
        self.setup_menu()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_menu(self):
        """Setup menu bar"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
'''

    def _generate_widgets(self):
        """Generate UI widgets template."""
        return '''
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any

class BaseWidget(ttk.Frame):
    """Base widget class"""

    def __init__(self, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_widget()

    def setup_widget(self):
        """Setup widget components"""
        raise NotImplementedError("Subclasses must implement widget setup")

class DataEntryWidget(BaseWidget):
    """Data entry form widget"""

    def __init__(self, master: Any, callback: Optional[Callable] = None, **kwargs):
        self.callback = callback
        super().__init__(master, **kwargs)

    def setup_widget(self):
        """Setup data entry form"""
        # Label
        self.label = ttk.Label(self, text="Enter data:")
        self.label.pack(padx=5, pady=5)

        # Entry
        self.entry = ttk.Entry(self)
        self.entry.pack(padx=5, pady=5)

        # Submit button
        self.submit_btn = ttk.Button(
            self,
            text="Submit",
            command=self._on_submit
        )
        self.submit_btn.pack(padx=5, pady=5)

    def _on_submit(self):
        """Handle submit button click"""
        if self.callback:
            self.callback(self.entry.get())
        self.entry.delete(0, tk.END)
'''

    def generate_project_structure(self):
        """Generate appropriate project structure based on analysis."""
        base_structure = {
            'src': {
                '__init__.py': '',
                'core': {
                    '__init__.py': '',
                    'exceptions.py': self._generate_exceptions(),
                    'utils.py': self._generate_utils(),
                }
            },
            'tests': {
                '__init__.py': '',
                'conftest.py': self._generate_conftest(),
            },
            'requirements.txt': self._generate_requirements(),
            'README.md': self._generate_readme(),
            '.gitignore': self._generate_gitignore(),
        }

        # Add pattern-specific directories and files
        if 'web' in self.keywords:
            base_structure['src']['api'] = {
                '__init__.py': '',
                'routes.py': self._generate_routes(),
                'models.py': self._generate_models(),
            }

        if 'data' in self.keywords:
            base_structure['src']['data'] = {
                '__init__.py': '',
                'processors.py': self._generate_processors(),
                'schema.py': self._generate_schema(),
            }

        if 'gui' in self.keywords:
            base_structure['src']['ui'] = {
                '__init__.py': '',
                'windows.py': self._generate_windows(),
                'widgets.py': self._generate_widgets(),
            }

        return base_structure

    def _generate_exceptions(self):
        """Generate custom exceptions."""
        return '''
class ProjectError(Exception):
    """Base exception for project-specific errors"""
    pass

class ValidationError(ProjectError):
    """Raised when validation fails"""
    pass

class ProcessingError(ProjectError):
    """Raised when processing fails"""
    pass
'''

    def _generate_utils(self):
        """Generate utility functions."""
        return '''
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the project"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def validate_input(data: Any) -> bool:
    """Validate input data"""
    # TODO: Implement input validation
    return True

def process_data(data: Any) -> Dict[str, Any]:
    """Process input data"""
    # TODO: Implement data processing
    return {"processed": data}
'''

    def _generate_conftest(self):
        """Generate pytest configuration."""
        return '''
import pytest
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def sample_data():
    """Provide sample data for tests"""
    return {
        "test": "data"
    }
'''

    def _generate_requirements(self):
        """Generate requirements.txt content."""
        base_reqs = ['pytest>=7.0.0', 'pytest-cov>=4.0.0']
        if 'web' in self.keywords:
            base_reqs.extend(['flask>=2.0.0', 'requests>=2.0.0'])
        if 'data' in self.keywords:
            base_reqs.extend(['pandas>=1.0.0', 'numpy>=1.0.0'])
        if 'gui' in self.keywords:
            base_reqs.append('PyQt6>=6.0.0')
        return '\n'.join(base_reqs)

    def _generate_readme(self):
        """Generate README.md content."""
        return f'''# {self.prompt.title()}

Generated by AI Project Generator

## Project Structure
```
{self._generate_structure_tree()}
```

## Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment
4. Install requirements: `pip install -r requirements.txt`

## Testing
Run tests with: `pytest tests/`

## License
MIT
'''

    def _generate_structure_tree(self):
        """Generate ASCII tree of project structure."""
        structure = ['project/', '├── src/', '│   └── core/', '├── tests/']
        if 'web' in self.keywords:
            structure.insert(2, '│   └── api/')
        if 'data' in self.keywords:
            structure.insert(2, '│   └── data/')
        if 'gui' in self.keywords:
            structure.insert(2, '│   └── ui/')
        return '\n'.join(structure)

    def _generate_gitignore(self):
        """Generate .gitignore content."""
        return '''*.pyc
__pycache__/
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.pytest_cache/
'''


class ProjectWindow:
    def __init__(self, root=None):
        if root is None:
            root = tk.Tk()

        self.root = root
        self.root.title("AI Project Generator")
        self.root.geometry("600x800")

        # Project state
        self.current_project_path = None
        self.config = self.load_config()
        self.generation_active = False
        self.analyzer = None
        self.paused = False
        self.expanded_nodes = set()  # Track expanded nodes

        # UI state
        self.ui_queue = queue.Queue()
        self.setup_ui()

        # Start queue monitoring
        self.root.after(100, self.process_ui_queue)

    def load_config(self):
        """Load or create configuration file."""
        config_path = 'data/project_generator_config.json'
        default_config = {
            'recent_projects': [],
            'default_project_dir': os.path.join('data', 'projects')
        }

        try:
            os.makedirs('data', exist_ok=True)
            os.makedirs(default_config['default_project_dir'], exist_ok=True)  # Ensure directory exists
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return default_config
        except Exception as e:
            self.log_error(f"Config load error: {e}")
            return default_config

    def setup_ui(self):
        """Initialize the main UI components."""
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.setup_project_tree()
        self.setup_right_panel()

        self.setup_command_bar()
        self.setup_styles()

    def setup_project_tree(self):
        """Setup the project file tree panel with improved state management."""
        tree_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(tree_frame)

        tree_header = ttk.Frame(tree_frame)
        tree_header.pack(fill=tk.X, padx=5, pady=5)

        tree_label = ttk.Label(tree_header, text="Project Files", style='Header.TLabel')
        tree_label.pack(side=tk.LEFT)

        # Create tree with full height display
        self.tree = ttk.Treeview(tree_frame, show='tree', selectmode='browse', height=20)

        # Add scrollbars for both vertical and horizontal scrolling
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack scrollbars and tree with proper fill and expand
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<<TreeviewOpen>>', self.on_node_expanded)
        self.tree.bind('<<TreeviewClose>>', self.on_node_collapsed)

    def on_node_expanded(self, event):
        """Track expanded nodes."""
        item = self.tree.focus()
        self.expanded_nodes.add(item)

    def on_node_collapsed(self, event):
        """Track collapsed nodes."""
        item = self.tree.focus()
        self.expanded_nodes.discard(item)

    def show_context_menu(self, event):
        """Show context menu for tree items"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="New File", command=self.new_file)
        menu.add_command(label="New Folder", command=self.new_folder)
        menu.add_separator()
        menu.add_command(label="Delete", command=self.delete_item)
        menu.post(event.x_root, event.y_root)

    def setup_right_panel(self):
        """Setup the right panel for editor and output."""
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_paned)

        self.setup_editor()
        self.setup_output_area()

    def setup_editor(self):
        """Setup the code editor area."""
        editor_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(editor_frame)

        editor_label = ttk.Label(editor_frame, text="Editor", style='Header.TLabel')
        editor_label.pack(fill=tk.X, padx=5, pady=5)

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
        """Setup the output and status area."""
        output_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(output_frame)

        output_label = ttk.Label(output_frame, text="Output", style='Header.TLabel')
        output_label.pack(fill=tk.X, padx=5, pady=5)

        self.output = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#2d2d2d',
            fg='#cccccc'
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_command_bar(self):
        """Setup the command input area with pause functionality."""
        cmd_frame = ttk.Frame(self.root)
        cmd_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(cmd_frame, text="Project Prompt:").pack(side=tk.LEFT, padx=(0, 5))
        self.prompt_entry = ttk.Entry(cmd_frame, width=50)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        button_frame = ttk.Frame(cmd_frame)
        button_frame.pack(side=tk.LEFT, padx=5)

        self.generate_btn = ttk.Button(
            button_frame,
            text="Generate Project",
            command=self.start_project_generation
        )
        self.generate_btn.pack(side=tk.LEFT, padx=2)

        self.pause_btn = ttk.Button(
            button_frame,
            text="⏸️ Pause",
            command=self.toggle_pause,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹️ Stop",
            command=self.stop_generation,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

    def toggle_pause(self):
        """Toggle pause state for file inspection."""
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.configure(text="▶️ Resume")
            self.update_status("Paused - Inspect files freely")
        else:
            self.pause_btn.configure(text="⏸️ Pause")
            self.update_status("Resumed generation")
            self.update_tree(force=True)

    def setup_styles(self):
        """Setup ttk styles."""
        style = ttk.Style()
        style.configure(
            'Header.TLabel',
            font=('Segoe UI', 10, 'bold'),
            background='#2d2d2d',
            foreground='white',
            padding=5
        )
        style.configure(
            'TButton',
            padding=5
        )

    def start_project_generation(self):
        """Handle project generation start with pause support."""
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter a project prompt")
            return

        project_id = uuid.uuid4().hex[:8]
        project_name = f"{prompt.split()[0].lower()}_{project_id}"
        project_path = os.path.join(self.config['default_project_dir'], project_name)

        try:
            os.makedirs(project_path, exist_ok=True)
            self.current_project_path = project_path
            self.update_tree(force=True)

            self.toggle_ui_state(False)
            self.log_info(f"Starting project generation: {project_name}")
            self.update_status(f"Generating project: {project_name}")
            self.paused = False
            self.pause_btn.configure(text="⏸️ Pause")

            threading.Thread(
                target=self.generate_project,
                args=(project_path, prompt),
                daemon=True
            ).start()
        except Exception as e:
            self.log_error(f"Failed to initialize project directory: {e}")

    def generate_project(self, path, prompt):
        """Generate project using TDD methodology with improved thread safety."""
        try:
            self.generation_active = True
            self.analyzer = ProjectAnalyzer(prompt)

            # Initialize project structure
            self.ui_queue.put(('status', "Initializing project structure..."))
            structure = self.analyzer.generate_project_structure()
            self._create_structure(path, structure)

            # Get list of features to implement
            features = self.analyzer.get_feature_list()
            self.ui_queue.put(('log', f"[INFO] Features to implement: {', '.join(features)}"))

            # TDD Cycle for each feature
            for feature in features:
                if not self.generation_active:
                    break

                while self.paused:
                    time.sleep(0.1)
                    continue

                self._execute_tdd_cycle(path, feature)
                time.sleep(0.5)  # Prevent UI overload

        except Exception as e:
            self.ui_queue.put(('log', f"[ERROR] Project generation failed: {e}"))
        finally:
            self.generation_active = False
            self.ui_queue.put(('enable_ui', None))

    def _execute_tdd_cycle(self, path, feature):
        """Execute a single TDD cycle for a feature with improved error handling and backup support."""
        try:
            # Red Phase
            self.ui_queue.put(('status', f"Red Phase: Writing tests for {feature}"))
            test_file = os.path.join(path, 'tests', f'test_{feature.lower()}.py')
            test_content = self._generate_test_content(feature)
            if test_content:
                self._create_file(test_file, test_content, "Created test file")
                time.sleep(0.5)  # Allow UI to update

            # Green Phase
            self.ui_queue.put(('status', f"Green Phase: Implementing {feature}"))
            impl_file = os.path.join(path, 'src', 'core', f'{feature.lower()}.py')
            impl_content = self._generate_implementation(feature, test_content)
            if impl_content:
                self._create_file(impl_file, impl_content, "Created implementation")

                # Verify implementation
                if not self._verify_implementation(path, feature, impl_file):
                    self.log_error(f"Initial implementation failed tests for {feature}")
                    return False

                time.sleep(0.5)  # Allow UI to update

            # Refactor Phase
            if impl_content and self._should_refactor(impl_content):
                self.ui_queue.put(('status', f"Refactor Phase: Improving {feature}"))

                # Create backup before refactoring
                backup_path = self._backup_file(impl_file)

                refactored_content = self._generate_refactored_code(impl_content)
                if refactored_content:
                    self._create_file(impl_file, refactored_content, "Refactored implementation")

                    # Verify refactored implementation
                    if not self._verify_implementation(path, feature, impl_file):
                        self.log_error(f"Refactored implementation failed tests for {feature}")
                        # Restore backup if tests fail
                        if self._restore_backup(backup_path, impl_file):
                            self.log_info(f"Restored previous working implementation for {feature}")
                        return False

                    # Remove backup if everything succeeded
                    if backup_path and os.path.exists(backup_path):
                        os.remove(backup_path)

            self.ui_queue.put(('log', f"[SUCCESS] Completed TDD cycle for {feature}"))
            return True

        except Exception as e:
            self.ui_queue.put(('log', f"[ERROR] TDD cycle failed for {feature}: {e}"))
            return False

    def _generate_test_content(self, feature):
        """Generate test content using AI assistant."""
        prompt = f"""
        Write a comprehensive test suite for the {feature} feature.
        Include:
        - Basic functionality tests
        - Edge cases
        - Error conditions
        Follow pytest best practices and include necessary imports.
        """
        response = self.process_prompt_with_ai(prompt)
        return self._extract_code_blocks(response)  # Clean extracted code

    def _generate_implementation(self, feature, test_content):
        """Generate implementation based on test requirements."""
        prompt = f"""
        Implement the {feature} feature to pass these tests:
        {test_content}

        Focus on:
        - Clean, maintainable code
        - Proper error handling
        - Clear documentation
        """
        response = self.process_prompt_with_ai(prompt)
        return self._extract_code_blocks(response)  # Clean extracted code

    def _should_refactor(self, code):
        """Analyze if code needs refactoring."""
        # Basic heuristics for refactoring need
        code_lines = code.split('\n')
        return (
                len(code_lines) > 20 or  # Code is getting long
                len([l for l in code_lines if l.strip().startswith('def ')]) > 3 or  # Many functions
                len([l for l in code_lines if ' = ' in l]) > 10  # Many variables
        )

    def _generate_refactored_code(self, original_code):
        """Generate refactored version of the code using AI assistant."""
        prompt = f"""
        Refactor this code to improve its quality while maintaining functionality:
        {original_code}

        Focus on:
        - Improving readability
        - Reducing complexity
        - Following SOLID principles
        - Applying design patterns where appropriate
        - Maintaining test compatibility

        Return only the refactored code without explanations.
        """
        refactored = self.process_prompt_with_ai(prompt)

        if not refactored:
            self.log_error("Failed to generate refactored code")
            return None

        # Clean up the response
        cleaned_code = self._extract_code_blocks(refactored)
        if not cleaned_code:
            return original_code  # Return original if cleaning fails

        return cleaned_code

    def _run_tests_for_feature(self, path, feature):
        """Run tests for a specific feature and return results."""
        try:
            test_file = os.path.join(path, 'tests', f'test_{feature.lower()}.py')
            if not os.path.exists(test_file):
                self.log_error(f"Test file not found for {feature}")
                return False

            # Run pytest for the specific test file
            result = subprocess.run(
                ['pytest', test_file, '-v'],
                capture_output=True,
                text=True,
                cwd=path
            )

            # Log test results
            if result.returncode == 0:
                self.log_success(f"Tests passed for {feature}")
                return True
            else:
                self.log_error(f"Tests failed for {feature}:\n{result.stdout}")
                return False

        except Exception as e:
            self.log_error(f"Error running tests for {feature}: {e}")
            return False

    def _verify_implementation(self, path, feature, implementation_file):
        """Verify that the implementation passes its tests."""
        try:
            # Ensure source directory is in Python path
            sys.path.insert(0, os.path.join(path, 'src'))

            # Run tests
            passed = self._run_tests_for_feature(path, feature)

            # Remove the temporary path addition
            sys.path.pop(0)

            return passed

        except Exception as e:
            self.log_error(f"Error verifying implementation: {e}")
            return False

    def _backup_file(self, file_path):
        """Create a backup of a file."""
        try:
            backup_path = f"{file_path}.bak"
            if os.path.exists(file_path):
                shutil.copy2(file_path, backup_path)
                return backup_path
            return None
        except Exception as e:
            self.log_error(f"Error creating backup: {e}")
            return None

    def _restore_backup(self, backup_path, original_path):
        """Restore a file from its backup."""
        try:
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)
                os.remove(backup_path)
                self.log_info(f"Restored backup for {os.path.basename(original_path)}")
                return True
            return False
        except Exception as e:
            self.log_error(f"Error restoring backup: {e}")
            return False

    def _extract_code_blocks(self, text):
        """Extract clean code blocks from AI response."""
        # Match code blocks enclosed in triple backticks (```language)
        code_blocks = re.findall(r'```(?:[a-zA-Z]*)\n(.*?)```', text, re.DOTALL)

        if code_blocks:
            # Combine and clean all extracted code blocks
            return '\n\n'.join(block.strip() for block in code_blocks)

        # Fallback: Detect lines resembling code
        potential_code = '\n'.join(
            line for line in text.splitlines()
            if line.strip() and (
                    line.strip().startswith(('def ', 'class ', 'import ', '#')) or
                    re.match(r'[a-zA-Z_]+\s*=\s*.+', line)  # Variable assignments
            )
        )
        return potential_code.strip() if potential_code else None

    def _create_file(self, file_path, content, log_message):
        """Create a file with cleaned content."""

        def _create_file_internal():
            try:
                # Extract clean code content
                cleaned_content = self._extract_code_blocks(content)
                if not cleaned_content:
                    self.log_error(f"Failed to extract code for {file_path}")
                    return

                # Create directories if they don't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Write the cleaned content to the file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_content)

                # Log success
                file_name = os.path.basename(file_path)
                self.log_success(f"{log_message}: {file_name}")

                # Update tree and expand parent directories
                self.update_tree(force=True)
                self._ensure_path_visible(file_path)

            except Exception as e:
                self.log_error(f"Failed to create file {file_path}: {e}")

        # Schedule file creation on main thread
        if threading.current_thread() is threading.main_thread():
            _create_file_internal()
        else:
            self.ui_queue.put(('create_file', (_create_file_internal,)))

    def _ensure_path_visible(self, path):
        """Ensure a path is visible in the tree by expanding all parent directories."""
        if not self.current_project_path:
            return

        try:
            # Get relative path from project root
            rel_path = os.path.relpath(path, self.current_project_path)
            parts = rel_path.split(os.sep)

            # Start from root
            current = ''
            parent_iid = ''

            # Traverse the tree and expand each parent
            for part in parts[:-1]:  # Skip the last part if it's a file
                current = os.path.join(current, part) if current else part
                full_path = os.path.join(self.current_project_path, current)

                # Find the item in the tree
                for item in self.tree.get_children(parent_iid):
                    if self.tree.item(item)['values'][0] == full_path:
                        self.tree.item(item, open=True)
                        parent_iid = item
                        break

        except Exception as e:
            self.log_error(f"Failed to ensure path visibility: {e}")

    def process_prompt_with_ai(self, combined_input):
        """Send the prompt to AI and receive the response."""
        ai_script_path = "src/models/ai_assistant.py"
        python_executable = 'python'

        command = [python_executable, ai_script_path, combined_input]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            ai_response, error = process.communicate()

            if error:
                self.ui_queue.put(('log', f"[ERROR] AI Assistant Error: {error}"))
            return ai_response.strip() if ai_response else None
        except Exception as e:
            self.ui_queue.put(('log', f"[ERROR] Failed to process prompt with AI: {e}"))
            return None

    def _create_structure(self, base_path, structure, current_path=''):
        """Recursively create project structure."""
        for name, content in structure.items():
            path = os.path.join(base_path, current_path, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                self._create_structure(base_path, content, os.path.join(current_path, name))
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_info(f"Created: {os.path.relpath(path, base_path)}")

    def new_file(self):
        """Create a new file in the selected directory or project root."""
        if not self.current_project_path:
            messagebox.showwarning("Warning", "No project open")
            return

        # Get the selected directory or use project root
        selection = self.tree.selection()
        parent_path = self.current_project_path
        if selection:
            selected_path = self.tree.item(selection[0])['values'][0]
            if os.path.isdir(selected_path):
                parent_path = selected_path
            else:
                parent_path = os.path.dirname(selected_path)

        def on_new_file_name(name):
            if name:
                try:
                    # Create full path and ensure parent directories exist
                    full_path = os.path.join(parent_path, name)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    # Create the file
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('')

                    self.log_success(f"Created file: {name}")

                    # Update tree and expand parent directory
                    self.update_tree(force=True)

                    # Select and show the new file
                    for item in self.tree.get_children(''):
                        if self._find_and_select_item(item, full_path):
                            break

                except Exception as e:
                    self.log_error(f"Failed to create file: {e}")

        # Use the custom non-modal dialog
        InputDialog(self.root, "New File", "Enter file name:", on_new_file_name)

    def new_folder(self):
        """Create a new folder in the selected directory or project root."""
        if not self.current_project_path:
            messagebox.showwarning("Warning", "No project open")
            return

        # Get the selected directory or use project root
        selection = self.tree.selection()
        parent_path = self.current_project_path
        if selection:
            selected_path = self.tree.item(selection[0])['values'][0]
            if os.path.isdir(selected_path):
                parent_path = selected_path
            else:
                parent_path = os.path.dirname(selected_path)

        def on_new_folder_name(name):
            if name:
                try:
                    # Create full path
                    full_path = os.path.join(parent_path, name)
                    os.makedirs(full_path, exist_ok=True)

                    self.log_success(f"Created folder: {name}")

                    # Update tree and expand parent directory
                    self.update_tree(force=True)

                    # Select and show the new folder
                    for item in self.tree.get_children(''):
                        if self._find_and_select_item(item, full_path):
                            break

                except Exception as e:
                    self.log_error(f"Failed to create folder: {e}")

        # Use the custom non-modal dialog
        InputDialog(self.root, "New Folder", "Enter folder name:", on_new_folder_name)

    def _find_and_select_item(self, node, target_path):
        """Recursively find and select an item in the tree by its path."""
        # Check current node
        if self.tree.item(node)['values'][0] == target_path:
            self.tree.selection_set(node)
            self.tree.see(node)
            return True

        # Check children
        for child in self.tree.get_children(node):
            if self._find_and_select_item(child, target_path):
                # Expand parent nodes to make the item visible
                parent = self.tree.parent(child)
                while parent:
                    self.tree.item(parent, open=True)
                    self.expanded_nodes.add(parent)
                    parent = self.tree.parent(parent)
                return True

        return False

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

    def generate_tests_from_prompt(self):
        """
        Generate test cases based on the user's input prompt.
        These tests include meaningful assertions related to typical expected functionality.
        """
        prompt = self.prompt_entry.get().strip()

        if not prompt:
            return """\
    import pytest

    def test_placeholder():
        assert True  # No prompt provided. Replace with meaningful tests.
    """

        # Analyzing the prompt for keywords and potential functionality
        keywords = re.findall(r'\b\w+\b', prompt.lower())  # Extract keywords from the prompt
        primary_features = ['add', 'delete', 'update', 'retrieve', 'process']

        # Base test template
        test_cases = []

        for feature in primary_features:
            if feature in keywords:
                test_cases.append(f"""\
    def test_{feature}():
        # Assuming a {feature} function exists
        # TODO: Replace with the actual implementation and meaningful assertions
        assert True  # Replace this with an actual assertion
    """)

        # General fallback if no specific features match
        if not test_cases:
            test_cases.append("""\
    def test_basic_functionality():
        # TODO: Replace with general tests for basic functionality
        assert True
    """)

        # Combine all tests
        return f"""\
    import pytest

    # Tests generated based on the prompt: "{prompt}"

    {''.join(test_cases)}
    """

    def update_tree(self, force=False):
        """Update project tree view with immediate visual feedback."""
        if self.paused and not force:
            return

        # Ensure we're on the main thread
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, lambda: self.update_tree(force))
            return

        # Store current selection and expanded nodes
        selection = self.tree.selection()
        expanded = {item: self.tree.item(item, 'open') for item in self.tree.get_children('')}

        # Clear and rebuild tree
        self.tree.delete(*self.tree.get_children())

        if not self.current_project_path or not os.path.exists(self.current_project_path):
            return

        def insert_recursively(parent, path):
            try:
                items = sorted(os.listdir(path),
                               key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

                for item in items:
                    full_path = os.path.join(path, item)
                    is_dir = os.path.isdir(full_path)
                    icon = "📁 " if is_dir else "📄 "

                    # Insert item
                    iid = self.tree.insert(
                        parent, 'end',
                        text=f"{icon}{item}",
                        values=(full_path,),
                        open=False
                    )

                    # Recursively process directories
                    if is_dir:
                        insert_recursively(iid, full_path)

                        # Expand if it was previously expanded
                        if full_path in self.expanded_nodes:
                            self.tree.item(iid, open=True)

            except Exception as e:
                self.log_error(f"Failed to process directory {path}: {e}")

        # Rebuild tree
        insert_recursively('', self.current_project_path)

        # Restore selection if possible
        if selection:
            self.tree.selection_set(selection)
            self.tree.see(selection[0])

        # Force update display
        self.tree.update_idletasks()

    def on_tree_select(self, event):
        """Display selected file in the editor."""
        selection = self.tree.selection()
        if not selection:
            return

        item_path = self.tree.item(selection[0])['values'][0]
        if os.path.isfile(item_path):
            try:
                with open(item_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', content)
                self.update_status(f"Opened: {os.path.basename(item_path)}")
            except Exception as e:
                self.log_error(f"Failed to open file: {e}")

    def toggle_ui_state(self, enabled):
        """Toggle UI state with pause button support."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.config(state=state)
        self.generate_btn.config(state=state)
        self.stop_btn.config(state=tk.DISABLED if enabled else tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED if enabled else tk.NORMAL)

    def process_ui_queue(self):
        """Process queued UI updates in the main thread with enhanced handlers."""
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
                elif command == 'create_file':
                    callback_func = data[0]
                    callback_func()
                elif command == 'select_file':
                    path = data
                    self._find_and_select_item('', path)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_ui_queue)

    def write_to_output(self, message):
        """Log output messages."""
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
        """Log an informational message."""
        self.ui_queue.put(('log', f"[INFO] {message}"))

    def log_error(self, message):
        """Log an error message."""
        self.ui_queue.put(('log', f"[ERROR] {message}"))

    def log_success(self, message):
        """Log a success message."""
        self.ui_queue.put(('log', f"[SUCCESS] {message}"))

    def update_status(self, message):
        """Update the status bar."""
        self.ui_queue.put(('status', message))

    def stop_generation(self):
        """Stop project generation."""
        self.generation_active = False
        self.log_info("Stopping project generation...")
        self.update_status("Stopping...")
        self.toggle_ui_state(True)


if __name__ == '__main__':
    app = ProjectWindow()
    app.run()
