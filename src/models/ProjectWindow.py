import os
import re
import string
import subprocess
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

    def generate_project_structure(self):
        """Generate initial project structure."""
        return {
            'src': {
                '__init__.py': '',
                'core': {
                    '__init__.py': ''
                },
                'utils': {
                    '__init__.py': ''
                }
            },
            'tests': {
                '__init__.py': ''
            },
            'docs': {
                'README.md': f'# Project Documentation\n\n{self.prompt}'
            }
        }

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

    def _generate_schema(self):
        """Generate data schema template."""
        return '''
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DataSchema:
    """Base data schema"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class ResourceSchema(DataSchema):
    """Resource data schema"""
    name: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource schema to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "name": self.name,
            "description": self.description
        })
        return base_dict
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

    def generate_test_suite(self):
        """Generate comprehensive test suite based on project type."""
        test_files = {
            'test_core.py': self._generate_core_tests(),
        }

        if 'web' in self.keywords:
            test_files['test_api.py'] = self._generate_api_tests()
        if 'data' in self.keywords:
            test_files['test_data.py'] = self._generate_data_tests()
        if 'gui' in self.keywords:
            test_files['test_ui.py'] = self._generate_ui_tests()

        return test_files

    def _generate_core_tests(self):
        """Generate core functionality tests."""
        return f'''
import pytest
from src.core import utils

def test_core_initialization():
    """Test core module initialization"""
    assert utils  # Verify module imports correctly

class TestCoreFunctionality:
    """Test core functionality of the project"""

    def test_basic_operations(self):
        """Test basic operations work as expected"""
        # TODO: Replace with actual core functionality tests
        assert True

    def test_error_handling(self):
        """Test error handling mechanisms"""
        # TODO: Implement error handling tests
        with pytest.raises(Exception):
            raise Exception("Test exception")
'''

    def _generate_api_tests(self):
        """Generate API-specific tests."""
        return '''
import pytest
from src.api import routes

