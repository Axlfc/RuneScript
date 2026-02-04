import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class TechStackDetector:
    """Detects the tech stack of a project from user prompts or project files."""

    # Core signatures in code for fast detection
    SIGNATURES = {
        'frontend_web': {
            'display_name': 'Frontend Web (HTML/CSS/JS)',
            'keywords': ['html', 'css', 'javascript', 'web', 'portfolio', 'landing', 'website', 'frontend', 'ui', 'ux'],
            'files': ['index.html', 'styles.css', 'main.js'],
            'test_framework': 'python_beautifulsoup',
            'test_command': '{python} {test_file}',
            'test_pattern': 'test_*.py',
            'default_structure': ['index.html', 'css/', 'js/', 'img/'],
            'quality_standards': {
                'html': {'min_lines': 150},
                'css': {'min_lines': 200},
                'js': {'min_lines': 100}
            }
        },
        'python_backend': {
            'display_name': 'Python Backend',
            'keywords': ['python', 'api', 'flask', 'django', 'fastapi', 'backend', 'server', 'logic', 'script'],
            'files': ['requirements.txt', 'setup.py', 'pyproject.toml', 'main.py', 'app.py'],
            'test_framework': 'pytest',
            'test_command': '{python} -m pytest {test_file} -v',
            'test_pattern': 'test_*.py',
            'default_structure': ['src/', 'tests/', 'requirements.txt'],
            'quality_standards': {
                'py': {'min_lines': 100}
            }
        },
        'node_js': {
            'display_name': 'Node.js Backend',
            'keywords': ['node', 'npm', 'express', 'javascript backend', 'typescript'],
            'files': ['package.json', 'package-lock.json'],
            'test_framework': 'jest',
            'test_command': 'npm test -- {test_file}',
            'test_pattern': '*.test.js',
            'default_structure': ['src/', 'tests/', 'package.json'],
            'quality_standards': {
                'js': {'min_lines': 100}
            }
        },
        'ruby_gem': {
            'display_name': 'Ruby Gem',
            'keywords': ['ruby', 'gem', 'gemspec', 'bundler', 'rake'],
            'files': ['*.gemspec', 'Gemfile', 'lib/', 'spec/'],
            'test_framework': 'rspec',
            'test_command': 'bundle exec rspec {test_file}',
            'test_pattern': '*_spec.rb',
            'default_structure': ['lib/', 'spec/', 'Gemfile'],
            'quality_standards': {'rb': {'min_lines': 100}}
        },
        'ruby_sinatra': {
            'display_name': 'Ruby Sinatra',
            'keywords': ['sinatra', 'ruby web', 'rack'],
            'files': ['app.rb', 'config.ru', 'Gemfile'],
            'test_framework': 'rspec',
            'test_command': 'bundle exec rspec {test_file}',
            'test_pattern': '*_spec.rb',
            'default_structure': ['app.rb', 'spec/', 'Gemfile'],
            'quality_standards': {'rb': {'min_lines': 150}}
        },
        'go_cli': {
            'display_name': 'Go CLI/System',
            'keywords': ['go', 'golang', 'cli go', 'concurrency go', 'goroutines', 'channel'],
            'files': ['go.mod', 'go.sum', 'main.go'],
            'test_framework': 'go test',
            'test_command': 'go test -v {test_file}',
            'test_pattern': '*_test.go',
            'default_structure': ['cmd/', 'internal/', 'pkg/', 'go.mod'],
            'quality_standards': {'go': {'min_lines': 150}}
        },
        'rust_project': {
            'display_name': 'Rust Project',
            'keywords': ['rust', 'cargo', 'tokio', 'performance rust', 'safe memory'],
            'files': ['Cargo.toml', 'Cargo.lock', 'src/main.rs', 'src/lib.rs'],
            'test_framework': 'cargo test',
            'test_command': 'cargo test',
            'test_pattern': '*',
            'default_structure': ['src/', 'tests/', 'Cargo.toml'],
            'quality_standards': {'rs': {'min_lines': 200}}
        },
        'nextjs_fullstack': {
            'display_name': 'Next.js Fullstack',
            'keywords': ['next.js', 'nextjs', 'react', 'tailwind', 'prisma', 'typescript', 'fullstack'],
            'files': ['next.config.js', 'tsconfig.json', 'app/', 'pages/'],
            'test_framework': 'jest',
            'test_command': 'npm test',
            'test_pattern': '*.test.tsx',
            'default_structure': ['app/', 'components/', 'public/', 'package.json'],
            'quality_standards': {
                'tsx': {'min_lines': 150},
                'ts': {'min_lines': 100}
            }
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("data/tech_stacks.json")
        self._load_external_configs()

    def _load_external_configs(self):
        """Merge external JSON configurations into SIGNATURES."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    external_config = json.load(f)

                for tech, config in external_config.items():
                    if tech in self.SIGNATURES:
                        self.SIGNATURES[tech].update(config)
                    else:
                        self.SIGNATURES[tech] = config
            except Exception as e:
                logger.error(f"Error loading tech_stacks.json: {e}")

    def detect_from_prompt(self, prompt: str) -> str:
        """Detect tech stack from a user prompt."""
        prompt_lower = prompt.lower()

        # Scoring system
        scores = {tech: 0 for tech in self.SIGNATURES}

        for tech, config in self.SIGNATURES.items():
            for kw in config.get('keywords', []):
                if kw in prompt_lower:
                    scores[tech] += 1

        # Find best match
        best_tech = max(scores, key=scores.get)

        if scores[best_tech] == 0:
            # Default to frontend_web if no keywords match, it's a common case
            return 'frontend_web'

        return best_tech

    def detect_from_project(self, project_path: Path) -> str:
        """Detect tech stack from existing project files."""
        scores = {tech: 0 for tech in self.SIGNATURES}

        for tech, config in self.SIGNATURES.items():
            for file_pattern in config.get('files', []):
                if list(project_path.glob(f"**/{file_pattern}")):
                    scores[tech] += 2 # Higher weight for file matches

        best_tech = max(scores, key=scores.get)
        if scores[best_tech] == 0:
            return 'unknown'

        return best_tech

    def get_config(self, tech: str) -> Dict[str, Any]:
        """Return configuration for a specific tech stack."""
        return self.SIGNATURES.get(tech, self.SIGNATURES['frontend_web'])
