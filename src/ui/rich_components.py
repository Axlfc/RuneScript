import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from datetime import datetime
from typing import Callable, Dict, List, Optional
import sys
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

class FileSystemEvent:
    """Represents a file system change event."""
    def __init__(self, event_type: str, src_path: str):
        self.event_type = event_type  # 'created', 'modified', 'deleted'
        self.src_path = src_path

class FileSystemWatcher:
    """A simple polling-based file system watcher."""

    def __init__(self, path: str, callback: Callable[[FileSystemEvent], None], interval: float = 1.0):
        self.path = os.path.abspath(path)
        self.callback = callback
        self.interval = interval
        self.running = False
        self.snapshot = self._take_snapshot()
        self.thread = None
        self._lock = threading.Lock()

    def _take_snapshot(self) -> Dict[str, float]:
        """Takes a snapshot of the current directory state (files and mtimes)."""
        snapshot = {}
        try:
            if not os.path.exists(self.path):
                return snapshot
            for root, dirs, files in os.walk(self.path):
                # Skip hidden directories and build artifacts
                dirs[:] = [d for d in dirs if d not in ['.git', '.nia', '.venv', '__pycache__', 'node_modules', 'dist', 'build']]

                for f in files:
                    full_path = os.path.join(root, f)
                    try:
                        snapshot[full_path] = os.path.getmtime(full_path)
                    except (OSError, FileNotFoundError):
                        pass
                for d in dirs:
                    full_path = os.path.join(root, d)
                    try:
                        snapshot[full_path] = os.path.getmtime(full_path)
                    except (OSError, FileNotFoundError):
                        pass
        except Exception as e:
            print(f"Error taking snapshot of {self.path}: {e}")
        return snapshot

    def start(self):
        """Starts the watcher thread."""
        with self._lock:
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._watch, daemon=True)
                self.thread.start()

    def stop(self):
        """Stops the watcher thread."""
        with self._lock:
            self.running = False

    def _watch(self):
        """Main watch loop."""
        while True:
            with self._lock:
                if not self.running:
                    break

            time.sleep(self.interval)

            new_snapshot = self._take_snapshot()

            # Check for deletions
            for path in list(self.snapshot.keys()):
                if path not in new_snapshot:
                    self.callback(FileSystemEvent('deleted', path))

            # Check for creations and modifications
            for path, mtime in new_snapshot.items():
                if path not in self.snapshot:
                    self.callback(FileSystemEvent('created', path))
                elif mtime > self.snapshot[path]:
                    self.callback(FileSystemEvent('modified', path))

            self.snapshot = new_snapshot

