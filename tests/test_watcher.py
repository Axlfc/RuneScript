import os
import time
import shutil
import threading
from src.ui.rich_components import FileSystemWatcher, FileSystemEvent

def test_watcher():
    test_dir = os.path.abspath("test_watcher_workspace")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    events = []
    def callback(event):
        print(f"Event: {event.event_type} on {event.src_path}")
        events.append(event)

    watcher = FileSystemWatcher(test_dir, callback, interval=0.1)
    watcher.start()

    try:
        # Test creation
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello")

        time.sleep(0.5)
        assert any(e.event_type == 'created' and e.src_path == test_file for e in events)

        # Test modification
        events.clear()
        with open(test_file, "a") as f:
            f.write(" world")

        time.sleep(0.5)
        assert any(e.event_type == 'modified' and e.src_path == test_file for e in events)

        # Test deletion
        events.clear()
        os.remove(test_file)

        time.sleep(0.5)
        assert any(e.event_type == 'deleted' and e.src_path == test_file for e in events)

        print("FileSystemWatcher tests passed!")

    finally:
        watcher.stop()
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_watcher()
