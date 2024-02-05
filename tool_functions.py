import os
import subprocess
import threading
from tkinter import colorchooser, END, Toplevel, Label, Entry, Button, scrolledtext, IntVar, Menu, StringVar

import markdown
from tkhtmlview import HTMLLabel

from script_tasks import show_selected_model
from tk_utils import text, script_text, root
from utility_functions import make_tag


def change_color():
    color = colorchooser.askcolor(initialcolor='#ff0000')
    color_name = color[1]
    global fontColor
    fontColor = color_name
    current_tags = text.tag_names()
    if "font_color_change" in current_tags:
        # first char is bold, so unbold the range
        text.tag_delete("font_color_change", 1.0, END)
    else:
        # first char is normal, so bold the whole selection
        text.tag_add("font_color_change", 1.0, END)
    make_tag()


def colorize_text():
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def check(value):
    script_text.tag_remove('found', '1.0', END)

    if value:
        script_text.tag_config('found', background='yellow')
        idx = '1.0'
        while idx:
            idx = script_text.search(value, idx, nocase=1, stopindex=END)
            if idx:
                lastidx = f"{idx}+{len(value)}c"
                script_text.tag_add('found', idx, lastidx)
                idx = lastidx


def search_and_replace(search_text, replace_text):
    if search_text:
        start_index = '1.0'
        while True:
            start_index = script_text.search(search_text, start_index, nocase=1, stopindex=END)
            if not start_index:
                break
            end_index = f"{start_index}+{len(search_text)}c"
            script_text.delete(start_index, end_index)
            script_text.insert(start_index, replace_text)
            start_index = end_index