class FileTreeView(ttk.Frame):
    """Live file system tree with real-time updates."""

    def __init__(self, parent, project_path, on_file_open_callback=None, on_file_modified_callback=None):
        super().__init__(parent)
        self.project_path = os.path.abspath(project_path)
        self.on_file_open_callback = on_file_open_callback
        self.on_file_modified_callback = on_file_modified_callback
        self._pending_callbacks = set()

        # Create tree widget
        self.tree = ttk.Treeview(self, selectmode='browse')
        self.tree.pack(fill='both', expand=True)

        # Configure columns
        # path is hidden but used for backward compatibility with ProjectFileManager
        self.tree['columns'] = ('path', 'type', 'size', 'modified')
        self.tree.column('#0', width=250)  # File name
        self.tree.column('path', width=0, stretch=tk.NO) # Hidden
        self.tree.column('type', width=80)
        self.tree.column('size', width=80)
        self.tree.column('modified', width=150)

        self.tree.heading('#0', text='Name')
        self.tree.heading('path', text='Path')
        self.tree.heading('type', text='Type')
        self.tree.heading('size', text='Size')
        self.tree.heading('modified', text='Modified')

        # Bindings
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)
        if sys.platform == 'darwin':
            self.tree.bind('<Button-2>', self._on_right_click)

        # Style configuration
        style = ttk.Style()
        style.configure('Treeview',
                       background='#2b2b2b',
                       foreground='#ffffff',
                       fieldbackground='#2b2b2b')

        # File type icons
        self.icons = {
            'folder': '📁', 'python': '🐍', 'html': '🌐', 'css': '🎨',
            'js': '📜', 'md': '📝', 'json': '{}', 'git': '🔀', 'test': '🧪', 'default': '📄'
        }

        self.node_map = {}
        self.file_watcher = None
        self.set_project_path(project_path)

    def set_project_path(self, new_path):
        """Update the project path and restart watcher."""
        if not new_path: return
        self.project_path = os.path.abspath(new_path)
        if self.file_watcher:
            self.file_watcher.stop()
        self.file_watcher = FileSystemWatcher(self.project_path, self.on_file_change)
        self.file_watcher.start()
        self.refresh_tree()

    def refresh_tree(self):
        """Rebuild entire tree."""
        self.tree.delete(*self.tree.get_children())
        self.node_map = {}
        if os.path.exists(self.project_path):
            self._populate_tree('', self.project_path)

    def _populate_tree(self, parent, path):
        try:
            items = sorted(os.listdir(path))
            for item in items:
                if item in ['.git', '.nia', '.venv', '__pycache__']: continue
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                abs_path = os.path.abspath(item_path)
                node = self.tree.insert(parent, 'end', text=f"{self._get_icon(item, is_dir)} {item}",
                    values=(abs_path, 'DIR' if is_dir else self._get_file_type(item), self._format_size(item_path), self._format_time(item_path)))
                self.node_map[abs_path] = node
                if is_dir: self._populate_tree(node, item_path)
        except Exception: pass

    def _get_icon(self, filename, is_dir):
        if is_dir: return self.icons['folder']
        ext = os.path.splitext(filename)[1].lower()
        if 'test' in filename.lower(): return self.icons['test']
        return self.icons.get(ext[1:], self.icons['default']) if ext else self.icons['default']

    def _get_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return ext[1:].upper() if ext else 'FILE'

    def _format_size(self, path):
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
            else:
                size = 0
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if not os.path.islink(fp):
                            size += os.path.getsize(fp)

            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024: return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except: return "N/A"

    def _format_time(self, path):
        try: return datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
        except: return "N/A"

    def _on_double_click(self, event):
        item = self.tree.selection()
        if not item: return

        # Find path for the selected node
        filepath = self._get_path_from_node(item[0])

        if filepath and os.path.isfile(filepath):
            if self.on_file_open_callback:
                self.on_file_open_callback(filepath)

    def _get_path_from_node(self, node_id):
        for path, node in self.node_map.items():
            if node == node_id:
                return path
        return None

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._show_context_menu(event)

    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)

        item = self.tree.selection()
        if not item: return
        filepath = self._get_path_from_node(item[0])
        if not filepath: return

        menu.add_command(label="Open", command=lambda: self._on_double_click(None))
        menu.add_command(label="Rename", command=self._rename_file)
        menu.add_command(label="Delete", command=self._delete_file)
        menu.add_separator()
        menu.add_command(label="Copy Path", command=self._copy_path)

        menu.post(event.x_root, event.y_root)

    def _rename_file(self):
        item = self.tree.selection()
        if not item: return
        old_path = self._get_path_from_node(item[0])
        if not old_path: return

        old_name = os.path.basename(old_path)
        new_name = simpledialog.askstring("Rename", f"Enter new name for {old_name}:", initialvalue=old_name)

        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                # Watcher will handle UI update via refresh or events
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename: {e}")

    def _delete_file(self):
        item = self.tree.selection()
        if not item: return
        filepath = self._get_path_from_node(item[0])
        if not filepath: return

        if messagebox.askyesno("Delete", f"Are you sure you want to delete {os.path.basename(filepath)}?"):
            try:
                if os.path.isdir(filepath):
                    import shutil
                    shutil.rmtree(filepath)
                else:
                    os.remove(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}")

    def _copy_path(self):
        item = self.tree.selection()
        if not item: return
        filepath = self._get_path_from_node(item[0])
        if not filepath: return

        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(filepath)
                return
            except Exception:
                pass

        # Fallback to tkinter clipboard
        self.tree.clipboard_clear()
        self.tree.clipboard_append(filepath)

    def on_file_change(self, event):
        self._safe_after(0, lambda: self._handle_event(event))

    def _handle_event(self, event):
        try:
            if event.event_type == 'created': self._animate_file_creation(event.src_path)
            elif event.event_type == 'modified': self._highlight_file_modification(event.src_path)
            elif event.event_type == 'deleted': self._fade_out_file_deletion(event.src_path)
        except Exception as e:
            print(f"Error handling file event: {e}")

    def _animate_file_creation(self, filepath):
        filepath = os.path.abspath(filepath)
        if filepath in self.node_map: return
        parent_dir = os.path.abspath(os.path.dirname(filepath))
        parent_node = self.node_map.get(parent_dir, '')

        # Check if parent node exists in tree
        if parent_node and not self.tree.exists(parent_node):
             parent_node = ''

        filename = os.path.basename(filepath)
        is_dir = os.path.isdir(filepath)

        try:
            node = self.tree.insert(parent_node, 'end', text=f"{self._get_icon(filename, is_dir)} {filename}",
                values=(filepath, 'DIR' if is_dir else self._get_file_type(filename), self._format_size(filepath), self._format_time(filepath)))
            self.node_map[filepath] = node
            if parent_node: self.tree.item(parent_node, open=True)
            self.tree.tag_configure('new_file', background='#00ff00', foreground='#000000')
            self.tree.item(node, tags=('new_file',))

            def clear_tag():
                if self.tree.exists(node):
                    self.tree.item(node, tags=())

            self._safe_after(2000, clear_tag)
        except Exception as e:
            print(f"Error animating creation: {e}")

    def _highlight_file_modification(self, filepath):
        filepath = os.path.abspath(filepath)
        node = self.node_map.get(filepath)
        if node and self.tree.exists(node):
            try:
                self.tree.item(node, values=(filepath, 'DIR' if os.path.isdir(filepath) else self._get_file_type(filepath), self._format_size(filepath), self._format_time(filepath)))
                self.tree.tag_configure('modified', background='#ffff00', foreground='#000000')
                self.tree.item(node, tags=('modified',))

                def clear_tag():
                    if self.tree.exists(node):
                        self.tree.item(node, tags=())

                self._safe_after(1500, clear_tag)
            except Exception as e:
                print(f"Error highlighting modification: {e}")

        # Trigger callback for real-time editor updates
        if self.on_file_modified_callback:
            self.on_file_modified_callback(filepath)

    def _fade_out_file_deletion(self, filepath):
        filepath = os.path.abspath(filepath)
        node = self.node_map.get(filepath)
        if node and self.tree.exists(node):
            try:
                self.tree.tag_configure('deleted', background='#ff4444', foreground='#ffffff')
                self.tree.item(node, tags=('deleted',))
                def remove():
                    if self.tree.exists(node): self.tree.delete(node)
                    if filepath in self.node_map: del self.node_map[filepath]
                self._safe_after(1000, remove)
            except Exception as e:
                print(f"Error fading out deletion: {e}")

    def _safe_after(self, ms, func):
        """A safe version of after() that tracks callbacks for cleanup."""
        def wrapper():
            if func not in self._pending_callbacks:
                return
            self._pending_callbacks.remove(func)
            try:
                func()
            except Exception:
                pass

        self._pending_callbacks.add(func)
        return self.after(ms, wrapper)

    def stop_animations(self):
        """Stop all pending animations."""
        self._pending_callbacks.clear()

