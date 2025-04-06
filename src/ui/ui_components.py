import tkinter as tk
from tkinter import ttk, scrolledtext


def create_project_tree(parent, on_select):
    tree = ttk.Treeview(parent, columns=('path',), show='tree')
    tree.pack(fill=tk.BOTH, expand=True)
    tree.bind('<<TreeviewSelect>>', on_select)
    return tree


def create_output_console(parent):
    console = scrolledtext.ScrolledText(
        parent, height=15, wrap=tk.WORD, state='disabled'
    )
    console.pack(fill=tk.X, side=tk.BOTTOM)
    return console


def create_ai_plan(parent):
    plan_frame = ttk.LabelFrame(parent, text="AI Project Plan")
    listbox = tk.Listbox(plan_frame, height=10)
    listbox.pack(fill=tk.BOTH, expand=True)
    parent.add(plan_frame)
    return listbox


def create_file_editor(parent, on_modified):
    editor_frame = ttk.LabelFrame(parent, text="File Contents")
    editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, undo=True)
    editor.pack(fill=tk.BOTH, expand=True)
    editor.bind('<<Modified>>', on_modified)
    parent.add(editor_frame)
    return editor


def create_command_bar(parent, on_generate, on_pause, on_stop):
    command_bar = ttk.Frame(parent)
    command_bar.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(command_bar, text="Project Prompt:").pack(side=tk.LEFT, padx=(0, 5))
    prompt_entry = ttk.Entry(command_bar, width=50)
    prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    button_frame = ttk.Frame(command_bar)
    button_frame.pack(side=tk.LEFT, padx=5)

    generate_btn = ttk.Button(button_frame, text="Generate Project", command=on_generate)
    generate_btn.pack(side=tk.LEFT, padx=2)

    pause_btn = ttk.Button(button_frame, text="Pause", command=on_pause, state=tk.DISABLED)
    pause_btn.pack(side=tk.LEFT, padx=2)

    stop_btn = ttk.Button(button_frame, text="Stop", command=on_stop, state=tk.DISABLED)
    stop_btn.pack(side=tk.LEFT, padx=2)

    return prompt_entry, generate_btn, pause_btn, stop_btn
