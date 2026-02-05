import tkinter as tk
from src.ui.UIManager import UIManager
import os

def test_ui_initialization():
    print("Starting UI Smoke Test...")
    try:
        # Mocking root since we can't open a real window easily in CI
        root = tk.Tk()
        root.withdraw() # Hide it

        # We need to mock IDEController slightly or just instantiate it
        # IDEController(root=root) might try to do too much

        # Let's try to just instantiate UIManager with a mock controller
        class MockController:
            def __init__(self, root):
                self.root = root
                self.current_project = os.getcwd()
                self.projects_base_dir = "data/projects"
                self.project_manager = MockProjectManager()
                self.ai_orchestrator = MockAIOrchestrator()

            def safe_ui_call(self, func, *args, **kwargs):
                func(*args, **kwargs)

            def safe_new_project(self): pass
            def safe_open_project(self): pass

        class MockProjectManager:
            def generate_project_with_ai(self, **kwargs): pass
            def pause_project(self): pass

        class MockAIOrchestrator:
            def stop_generation(self): pass

        controller = MockController(root)
        ui = UIManager(controller)

        print("UIManager initialized successfully.")

        # Check basic component existence
        assert hasattr(ui, 'top_bar')
        assert hasattr(ui, 'sidebar')
        assert hasattr(ui, 'center_panel')
        assert hasattr(ui, 'right_panel')
        assert hasattr(ui, 'outer_paned')

        print("Basic components verified.")

        root.destroy()
        print("UI Smoke Test PASSED.")
    except Exception as e:
        print(f"UI Smoke Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    test_ui_initialization()
