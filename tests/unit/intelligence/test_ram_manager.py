import pytest
from src.core.storage import FileSystemStorage
from src.core.context_intelligence import RAMContextManager

def test_ram_manager_refresh(tmp_path):
    storage = FileSystemStorage(tmp_path)
    ram_path = "ram.md"
    manager = RAMContextManager(storage, ram_path)

    manager.refresh({"tech_stack": "python", "phase": "GREEN"})
    assert storage.exists(ram_path)
    content = manager.get_sanitized_content()
    assert "# 🧠 Active Development Context" in content
    assert "Tech Stack: python" in content
    assert "Current: GREEN" in content