def find_text(event=None):
    search_toplevel = Toplevel(root)
    search_toplevel.title('Find Text')
    search_toplevel.transient(root)
    search_toplevel.resizable(False, False)
    Label(search_toplevel, text="Find All:").grid(row=0, column=0, sticky='e')
    search_entry_widget = Entry(search_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')
    search_entry_widget.focus_set()
    Button(search_toplevel, text="Ok", underline=0, command=lambda: check(search_entry_widget.get())).grid(row=0,
                                                                                                           column=2,
                                                                                                           sticky='e' + 'w',
                                                                                                           padx=2,
                                                                                                           pady=5)
    Button(search_toplevel, text="Cancel", underline=0, command=lambda: find_text_cancel_button(search_toplevel)).grid(
        row=0, column=4, sticky='e' + 'w', padx=2, pady=2)


# remove search tags and destroys the search box
def find_text_cancel_button(search_toplevel):
    text.tag_remove('found', '1.0', END)
    search_toplevel.destroy()
    return "break"


def open_search_replace_dialog():
    search_replace_toplevel = Toplevel(root)
    search_replace_toplevel.title('Search and Replace')
    search_replace_toplevel.transient(root)
    search_replace_toplevel.resizable(False, False)

    # Campo de búsqueda
    Label(search_replace_toplevel, text="Find:").grid(row=0, column=0, sticky='e')
    search_entry_widget = Entry(search_replace_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')

    # Campo de reemplazo
    Label(search_replace_toplevel, text="Replace:").grid(row=1, column=0, sticky='e')
    replace_entry_widget = Entry(search_replace_toplevel, width=25)
    replace_entry_widget.grid(row=1, column=1, padx=2, pady=2, sticky='we')

    # Botones
    Button(search_replace_toplevel, text="Replace All", command=lambda: search_and_replace(search_entry_widget.get(), replace_entry_widget.get())).grid(row=2, column=1, sticky='e' + 'w', padx=2, pady=5)


def open_terminal_window():
    terminal_window = Toplevel()
    terminal_window.title("Python Terminal")
    terminal_window.geometry("600x400")

    # Create a ScrolledText widget to display terminal output
    output_text = scrolledtext.ScrolledText(terminal_window, height=20, width=80)
    output_text.pack(fill='both', expand=True)

    # Initialize a list to store command history
    command_history = []
    # Initialize a pointer to the current position in the command history
    history_pointer = [0]

    # Function to execute the command from the entry widget
    def execute_command(event=None):
        # Get the command from entry widget
        command = entry.get()
        if command.strip():
            # Add command to history and reset history pointer
            command_history.append(command)
            history_pointer[0] = len(command_history)

            try:
                # Run the command and get the output
                output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, text=True, cwd=os.getcwd())
                output_text.insert(END, f"{command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                # If there's an error, print it to the output widget
                output_text.tag_configure("error", foreground="red")
                output_text.insert(END, f"Error: {e.output}", "error")
            # Clear the entry widget
            entry.delete(0, END)
            output_text.see(END)  # Auto-scroll to the bottom

    # Function to navigate the command history
    def navigate_history(event):
        if command_history:
            # UP arrow key pressed
            if event.keysym == 'Up':
                history_pointer[0] = max(0, history_pointer[0] - 1)
            # DOWN arrow key pressed
            elif event.keysym == 'Down':
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            # Get the command from history
            command = command_history[history_pointer[0]] if history_pointer[0] < len(command_history) else ''
            # Set the command to the entry widget
            entry.delete(0, END)
            entry.insert(0, command)

    # Create an Entry widget for typing commands
    entry = Entry(terminal_window, width=80)
    entry.pack(side='bottom', fill='x')
    entry.focus()
    entry.bind("<Return>", execute_command)
    # Bind the UP and DOWN arrow keys to navigate the command history
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)


def open_ai_assistant_window():
    global original_md_content, markdown_render_enabled, rendered_html_content
    original_md_content = ""
    rendered_html_content = ""
    markdown_render_enabled = False
    render_markdown_var = IntVar()

    def on_md_content_change(event=None):
        global original_md_content
        original_md_content = script_text.get("1.0", END)
        print("on_md_content_change: original_md_content updated")  # Debug print
        if markdown_render_enabled:
            print("on_md_content_change: markdown_render_enabled is True, updating HTML content")  # Debug print
            update_html_content()
        else:
            print("on_md_content_change: markdown_render_enabled is False")  # Debug print

    def update_html_content():
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        print("update_html_content: rendered_html_content updated")  # Debug print
        html_display.set_html(rendered_html_content)

    def toggle_render_markdown(is_checked):
        global markdown_render_enabled
        markdown_render_enabled = bool(is_checked)
        print(f"toggle_render_markdown: Markdown to HTML toggled: {markdown_render_enabled}")  # Debug print

        if markdown_render_enabled:
            print("toggle_render_markdown: Calling update_html_content")  # Debug print
            update_html_content()
            output_text.pack_forget()
            html_display.pack(fill='both', expand=True)
        else:
            output_text.delete("1.0", "end")
            output_text.insert("1.0", original_md_content)
            html_display.pack_forget()
            output_text.pack(fill='both', expand=True)

    ai_assistant_window = Toplevel()
    ai_assistant_window.title("AI Assistant")
    ai_assistant_window.geometry("600x400")

    # Create a Menu Bar
    menu_bar = Menu(ai_assistant_window)
    ai_assistant_window.config(menu=menu_bar)

    # Create a 'Settings' Menu
    settings_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)

    # Add 'Selected Model' Menu Item
    settings_menu.add_command(label="Selected Model", command=show_selected_model)

    # Checkbox Variable for 'Render Markdown to HTML'
    render_markdown_var = IntVar()
    settings_menu.add_checkbutton(
        label="Render Markdown to HTML",
        onvalue=1,
        offvalue=0,
        variable=render_markdown_var,
        command=lambda: toggle_render_markdown(render_markdown_var.get())
    )

    # Create the output text widget
    output_text = scrolledtext.ScrolledText(ai_assistant_window, height=20, width=80)
    output_text.pack(fill='both', expand=True)

    # Create an HTMLLabel for rendering HTML
    html_display = HTMLLabel(ai_assistant_window, html="")

    html_display.pack(fill='both', expand=False)
    html_display.pack_forget()  # Initially hide the HTML display

    status_label_var = StringVar()
    status_label = Label(ai_assistant_window, textvariable=status_label_var)
    status_label.pack()
    status_label_var.set("READY")  # Initialize the status label as "READY"

    # Initialize a list to store command history
    command_history = []
    # Initialize a pointer to the current position in the command history
    history_pointer = [0]

    output_text.insert(END, "> ")
    output_text.bind("<<TextModified>>", on_md_content_change)
    output_text.see(END)

    def navigate_history(event):
        if command_history:
            # UP arrow key pressed
            if event.keysym == 'Up':
                history_pointer[0] = max(0, history_pointer[0] - 1)
            # DOWN arrow key pressed
            elif event.keysym == 'Down':
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            # Get the command from history
            command = command_history[history_pointer[0]] if history_pointer[0] < len(command_history) else ''
            # Set the command to the entry widget
            entry.delete(0, END)
            entry.insert(0, command)

    def stream_output(process):
        try:
            output_buffer = ""  # Initialize an empty buffer
            buffer_size = 2  # Set the size of the buffer to hold the last two characters
            global original_md_content

            while True:
                char = process.stdout.read(1)  # Read one character at a time
                if char:
                    if markdown_render_enabled:
                        # Append new char to Markdown content and update HTML content
                        original_md_content += char
                        update_html_content()
                    else:
                        # Append new char to Markdown content
                        original_md_content += char
                        output_text.insert(END, char)
                        output_text.see(END)

                    # Update the Tkinter window; use after method to ensure GUI updates
                    ai_assistant_window.after(10, lambda: ai_assistant_window.update_idletasks())

                    # Update the buffer with the latest character
                    output_buffer += char
                    output_buffer = output_buffer[-buffer_size:]  # Keep only the last 'buffer_size' characters

                    # Check if the last two characters are '> ' indicating the end of the response
                    if output_buffer == '> ':
                        break
                elif process.poll() is not None:
                    break  # Break if the subprocess has finished

        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
        finally:
            on_processing_complete()

    def on_processing_complete():
        print("Debug: Processing complete, re-enabling entry widget.")  # Debug print
        entry.config(state='normal')  # Re-enable the entry widget
        status_label_var.set("READY")  # Update label to show AI is processing

    def execute_ai_assistant_command():
        global process, original_md_content  # Define process as a global variable

        ai_command = entry.get()
        if ai_command.strip():
            original_md_content += "\n" + ai_command  # Append command to Markdown content
            output_text.insert(END, f"You: {ai_command}\n")
            entry.delete(0, END)
            entry.config(state='disabled')  # Disable entry while processing
            status_label_var.set("AI is thinking...")  # Update label to show AI is processing

            ai_script_path = r"C:\Users\AxelFC\Documents\git\UE5-python\Content\Python\src\text\ai_assistant.py"
            command = ['python', ai_script_path, ai_command]

            # Terminate existing subprocess if it exists
            if 'process' in globals() and process.poll() is None:
                process.terminate()

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                           bufsize=1)
                threading.Thread(target=stream_output, args=(process,)).start()
            except Exception as e:
                output_text.insert(END, f"Error: {e}\n")
                on_processing_complete()
            finally:
                update_html_content()
        else:
            entry.config(state='normal')  # Re-enable the entry widget if no command is entered


    entry = Entry(ai_assistant_window, width=30)
    entry.pack(side='bottom', fill='x')
    entry.focus()
    entry.bind("<Return>", lambda event: execute_ai_assistant_command())
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)

    print("open_ai_assistant_window: Window opened")  # Debug print
    ai_assistant_window.mainloop()
    print("open_ai_assistant_window: Mainloop ended")  # Debug print