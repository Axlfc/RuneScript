import threading
import logging
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Dict, Any, Optional, List
import queue
from logging.handlers import RotatingFileHandler
import os

# Configure logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "threading.log")
logger = logging.getLogger("ThreadManager")
logger.setLevel(logging.DEBUG)

# File handler with rotation
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024 * 5, backupCount=5, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class ManagedTask:
    def __init__(self, task_id: str, future: Future, stop_event: threading.Event):
        self.task_id = task_id
        self.future = future
        self.stop_event = stop_event
        self.start_time = time.time()

class ThreadManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ThreadManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RuneWorker")
        self.active_tasks: Dict[str, ManagedTask] = {}
        self.task_lock = threading.Lock()
        self._initialized = True
        logger.info("ThreadManager initialized with 4 workers.")

    def run_in_thread(self, func: Callable, task_id: str, *args,
                      on_complete: Optional[Callable] = None,
                      on_error: Optional[Callable] = None,
                      timeout: float = 60.0,
                      **kwargs) -> str:
        """
        Runs a function in a background thread from the pool.
        """
        stop_event = threading.Event()

        def wrapper():
            thread_id = threading.get_ident()
            logger.debug(f"Task {task_id} started in thread {thread_id}")
            try:
                # We pass the stop_event as the first argument if the function signature allows it,
                # or the function can check thread_manager.is_cancelled(task_id)
                result = func(stop_event, *args, **kwargs)
                logger.debug(f"Task {task_id} completed successfully")
                if on_complete:
                    from src.views.tk_utils import root
                    root.after(0, lambda: on_complete(result))
            except Exception as e:
                logger.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
                if on_error:
                    from src.views.tk_utils import root
                    root.after(0, lambda: on_error(e))
            finally:
                with self.task_lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
                logger.debug(f"Task {task_id} cleaned up")

        with self.task_lock:
            future = self.executor.submit(wrapper)
            self.active_tasks[task_id] = ManagedTask(task_id, future, stop_event)

        return task_id

    def cancel_task(self, task_id: str):
        with self.task_lock:
            if task_id in self.active_tasks:
                logger.info(f"Cancelling task {task_id}")
                self.active_tasks[task_id].stop_event.set()
                # future.cancel() only works if task hasn't started
                self.active_tasks[task_id].future.cancel()
                return True
        return False

    def is_cancelled(self, task_id: str) -> bool:
        with self.task_lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].stop_event.is_set()
        return False

    def run_subprocess(self, command: List[str], task_id: str,
                       on_output: Optional[Callable[[str], None]] = None,
                       on_complete: Optional[Callable[[int, str, str], None]] = None,
                       on_error: Optional[Callable[[Exception], None]] = None,
                       cwd: Optional[str] = None):
        """
        Runs a subprocess asynchronously and reads its output.
        """
        def worker(stop_event: threading.Event):
            logger.info(f"Starting subprocess for task {task_id}: {command}")
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    errors='replace',
                    cwd=cwd,
                    bufsize=1,
                    universal_newlines=True
                )

                stdout_lines = []
                stderr_lines = []

                def read_stream(stream, lines_list, is_stderr):
                    for line in iter(stream.readline, ''):
                        if stop_event.is_set():
                            process.terminate()
                            break
                        lines_list.append(line)
                        if on_output:
                            from src.views.tk_utils import root
                            root.after(0, lambda l=line: on_output(l))
                    stream.close()

                t1 = threading.Thread(target=read_stream, args=(process.stdout, stdout_lines, False))
                t2 = threading.Thread(target=read_stream, args=(process.stderr, stderr_lines, True))
                t1.start()
                t2.start()

                while t1.is_alive() or t2.is_alive():
                    if stop_event.is_set():
                        process.terminate()
                        break
                    time.sleep(0.1)

                return_code = process.wait()
                stdout_final = "".join(stdout_lines)
                stderr_final = "".join(stderr_lines)

                if on_complete:
                    from src.views.tk_utils import root
                    root.after(0, lambda: on_complete(return_code, stdout_final, stderr_final))

                return return_code
            except Exception as e:
                if on_error:
                    from src.views.tk_utils import root
                    root.after(0, lambda: on_error(e))
                raise e

        return self.run_in_thread(worker, task_id)

    def update_status_bar(self, message: str, show_progress: bool = False, show_cancel: bool = False, task_id: Optional[str] = None):
        from src.views.tk_utils import root, status_label_var, progress_bar, cancel_button

        status_label_var.set(message)

        if show_progress:
            progress_bar.pack(side="right", padx=10)
            progress_bar.start()
        else:
            progress_bar.stop()
            progress_bar.pack_forget()

        if show_cancel and task_id:
            cancel_button.pack(side="right", padx=5)
            cancel_button.configure(command=lambda: self.cancel_task(task_id))
        else:
            cancel_button.pack_forget()

    def get_active_tasks_info(self) -> List[Dict[str, Any]]:
        with self.task_lock:
            now = time.time()
            return [
                {
                    "id": t.task_id,
                    "duration": round(now - t.start_time, 2),
                    "cancelled": t.stop_event.is_set()
                }
                for t in self.active_tasks.values()
            ]

    def shutdown(self):
        logger.info("Shutting down ThreadManager...")
        self.executor.shutdown(wait=False)

def show_debug_threads_window():
    import tkinter as tk
    from tkinter import ttk
    from src.views.tk_utils import root

    debug_win = tk.Toplevel(root)
    debug_win.title("Thread Debugger")
    debug_win.geometry("400x300")

    listbox = tk.Listbox(debug_win)
    listbox.pack(expand=True, fill='both', padx=10, pady=10)

    def refresh():
        if not debug_win.winfo_exists():
            return
        listbox.delete(0, tk.END)
        tasks = thread_manager.get_active_tasks_info()
        for t in tasks:
            status = "CANCELLED" if t['cancelled'] else "RUNNING"
            listbox.insert(tk.END, f"{t['id']} | {t['duration']}s | {status}")
        debug_win.after(1000, refresh)

    btn_cancel = tk.Button(debug_win, text="Cancel Selected",
                           command=lambda: [thread_manager.cancel_task(listbox.get(tk.ACTIVE).split(' | ')[0])
                                          if listbox.curselection() else None])
    btn_cancel.pack(pady=5)

    refresh()

# Global instance
thread_manager = ThreadManager()
