import os
import time
import threading
import tkinter as tk
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.ui.rich_components import FileTreeView

def demo():
    # Setup test directory
    test_dir = os.path.abspath("test_workspace")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # Initialize Tkinter root
    root = tk.Tk()
    root.withdraw() # Hide main window

    print(f"Initializing FileTreeView on {test_dir}")
    view = FileTreeView(root, test_dir)
    view.pack()

    def simulate_changes():
        try:
            time.sleep(1)

            # Create a file
            test_file = os.path.join(test_dir, "hello.py")
            print(f"Creating {test_file}")
            with open(test_file, "w") as f:
                f.write("print('hello')")

            time.sleep(1.5)

            # Modify the file
            print(f"Modifying {test_file}")
            with open(test_file, "a") as f:
                f.write("\nprint('world')")

            time.sleep(1.5)

            # Delete the file
            print(f"Deleting {test_file}")
            os.remove(test_file)

            time.sleep(1)
            print("Demo finished successfully.")
        except Exception as e:
            print(f"Demo failed: {e}")
        finally:
            root.quit()

    # Start simulation in a thread
    sim_thread = threading.Thread(target=simulate_changes)
    sim_thread.start()

    # Run Tkinter main loop
    root.mainloop()
    sim_thread.join()

    # Cleanup
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    demo()
