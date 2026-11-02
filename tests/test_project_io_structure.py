import os

from src.utils.ProjectIO import ProjectIO


def test_create_structure_does_not_turn_file_paths_into_directories(tmp_path):
    metadata = {
        "project_structure": [
            "README.md",
            "backend/app/main.py",
            "backend/app/api/",
            "backend/tests/unit",
            ".github/workflows/ci.yml",
        ]
    }

    messages = []
    ProjectIO(messages.append).create_structure(str(tmp_path), metadata)

    assert not (tmp_path / "README.md").is_dir()
    assert not (tmp_path / "backend" / "app" / "main.py").is_dir()
    assert not (tmp_path / ".github" / "workflows" / "ci.yml").is_dir()

    assert (tmp_path / "backend" / "app").is_dir()
    assert (tmp_path / "backend" / "app" / "api").is_dir()
    assert (tmp_path / "backend" / "tests" / "unit").is_dir()
    assert (tmp_path / ".github" / "workflows").is_dir()

    assert (tmp_path / "src" / "__init__.py").is_file()
    assert (tmp_path / "tests" / "__init__.py").is_file()
    assert (tmp_path / "pytest.ini").is_file()