class TestAPIEndpoints:
    """Test API endpoints functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        # TODO: Initialize test client
        return None

    def test_health_check(self, client):
        """Test health check endpoint"""
        # TODO: Implement health check test
        assert True

    def test_api_authentication(self, client):
        """Test API authentication"""
        # TODO: Implement authentication tests
        assert True
'''

    def _generate_data_tests(self):
        """Generate data processing tests."""
        return '''
import pytest
from src.data import processors

class TestDataProcessing:
    """Test data processing functionality"""

    @pytest.fixture
    def sample_data(self):
        """Provide sample data for tests"""
        return {
            "test": "data"
        }

    def test_data_validation(self, sample_data):
        """Test data validation"""
        # TODO: Implement data validation tests
        assert isinstance(sample_data, dict)

    def test_data_transformation(self, sample_data):
        """Test data transformation"""
        # TODO: Implement transformation tests
        assert True
'''

    def _generate_ui_tests(self):
        """Generate UI-specific tests."""
        return '''
import pytest
from src.ui import windows

class TestUIComponents:
    """Test UI components functionality"""

    @pytest.fixture
    def window(self):
        """Create test window"""
        # TODO: Initialize test window
        return None

    def test_window_creation(self, window):
        """Test window creation"""
        # TODO: Implement window creation test
        assert True

    def test_user_interactions(self, window):
        """Test user interactions"""
        # TODO: Implement interaction tests
        assert True
'''

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

        self.tree = ttk.Treeview(tree_frame, show='tree', selectmode='browse')
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
        """Generate project with AI-based content generation."""
        try:
            self.generation_active = True
            self.analyzer = ProjectAnalyzer(prompt)

            # Generate initial structure
            structure = self.analyzer.generate_project_structure()
            self._create_structure(path, structure)
            self.ui_queue.put(('update_tree', None))

            # Generate test suite
            test_files = self.analyzer.generate_test_suite()
            self._create_test_files(path, test_files)
            self.ui_queue.put(('update_tree', None))

            self.ui_queue.put(('log', "[SUCCESS] Initial project structure generated!"))

            # AI-based incremental development with TDD
            while self.generation_active:
                if not self.paused:
                    feature_type = self._select_feature_type()
                    ai_prompt = self._build_ai_prompt(feature_type, prompt)
                    ai_response = self.process_prompt_with_ai(ai_prompt)

                    if ai_response:
                        self._apply_ai_generated_feature(path, feature_type, ai_response)
                        # Generate corresponding test for the new feature
                        self._apply_ai_generated_feature(path, 'test', ai_response)
                    else:
                        self.ui_queue.put(('log', "[ERROR] AI failed to generate feature."))

                    self.ui_queue.put(('update_tree', None))
                time.sleep(2)  # Prevent excessive updates

        except Exception as e:
            self.ui_queue.put(('log', f"[ERROR] Project generation failed: {e}"))
        finally:
            self.generation_active = False
            self.ui_queue.put(('enable_ui', None))

    def generate_project(self, path, prompt):
        """Generate project using TDD methodology with clear phases."""
        try:
            self.generation_active = True
            self.analyzer = ProjectAnalyzer(prompt)

            # Initialize project structure
            structure = self.analyzer.generate_project_structure()
            self._create_structure(path, structure)
            self.ui_queue.put(('update_tree', None))

            # Get list of features to implement from analyzer
            features = self.analyzer.get_feature_list()
            implemented_features = set()

            while self.generation_active and features:
                if not self.paused:
                    current_feature = features.pop(0)

                    # Skip if feature already implemented
                    if current_feature in implemented_features:
                        continue

                    # Red Phase - Write failing test
                    if self._red_phase(path, current_feature):
                        # Green Phase - Implement feature
                        if self._green_phase(path, current_feature):
                            # Refactor Phase
                            self._refactor_phase(path, current_feature)
                            implemented_features.add(current_feature)

                    self.ui_queue.put(('update_tree', None))
                    time.sleep(1)  # Prevent excessive updates

            if not features:
                self.ui_queue.put(('log', "[SUCCESS] All features implemented successfully!"))

        except Exception as e:
            self.ui_queue.put(('log', f"[ERROR] Project generation failed: {e}"))
        finally:
            self.generation_active = False
            self.ui_queue.put(('enable_ui', None))

    def _red_phase(self, path, feature):
        """Red Phase: Write failing test for the feature."""
        try:
            self.log_info(f"[RED PHASE] Writing test for: {feature}")

            # Generate test file path
            test_file = os.path.join(path, 'tests', f'test_{feature.lower()}.py')

            # Get test content from AI
            test_prompt = f"Write a failing test for the following feature: {feature}. Include necessary imports and clear assertions."
            test_content = self.process_prompt_with_ai(test_prompt)

            if test_content:
                cleaned_test_content = self._extract_code_blocks(test_content)
                if cleaned_test_content:
                    self._create_file(test_file, cleaned_test_content, "Created failing test")
                    return True

            return False
        except Exception as e:
            self.log_error(f"Failed to create test for {feature}: {e}")
            return False

    def _green_phase(self, path, feature):
        """Green Phase: Implement minimal code to pass the test."""
        try:
            self.log_info(f"[GREEN PHASE] Implementing feature: {feature}")

            # Generate implementation file path
            impl_file = os.path.join(path, 'src', 'core', f'{feature.lower()}.py')

            # Get implementation from AI
            impl_prompt = f"Write minimal code to implement this feature and make its test pass: {feature}. Focus on simplicity."
            impl_content = self.process_prompt_with_ai(impl_prompt)

            if impl_content:
                cleaned_impl_content = self._extract_code_blocks(impl_content)
                if cleaned_impl_content:
                    self._create_file(impl_file, cleaned_impl_content, "Created implementation")
                    return True

            return False
        except Exception as e:
            self.log_error(f"Failed to implement {feature}: {e}")
            return False

    def _refactor_phase(self, path, feature):
        """Refactor Phase: Improve code quality while maintaining functionality."""
        try:
            self.log_info(f"[REFACTOR PHASE] Refactoring: {feature}")

            # Get implementation file path
            impl_file = os.path.join(path, 'src', 'core', f'{feature.lower()}.py')

            # Read current implementation
            with open(impl_file, 'r', encoding='utf-8') as f:
                current_code = f.read()

            # Get refactored version from AI
            refactor_prompt = f"Refactor this code while maintaining its functionality:\n{current_code}"
            refactored_content = self.process_prompt_with_ai(refactor_prompt)

            if refactored_content:
                cleaned_refactored_content = self._extract_code_blocks(refactored_content)
                if cleaned_refactored_content:
                    # Verify refactored code still passes tests
                    backup_file = impl_file + '.bak'
                    os.rename(impl_file, backup_file)

                    try:
                        self._create_file(impl_file, cleaned_refactored_content, "Refactored implementation")
                        if self._run_tests(path, feature):
                            os.remove(backup_file)
                            self.log_success(f"Refactoring successful for {feature}")
                            return True
                        else:
                            # Restore backup if tests fail
                            os.remove(impl_file)
                            os.rename(backup_file, impl_file)
                            self.log_error(f"Refactoring broke tests for {feature}, reverting changes")
                            return False
                    except Exception as e:
                        if os.path.exists(backup_file):
                            os.rename(backup_file, impl_file)
                        raise e

            return False
        except Exception as e:
            self.log_error(f"Failed to refactor {feature}: {e}")
            return False

    def _run_tests(self, path, feature):
        """Run tests for a specific feature."""
        try:
            test_file = os.path.join(path, 'tests', f'test_{feature.lower()}.py')

            # Run pytest for the specific test file
            result = subprocess.run(
                ['pytest', test_file, '-v'],
                capture_output=True,
                text=True,
                cwd=path
            )

            if result.returncode == 0:
                self.log_success(f"Tests passed for {feature}")
                return True
            else:
                self.log_error(f"Tests failed for {feature}:\n{result.stdout}")
                return False

        except Exception as e:
            self.log_error(f"Failed to run tests for {feature}: {e}")
            return False

    def _select_feature_type(self):
        """Select the type of feature to generate dynamically."""
        feature_types = ['utility', 'core', 'test']
        return feature_types[int(time.time()) % len(feature_types)]

    def _build_ai_prompt(self, feature_type, prompt):
        """Build a prompt for AI based on the feature type."""
        if feature_type == 'utility':
            return f"Generate a Python utility function for the following project description. Output the code within triple backticks: {prompt}"
        elif feature_type == 'core':
            return f"Generate a core Python feature for the following project. Output the code within triple backticks: {prompt}"
        elif feature_type == 'test':
            return f"Generate a Python test case for the following project. Output the code within triple backticks: {prompt}"
        else:
            return f"Generate relevant code for the following project. Use triple backticks for code blocks: {prompt}"

    def _apply_ai_generated_feature(self, path, feature_type, ai_response):
        """Save AI-generated feature to the project, avoiding duplicates."""
        if feature_type == 'utility':
            file_path = os.path.join(path, 'src', 'core', 'utils.py')
        elif feature_type == 'core':
            file_path = os.path.join(path, 'src', 'core', f'feature_{uuid.uuid4().hex[:8]}.py')
        elif feature_type == 'test':
            file_path = os.path.join(path, 'tests', f'test_feature_{uuid.uuid4().hex[:8]}.py')
        else:
            return

        cleaned_code = self._extract_code_blocks(ai_response)

        if cleaned_code:
            existing_features = self._get_existing_features(path)
            if self._check_duplicates(cleaned_code, existing_features, log_func=self.log_info):
                # Append suffix to avoid collision
                file_path = file_path.replace('.py', f'_duplicate_{uuid.uuid4().hex[:4]}.py')
            self._create_file(file_path, cleaned_code, f"AI-generated {feature_type} added")
        else:
            self.log_error(f"Failed to extract code from AI response for {feature_type}")

    def _get_existing_features(self, path):
        """Collect all existing features in the project for duplication checks."""
        existing_features = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            existing_features.append(content)
                    except Exception as e:
                        self.log_error(f"Failed to read {file}: {e}")
        return existing_features

    def _create_design_docs(self, path):
        """Generate design documents for the project."""
        docs_path = os.path.join(path, 'docs')
        os.makedirs(docs_path, exist_ok=True)

        design_doc = os.path.join(docs_path, 'design_document.md')
        with open(design_doc, 'w', encoding='utf-8') as f:
            f.write(
                "# Design Document\n\nDescribe the project architecture, major components, and design decisions here.")

        self.log_success("Generated design document.")

    def _check_project_completeness(self, path):
        """Check if the project is complete based on key criteria."""
        required_files = [
            os.path.join(path, 'src', '__init__.py'),
            os.path.join(path, 'tests', '__init__.py'),
            os.path.join(path, 'docs', 'design_document.md'),
            os.path.join(path, 'README.md')
        ]
        missing_files = [file for file in required_files if not os.path.exists(file)]

        if missing_files:
            self.log_error(f"Project is incomplete. Missing files: {', '.join(missing_files)}")
            return False

        self.log_success("Project appears complete.")
        return True

    def _generate_testing_instructions(self, path):
        """Generate a TESTING.md file with instructions for running tests."""
        testing_file = os.path.join(path, 'docs', 'TESTING.md')
        os.makedirs(os.path.dirname(testing_file), exist_ok=True)

        with open(testing_file, 'w', encoding='utf-8') as f:
            f.write("""# Testing Instructions

    ## Running Unit Tests
    1. Ensure all dependencies are installed: `pip install -r requirements.txt`
    2. Run the test suite: `pytest tests/`

    ## Testing Features
    - Check API endpoints with a tool like Postman or cURL.
    - Validate GUI functionality manually by launching the application.
            """)

        self.log_success("Generated testing instructions.")

    def _extract_code_blocks(self, text):
        """Extract code blocks from AI response, removing language markers."""
        # Match any code block inside triple backticks
        code_blocks = re.findall(r'```(?:[a-zA-Z]*)\n(.*?)```', text, re.DOTALL)

        if code_blocks:
            # Combine and clean all code blocks
            return '\n\n'.join(block.strip() for block in code_blocks)

        # Fallback: Detect lines that appear to be code
        potential_code = '\n'.join(
            line for line in text.splitlines()
            if line.strip() and (line.lstrip().startswith(('def ', 'class ', 'import ', '#')))
        )
        return potential_code.strip() if potential_code else None

    def _create_file(self, file_path, content, log_message):
        """Create a file and validate its content for naming conventions."""
        try:
            _validate_names(content)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            file_name = os.path.basename(file_path)
            self.log_success(f"{log_message}: {file_name}")
        except ValueError as e:
            self.log_error(f"Validation failed for {file_path}: {e}")
        except Exception as e:
            self.log_error(f"Failed to create file {file_path}: {e}")

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

    def _create_test_files(self, path, test_files):
        """Create test files in the tests directory."""
        tests_dir = os.path.join(path, 'tests')
        os.makedirs(tests_dir, exist_ok=True)

        for name, content in test_files.items():
            file_path = os.path.join(tests_dir, name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log_info(f"Created test file: {name}")

    def _develop_next_feature(self, path):
        """Develop the next project feature incrementally."""
        if not self.analyzer:
            return

        # Simulate development by adding new features/tests
        feature_types = ['utility', 'core', 'test']
        feature_type = feature_types[int(time.time()) % len(feature_types)]

        if feature_type == 'utility':
            self._add_utility_function(path)
        elif feature_type == 'core':
            self._add_core_feature(path)
        elif feature_type == 'test':
            self._add_test_case(path)

    def _add_utility_function(self, path):
        """Add a new utility function."""
        utils_path = os.path.join(path, 'src', 'core', 'utils.py')
        if os.path.exists(utils_path):
            with open(utils_path, 'a', encoding='utf-8') as f:
                f.write(f'''

def new_utility_{uuid.uuid4().hex[:8]}(data: Any) -> Dict[str, Any]:
    """New utility function"""
    # TODO: Implement utility function
    return {{"processed": data}}
''')
            self.log_info("Added new utility function")

    def _add_core_feature(self, path):
        """Add a new core feature."""
        core_path = os.path.join(path, 'src', 'core', f'feature_{uuid.uuid4().hex[:8]}.py')
        with open(core_path, 'w', encoding='utf-8') as f:
            f.write('''
from typing import Any, Dict

def process_feature(data: Any) -> Dict[str, Any]:
    """Process feature data"""
    # TODO: Implement feature processing
    return {"processed": data}
''')
        self.log_info("Added new core feature")

    def _add_test_case(self, path):
        """Add a new test case."""
        test_path = os.path.join(path, 'tests', f'test_feature_{uuid.uuid4().hex[:8]}.py')
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write('''
import pytest
from src.core import utils

def test_new_feature():
    """Test new feature functionality"""
    # TODO: Implement feature test
    assert True
''')
        self.log_info("Added new test case")

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

        name = simpledialog.askstring("New File", "Enter file name:")
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

        name = simpledialog.askstring("New Folder", "Enter folder name:")
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

    def create_initial_files(self, path, prompt):
        """Create initial project files."""
        files = {
            'README.md': f"# {prompt}\n\nProject generated by AI Project Generator.",
            '.gitignore': "*.pyc\n__pycache__/\n.env",
            'src/__init__.py': '',
            'tests/__init__.py': '',
        }
        for file_path, content in files.items():
            full_path = os.path.join(path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log_info(f"Created: {file_path}")
        self.update_tree()

    def create_tests(self, path):
        """Create initial test files dynamically based on the user's prompt."""
        try:
            # Create the tests directory
            tests_dir = os.path.join(path, 'tests')
            os.makedirs(tests_dir, exist_ok=True)

            # Generate test cases dynamically based on the prompt
            test_file_path = os.path.join(tests_dir, 'test_generated.py')
            test_content = self.generate_tests_from_prompt()

            # Write the generated test content into the test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)

            # Enqueue success message and tree update for the main thread
            self.ui_queue.put(('log', f"Test file created: {test_file_path}"))
            self.ui_queue.put(('update_tree', None))
        except Exception as e:
            # Enqueue error message for the main thread
            self.ui_queue.put(('log', f"[ERROR] Failed to create test files: {e}"))

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
        """Update project tree view while preserving expansion state and maintaining hierarchy."""
        if self.paused and not force:
            return

        # Store current selection and expanded state
        selection = self.tree.selection()
        expanded_items = {}

        def store_expanded_state(node=''):
            children = self.tree.get_children(node)
            for child in children:
                if self.tree.item(child, 'open'):
                    item_path = self.tree.item(child)['values'][0]
                    expanded_items[item_path] = child
                store_expanded_state(child)

        store_expanded_state()

        # Clear existing tree items
        self.tree.delete(*self.tree.get_children())

        if not self.current_project_path:
            return

        def sort_items(items, path):
            """Sort items with directories first, then files, both alphabetically."""
            return sorted(items, key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

        def insert_path(parent, path, level=0):
            try:
                items = os.listdir(path)
                for item in sort_items(items, path):  # Pass path to sort_items
                    item_path = os.path.join(path, item)
                    is_dir = os.path.isdir(item_path)
                    icon = "📁 " if is_dir else "📄 "

                    # Insert the item
                    node = self.tree.insert(
                        parent,
                        'end',
                        text=f"{icon}{item}",
                        values=(item_path,),
                        open=item_path in expanded_items
                    )

                    # If it's a directory and was previously expanded, process its children
                    if is_dir and (item_path in expanded_items or level == 0):
                        insert_path(node, item_path, level + 1)

                    # Keep track of the node if it was previously expanded
                    if item_path in expanded_items:
                        expanded_items[item_path] = node
                        self.expanded_nodes.add(node)

            except Exception as e:
                self.log_error(f"Failed to insert path {path}: {e}")

        # Add the root directory to the tree
        insert_path('', self.current_project_path)

        # Restore selection if possible
        for item in selection:
            if self.tree.exists(item):
                self.tree.selection_set(item)
                self.tree.see(item)  # Ensure the selected item is visible

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
        """Process queued UI updates in the main thread."""
        try:
            while True:
                command, data = self.ui_queue.get_nowait()
                if command == 'log':
                    self.write_to_output(data)  # Log messages to the output area
                elif command == 'status':
                    self.status_var.set(data)  # Update the status bar
                elif command == 'update_tree':
                    self.update_tree()  # Update the project tree
                elif command == 'enable_ui':
                    self.toggle_ui_state(True)  # Re-enable the UI
        except queue.Empty:
            pass
        finally:
            # Schedule the next queue processing
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

    def run(self):
        """Run the application."""
        self.root.mainloop()


if __name__ == '__main__':
    app = ProjectWindow()
    app.run()
