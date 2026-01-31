import os
import re

windows_dir = 'src/window'
files = [f for f in os.listdir(windows_dir) if f.endswith('.py')]

for filename in files:
    filepath = os.path.join(windows_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for usage of constants without 'tk.' or 'ctk.'
    # and check if they are imported

    # Common constants
    constants = ['END', 'INSERT', 'W', 'E', 'N', 'S', 'BOTH', 'X', 'Y', 'HORIZONTAL', 'VERTICAL', 'LEFT', 'RIGHT', 'RAISED', 'SUNKEN', 'DISABLED', 'NORMAL', 'WORD', 'NONE', 'SOLID', 'NO', 'W', 'E', 'NW']

    needs_tk = False
    for const in constants:
        if re.search(r'\b' + const + r'\b', content) and not re.search(r'tk\.' + const, content) and not re.search(r'from tkinter import .*\b' + const + r'\b', content) and not re.search(r'from tkinter\.constants import .*\b' + const + r'\b', content):
            # Replace with tk.CONST
            content = re.sub(r'\b' + const + r'\b', 'tk.' + const, content)
            needs_tk = True

    # Fix Menu, Toplevel, Frame, Label, Entry, Button if used as classes
    classes = ['Menu', 'Toplevel', 'Frame', 'Label', 'Entry', 'Button', 'Text', 'Canvas', 'Scrollbar', 'PanedWindow', 'StringVar', 'IntVar', 'BooleanVar']
    for cls in classes:
        if re.search(r'\b' + cls + r'\(', content) and not re.search(r'tk\.' + cls, content) and not re.search(r'ctk\.CTk' + cls, content) and not re.search(r'from tkinter import .*\b' + cls + r'\b', content):
             content = re.sub(r'\b' + cls + r'\(', 'tk.' + cls + '(', content)
             needs_tk = True

    if needs_tk:
        if 'import tkinter as tk' not in content:
            if 'import tkinter' in content:
                content = content.replace('import tkinter', 'import tkinter as tk')
            else:
                content = 'import tkinter as tk\n' + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated imports in {filename}")
