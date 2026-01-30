# Threading and Concurrency Audit - RuneScript

This document details the exhaustive audit and subsequent remediation of threading, subprocess, and asynchronous operations within RuneScript.

## 1. Summary of Issues (Resolved)
The application suffered from frequent freezes and unresponsiveness due to blocking operations on the main thread.
- **Blocking Subprocesses:** Replaced `subprocess.run`, `call`, and `communicate` with asynchronous versions using `ThreadManager`.
- **UI Thread Safety:** Standardized on `root.after(0, ...)` for all UI updates from background threads.
- **Centralized Management:** Implemented `src/utils/thread_manager.py` for global control, logging, and cancellation.
- **Nested Mainloops:** Removed dangerous `window.mainloop()` calls in secondary windows.

## 2. Refactored Components

### 2.1. Infrastructure
- **ThreadManager:** Located in `src/utils/thread_manager.py`. Manages a pool of 4 workers. Provides methods for running tasks and subprocesses with cancellation support.
- **Status Bar:** Integrated into the main window to provide non-modal feedback and a "Cancel" button for long-running tasks.
- **Logging:** Detailed thread lifecycle logging in `logs/threading.log`.

### 2.2. Critical Operations Refactored

| Component | File | Resolution |
|-----------|------|------------|
| Script Execution | `src/models/script_operations.py` | Migrated to `ThreadManager.run_subprocess`. Real-time status bar updates. |
| Tree Run Script | `src/views/tree_functions.py` | Migrated `_run_python_script` and `_run_script` to non-blocking. |
| File Search | `src/window/FindInFilesWindow.py` | Refactored `search_worker` to be thread-safe and cancellable. |
| WinGet Manager | `src/window/WingetWindow.py` | All winget commands moved to background threads. |
| LaTeX Editor | `src/window/LaTeXMarkdownEditor.py` | Compilation and Python execution refactored to use `ThreadManager`. |
| Planner | `src/window/PlannerWindow.py` | Alarm/Cronometros refactored to be non-blocking and cancellable. |
| Scheduled Tasks| `src/controllers/scheduled_tasks.py` | Removed nested mainloops; moved subprocess calls to background. |

## 3. How to Debug
- **Thread Debugger:** Press `Ctrl+Shift+D` in the main window to see active tasks, their duration, and status.
- **Logs:** Check `logs/threading.log` for a history of thread starts, completions, and errors.

## 4. Best Practices for Future Development
1. **Never block the main thread:** Any operation expected to take >100ms MUST use `thread_manager.run_in_thread`.
2. **UI Updates:** Always use `root.after(0, callback)` when updating widgets from a worker thread.
3. **Subprocesses:** Use `thread_manager.run_subprocess` to handle command execution and output capture.
4. **Cancellation:** Ensure long-running worker loops check `stop_event.is_set()`.