class TDDPhaseIndicator(ttk.Frame):
    """Visual state machine for Red-Green-Refactor cycle."""
    PHASES = {
        'RED': {'color': '#ff4444', 'icon': '🔴', 'text': 'RED - Write Failing Test', 'description': 'Test must fail to prove it tests something'},
        'GREEN': {'color': '#44ff44', 'icon': '🟢', 'text': 'GREEN - Make Test Pass', 'description': 'Implement minimum code to pass test'},
        'REFACTOR': {'color': '#4444ff', 'icon': '🔵', 'text': 'REFACTOR - Clean Code', 'description': 'Improve code quality while keeping tests green'},
        'IDLE': {'color': '#888888', 'icon': '⚪', 'text': 'Idle', 'description': 'Ready to start TDD cycle'}
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.current_phase = 'IDLE'
        self._create_phase_display()
        self._create_progress_bar()
        self._create_phase_timeline()

    def _create_phase_display(self):
        self.phase_frame = tk.Frame(self, bg='#1e1e1e', height=150)
        self.phase_frame.pack(fill='x', padx=10, pady=10)
        self.icon_label = tk.Label(self.phase_frame, text='⚪', font=('Arial', 72), bg='#1e1e1e', fg='#888888')
        self.icon_label.pack(side='left', padx=20)
        text_frame = tk.Frame(self.phase_frame, bg='#1e1e1e')
        text_frame.pack(side='left', fill='both', expand=True)
        self.phase_label = tk.Label(text_frame, text='Idle', font=('Arial', 24, 'bold'), bg='#1e1e1e', fg='#888888', anchor='w')
        self.phase_label.pack(anchor='w')
        self.description_label = tk.Label(text_frame, text='Ready to start TDD cycle', font=('Arial', 12), bg='#1e1e1e', fg='#cccccc', anchor='w')
        self.description_label.pack(anchor='w')

    def _create_progress_bar(self):
        self.progress_frame = tk.Frame(self, height=30)
        self.progress_frame.pack(fill='x', padx=10)
        self.progress = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=400)
        self.progress.pack(fill='x')

    def _create_phase_timeline(self):
        timeline_frame = tk.Frame(self, bg='#1e1e1e', height=60)
        timeline_frame.pack(fill='x', padx=10, pady=5)
        self.phase_bubbles = {}
        phases_to_show = ['RED', 'GREEN', 'REFACTOR']
        for i, phase in enumerate(phases_to_show):
            bubble = tk.Label(timeline_frame, text=self.PHASES[phase]['icon'], font=('Arial', 32), bg='#1e1e1e', fg='#444444')
            bubble.pack(side='left', padx=20)
            self.phase_bubbles[phase] = bubble
            if i < len(phases_to_show) - 1:
                tk.Label(timeline_frame, text='→', font=('Arial', 24), bg='#1e1e1e', fg='#666666').pack(side='left')

    def set_phase(self, phase_name: str, progress: int = None):
        if phase_name not in self.PHASES: return
        config = self.PHASES[phase_name]
        self.current_phase = phase_name
        self._animate_phase_change(config)
        self._update_timeline(phase_name)
        if progress is not None:
            self.progress.stop()
            self.progress.config(mode='determinate')
            self.progress['value'] = progress
        else:
            self.progress.config(mode='indeterminate')
            self.progress.start(10)

    def _animate_phase_change(self, config):
        for i in range(3):
            self.icon_label.config(fg=config['color']); self.phase_label.config(fg=config['color']); self.update(); self.after(150)
            self.icon_label.config(fg='#666666'); self.phase_label.config(fg='#666666'); self.update(); self.after(150)
        self.icon_label.config(text=config['icon'], fg=config['color'])
        self.phase_label.config(text=config['text'], fg=config['color'])
        self.description_label.config(text=config['description'])

    def _update_timeline(self, current_phase):
        phase_order = ['RED', 'GREEN', 'REFACTOR']
        current_index = phase_order.index(current_phase) if current_phase in phase_order else -1
        for i, phase in enumerate(phase_order):
            bubble = self.phase_bubbles[phase]
            if i < current_index: bubble.config(fg=self.PHASES[phase]['color'])
            elif i == current_index: bubble.config(fg=self.PHASES[phase]['color']); self._pulse_bubble(bubble, self.PHASES[phase]['color'])
            else: bubble.config(fg='#444444')

    def _pulse_bubble(self, bubble, color):
        def pulse(brightness=1.0, direction=-0.1):
            if self.current_phase not in self.phase_bubbles or self.phase_bubbles[self.current_phase] != bubble: return
            if brightness <= 0.3: direction = 0.1
            elif brightness >= 1.0: direction = -0.1
            new_brightness = brightness + direction
            dimmed_color = self._adjust_brightness(color, new_brightness)
            try:
                if bubble.winfo_exists():
                    bubble.config(fg=dimmed_color)
                    self.after(100, lambda: pulse(new_brightness, direction))
            except: pass
        pulse()

    @staticmethod
    def _adjust_brightness(hex_color, factor):
        r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
        r = int(r * factor); g = int(g * factor); b = int(b * factor)
        return f'#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}'

class TestResultsPanel(ttk.Frame):
    """Live-updating test results with syntax highlighting."""

    def __init__(self, parent):
        super().__init__(parent)
        self.stats_frame = tk.Frame(self, bg='#2b2b2b', height=50)
        self.stats_frame.pack(fill='x')
        self.passed_label = tk.Label(self.stats_frame, text='✅ Passed: 0', font=('Arial', 12, 'bold'), bg='#2b2b2b', fg='#00ff00')
        self.passed_label.pack(side='left', padx=10)
        self.failed_label = tk.Label(self.stats_frame, text='❌ Failed: 0', font=('Arial', 12, 'bold'), bg='#2b2b2b', fg='#ff0000')
        self.failed_label.pack(side='left', padx=10)
        self.duration_label = tk.Label(self.stats_frame, text='⏱️ Duration: 0.0s', font=('Arial', 12), bg='#2b2b2b', fg='#ffffff')
        self.duration_label.pack(side='left', padx=10)
        self.text = scrolledtext.ScrolledText(self, bg='#1e1e1e', fg='#ffffff', font=('Consolas', 10), wrap='word', state='disabled')
        self.text.pack(fill='both', expand=True)
        self._configure_tags()

    def _configure_tags(self):
        self.text.tag_config('passed', foreground='#00ff00', font=('Consolas', 10, 'bold'))
        self.text.tag_config('failed', foreground='#ff0000', font=('Consolas', 10, 'bold'))
        self.text.tag_config('error', foreground='#ff8800', background='#331100')
        self.text.tag_config('stdout', foreground='#cccccc')
        self.text.tag_config('stderr', foreground='#ff6666')
        self.text.tag_config('timestamp', foreground='#888888', font=('Consolas', 9, 'italic'))
        self.text.tag_config('separator', foreground='#444444')

    def stream_output(self, line: str, output_type: str = 'stdout'):
        self.text.config(state='normal')
        self.text.insert('end', f'[{datetime.now().strftime("%H:%M:%S")}] ', 'timestamp')
        self.text.insert('end', line + '\n', self._detect_line_type(line, output_type))
        self.text.see('end')
        self.text.config(state='disabled')
        self.update_idletasks()

    def _detect_line_type(self, line: str, default: str) -> str:
        l_line = line.lower()
        if any(x in l_line for x in ['✅', 'passed', 'ok']): return 'passed'
        if any(x in l_line for x in ['❌', 'failed', 'error']): return 'failed'
        if any(x in l_line for x in ['traceback', 'exception']): return 'error'
        if line.startswith('STDERR:'): return 'stderr'
        if line.startswith('='): return 'separator'
        return default

    def update_statistics(self, passed: int, failed: int, duration: float):
        self.passed_label.config(text=f'✅ Passed: {passed}')
        self.failed_label.config(text=f'❌ Failed: {failed}')
        self.duration_label.config(text=f'⏱️ Duration: {duration:.2f}s')
        color = '#330000' if failed > 0 else '#003300'
        original = self.stats_frame.cget('bg')
        self.stats_frame.config(bg=color)
        self.after(500, lambda: self.stats_frame.config(bg=original))

    def clear(self):
        self.text.config(state='normal'); self.text.delete('1.0', 'end'); self.text.config(state='disabled')

class InlineDiffViewer(ttk.Frame):
    """Inline git diff display."""

    def __init__(self, parent):
        super().__init__(parent)
        self.header = tk.Label(self, text='📝 File Changes', font=('Arial', 12, 'bold'), bg='#2b2b2b', fg='#ffffff', anchor='w', pady=5)
        self.header.pack(fill='x')
        self.diff_display = scrolledtext.ScrolledText(self, bg='#1e1e1e', fg='#cccccc', font=('Consolas', 9), wrap='none', state='disabled', height=15)
        self.diff_display.pack(fill='both', expand=True)
        self.diff_display.tag_config('addition', foreground='#00ff00')
        self.diff_display.tag_config('deletion', foreground='#ff0000')
        self.diff_display.tag_config('hunk', foreground='#00bfff', font=('Consolas', 9, 'bold'))
        self.diff_display.tag_config('file_header', foreground='#ffff00', font=('Consolas', 9, 'bold'))
        self.diff_display.tag_config('context', foreground='#888888')

    def show_diff(self, diff_content: str, commit_msg: str = None):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"show_diff called. Content length: {len(diff_content) if diff_content else 0}, commit: {commit_msg}")

        if not diff_content:
            return
        self.diff_display.config(state='normal'); self.diff_display.delete('1.0', 'end')
        if commit_msg:
            self.diff_display.insert('end', f'Commit: {commit_msg}\n', 'file_header')
            self.diff_display.insert('end', '=' * 80 + '\n\n', 'hunk')
        for line in diff_content.split('\n'):
            if line.startswith('+++') or line.startswith('---'): tag = 'file_header'
            elif line.startswith('+'): tag = 'addition'
            elif line.startswith('-'): tag = 'deletion'
            elif line.startswith('@@'): tag = 'hunk'
            else: tag = 'context'
            self.diff_display.insert('end', line + '\n', tag)
        self.diff_display.config(state='disabled'); self.diff_display.see('1.0')

    def show_file_changes_summary(self, files_changed: list):
        self.diff_display.config(state='normal'); self.diff_display.delete('1.0', 'end')
        self.diff_display.insert('end', f'📁 {len(files_changed)} file(s) changed:\n\n', 'file_header')
        for file_info in files_changed:
            icon = {'added': '🆕', 'modified': '📝', 'deleted': '🗑️'}.get(file_info['status'], '❓')
            line = f"  {icon} {file_info['path']}"
            if 'lines_added' in file_info: line += f" (+{file_info['lines_added']} -{file_info['lines_deleted']})"
            tag = {'added': 'addition', 'modified': 'hunk', 'deleted': 'deletion'}.get(file_info['status'], 'context')
            self.diff_display.insert('end', line + '\n', tag)
        self.diff_display.config(state='disabled')

class AccessibilityManager:
    """Manages accessibility features across the IDE."""
    KEYBOARD_SHORTCUTS = {
        '<F5>': 'run_red_phase', '<F6>': 'run_green_phase', '<F7>': 'run_refactor_phase',
        '<Control-t>': 'toggle_test_panel', '<Control-f>': 'toggle_file_tree', '<Control-g>': 'toggle_git_diff',
        '<Alt-1>': 'focus_file_tree', '<Alt-2>': 'focus_test_results', '<Alt-3>': 'focus_console', '<Escape>': 'stop_execution'
    }

    def __init__(self, root_window, controller=None):
        self.root = root_window; self.controller = controller
        self.screen_reader_enabled = self._detect_screen_reader()
        for key, action in self.KEYBOARD_SHORTCUTS.items():
            self.root.bind(key, lambda e, a=action: self._handle_shortcut(a))

    def _handle_shortcut(self, action):
        if self.controller and hasattr(self.controller, 'handle_action'): self.controller.handle_action(action)
        return "break"

    def announce(self, message: str, priority: str = 'polite'):
        print(f"[SCREEN READER] {priority.upper()}: {message}")

    def _detect_screen_reader(self) -> bool: return False # Placeholder

    def enable_high_contrast(self):
        style = ttk.Style()
        style.configure('Treeview', background='#000000', foreground='#ffffff', fieldbackground='#000000')

class AIPlanVisualizer(ttk.Frame):
    """Interactive sphere visualization of the AI Project Plan."""

    COLORS = {
        'completed': '#44ff44',
        'in_progress': '#ffff44',
        'pending': '#888888',
        'blocked': '#ff4444'
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg='#1e1e1e', highlightthickness=0, height=220)
        self.canvas.pack(fill='both', expand=True)

        self.tasks = []
        self.phases = [] # List of dicts {name, status, tasks, x, y, radius}
        self.pulse_val = 0
        self.pulse_dir = 1

        self.canvas.bind('<Configure>', lambda e: self.draw())
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>', self._on_hover)

        self.tooltip = None
        self.animating = True
        self._animate_pulse()

    def update_plan(self, tasks):
        self.tasks = tasks
        self._group_by_phase()
        self.draw()

    def _group_by_phase(self):
        phase_map = {}
        for task in self.tasks:
            # Task object from PlanParser has .phase attribute
            phase_name = getattr(task, 'phase', 'General')
            if phase_name not in phase_map:
                phase_map[phase_name] = []
            phase_map[phase_name].append(task)

        self.phases = []
        for name, tasks in phase_map.items():
            completed = len([t for t in tasks if getattr(t, 'status', '') == 'completed'])
            blocked = len([t for t in tasks if getattr(t, 'status', '') == 'blocked'])
            total = len(tasks)

            if completed == total: status = 'completed'
            elif blocked > 0: status = 'blocked'
            elif completed > 0: status = 'in_progress'
            else: status = 'pending'

            self.phases.append({
                'name': name,
                'status': status,
                'tasks': tasks,
                'progress': completed / total if total > 0 else 0
            })

    def draw(self):
        self.canvas.delete('all')
        if not self.phases:
            self.canvas.create_text(self.canvas.winfo_width()/2, 100, text="No plan loaded", fill='#888888', font=('Arial', 12))
            return

        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 200)

        # Calculate positions
        padding = 60
        num_phases = len(self.phases)
        spacing = (width - 2 * padding) / (num_phases - 1) if num_phases > 1 else 0
        x = padding if num_phases > 1 else width / 2
        y = height / 2 - 20
        radius = 30

        for i, phase in enumerate(self.phases):
            phase['x'] = x
            phase['y'] = y
            phase['radius'] = radius

            # Draw connection line to next phase
            if i < len(self.phases) - 1:
                next_x = x + spacing
                self.canvas.create_line(x, y, next_x, y, fill='#444444', width=2)

            x += spacing

        # Draw spheres (in separate loop to be on top of lines)
        for phase in self.phases:
            self._draw_sphere(phase)

    def _draw_sphere(self, phase):
        x, y, r = phase['x'], phase['y'], phase['radius']
        color = self.COLORS.get(phase['status'], self.COLORS['pending'])

        # Shadow
        self.canvas.create_oval(x-r+5, y-r+5, x+r+5, y+r+5, fill='#111111', outline='')

        # Gradient effect
        for i in range(r, 0, -4):
            factor = i / r
            c = self._adjust_brightness(color, 1.2 - 0.4 * factor)
            self.canvas.create_oval(x-i, y-i, x+i, y+i, fill=c, outline='', tags=(f"phase_{self.phases.index(phase)}", "sphere"))

        # Highlight
        self.canvas.create_oval(x-r/2, y-r/2, x-r/4, y-r/4, fill='#ffffff', outline='', tags=(f"phase_{self.phases.index(phase)}", "sphere"))

        # Outer ring
        self.canvas.create_oval(x-r, y-r, x+r, y+r, outline='#ffffff', width=1, tags=(f"phase_{self.phases.index(phase)}", "sphere"))

        # Progress arc
        if 0 < phase['progress'] < 1:
            self.canvas.create_arc(x-r-8, y-r-8, x+r+8, y+r+8, start=90, extent=-360*phase['progress'],
                                   outline='#00ffff', style='arc', width=3)
        elif phase['progress'] == 1:
            self.canvas.create_oval(x-r-8, y-r-8, x+r+8, y+r+8, outline='#44ff44', width=2)

        # Label
        self.canvas.create_text(x, y+r+25, text=phase['name'], fill='#ffffff', font=('Arial', 9, 'bold'),
                                width=120, justify='center', tags=(f"phase_{self.phases.index(phase)}", "label"))

    @staticmethod
    def _adjust_brightness(hex_color, factor):
        r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
        r = int(r * factor); g = int(g * factor); b = int(b * factor)
        return f'#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}'

    def stop_animations(self):
        """Stop all animations."""
        self.animating = False

    def start_animations(self):
        """Start animations if not already running."""
        if not self.animating:
            self.animating = True
            self._animate_pulse()

    def _animate_pulse(self):
        """Animates a pulsing effect on the active phase."""
        if not self.animating: return
        self.pulse_val += 0.05 * self.pulse_dir
        if self.pulse_val >= 1.0: self.pulse_dir = -1
        elif self.pulse_val <= 0.0: self.pulse_dir = 1

        # Find active phase spheres and update their rings
        for i, phase in enumerate(self.phases):
            if phase.get('status') == 'in_progress':
                tag = f"pulse_ring_{i}"
                self.canvas.delete(tag)
                x, y, r = phase['x'], phase['y'], phase['radius']
                pulse_r = r + 5 + (self.pulse_val * 10)
                # Color transition from yellow to background
                bg_color = [30, 30, 30] # #1e1e1e
                fg_color = [255, 255, 68] # #ffff44
                mixed = [int(bg_color[j] + (fg_color[j] - bg_color[j]) * (1.0 - self.pulse_val)) for j in range(3)]
                color = f'#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}'
                self.canvas.create_oval(x-pulse_r, y-pulse_r, x+pulse_r, y+pulse_r, outline=color, width=2, tags=tag)

        self.after(50, self._animate_pulse)

    def _animate_progress(self):
        # Implementation for smooth transitions can go here
        pass

    def _on_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if not item: return

        # Check if we clicked within the radius of a sphere
        for i, phase in enumerate(self.phases):
            dist = ((event.x - phase['x'])**2 + (event.y - phase['y'])**2)**0.5
            if dist <= phase['radius'] + 10:
                self._show_phase_details(phase)
                return

    def _show_phase_details(self, phase):
        details = f"Phase: {phase['name']}\n"
        details += f"Status: {phase['status'].upper()}\n"
        details += f"Progress: {int(phase['progress']*100)}%\n"
        details += "-" * 40 + "\n"
        for t in phase['tasks']:
            icon = '✅' if getattr(t, 'status', '') == 'completed' else ('❌' if getattr(t, 'status', '') == 'blocked' else '⬜')
            desc = getattr(t, 'description', 'No description')
            details += f"{icon} {desc}\n"

        messagebox.showinfo(f"Phase Details - {phase['name']}", details)

    def _on_hover(self, event):
        # Change cursor when hovering over spheres
        found = False
        self.canvas.delete('hover_info')

        for phase in self.phases:
            dist = ((event.x - phase['x'])**2 + (event.y - phase['y'])**2)**0.5
            if dist <= phase['radius'] + 10:
                self.canvas.config(cursor='hand2')
                # Show quick info
                self.canvas.create_text(phase['x'], phase['y'] - phase['radius'] - 15,
                                        text=f"{int(phase['progress']*100)}% Complete",
                                        fill='#00ffff', font=('Arial', 8, 'bold'), tags='hover_info')
                found = True
                break

        if not found:
            self.canvas.config(cursor='')
