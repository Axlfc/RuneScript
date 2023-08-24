from crontab import CronTab
import subprocess
import tempfile
from time import sleep
import os
import re


def make_tag():
    current_tags = text.tag_names()
    if "bold" in current_tags:
        weight = "bold"
    else:
        weight = "normal"

    if "italic" in current_tags:
        slant = "italic"
    else:
        slant = "roman"

    if "underline" in current_tags:
        underline = 1
    else:
        underline = 0

    if "overstrike" in current_tags:
        overstrike = 1
    else:
        overstrike = 0

    big_font = tkinter.font.Font(text, text.cget("font"))
    big_font.configure(slant=slant, weight=weight, underline=underline, overstrike=overstrike,
                       family=current_font_family, size=current_font_size)
    text.tag_config("BigTag", font=big_font, foreground=fontColor, background=fontBackground)
    if "BigTag" in current_tags:
        text.tag_remove("BigTag", 1.0, END)
    text.tag_add("BigTag", 1.0, END)


def new(event=None):
    global file_name

    ans = messagebox.askquestion(title="Save File", message="Would you like to save this file?")
    if ans == "yes":
        save()

    file_name = ""
    script_text.delete('1.0', 'end')
    root.title("*New file - Script Editor")


def open_file(event=None):
    new()
    file = filedialog.askopenfile()
    global file_name
    file_name = file.name
    text.insert(INSERT, file.read())


'''def save(event=None):
    global file_name
    if file_name == "":
        path = filedialog.asksaveasfilename()
        file_name = path
    root.title(file_name + " - Script Editor")
    write = open(file_name, mode='w')
    write.write(text.get("1.0", END))'''


def save():
    global file_name

    if file_name:
        # Save the file
        with open(file_name, 'w') as file:
            file.write(script_text.get('1.0', 'end-1c'))

        # Update the window title
        root.title(file_name + " - Script Editor")
    else:
        save_as()

    # Remove the asterisk from the title
    root.title(root.title().replace('*', ''))


def update_modification_status(event):
    set_modified_status(True)


def on_text_change(event=None):
    global is_modified

    if not is_modified:
        is_modified = True
        root.title("*" + root.title())


'''def save_as(event=None):
    if file_name == "":
        save()
        return "break"
    f = filedialog.asksaveasfile(mode='w')
    if f is None:
        return
    text2save = str(text.get(1.0, END))
    f.write(text2save)
    f.close()'''


def save_as():
    global file_name

    new_file_name = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if new_file_name:
        file_name = new_file_name
        save()
    else:
        messagebox.showinfo("Info", "File saving canceled.")


def rename(event=None):
    global file_name
    if file_name == "":
        # Prompt the user to enter the file path or select a file using a file dialog
        file_path = simpledialog.askstring("Rename", "Enter file path or select a file")
        if not file_path:
            # User cancelled the operation
            return

        print("File path:", file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return

        file_name = file_path

    # Extract the directory path and file name
    dir_path, old_name = os.path.split(file_name)
    new_name = simpledialog.askstring("Rename", "Enter new name")

    try:
        # Rename the file
        new_path = os.path.join(dir_path, new_name)
        os.rename(file_name, new_path)
        file_name = new_path
        root.title(file_name + " - Script Editor")
    except OSError as e:
        messagebox.showerror("Error", f"Failed to rename file: {e}")


def close(event=None):
    save()
    root.quit()


# EDIT MENU METHODS

def cut(event=None):
    # first clear the previous text on the clipboard.
    root.clipboard_clear()
    text.clipboard_append(string=text.selection_get())
    # index of the first and yhe last letter of our selection.
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


def copy(event=None):
    # first clear the previous text on the clipboard.
    print(text.index(SEL_FIRST))
    print(text.index(SEL_LAST))
    root.clipboard_clear()
    text.clipboard_append(string=text.selection_get())


def paste(event=None):
    # get gives everyting from the clipboard and paste it on the current cursor position
    # it does'nt removes it from the clipboard.
    text.insert(INSERT, root.clipboard_get())


def undo():
    text.edit_undo()


def redo():
    text.edit_redo()


def select_all(event=None):
    text.tag_add(SEL, "1.0", END)


def delete_all():
    text.delete(1.0, END)


def duplicate(event=None):
    selected_text = text.get("sel.first", "sel.last")
    text.insert("insert", selected_text)


def show_context_menu(event):
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()


def delete():
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


# TOOLS MENU METHODS

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


# Adding Search Functionality

def check(value):
    text.tag_remove('found', '1.0', END)
    text.tag_config('found', foreground='red')
    list_of_words = value.split(' ')
    for word in list_of_words:
        idx = '1.0'
        while idx:
            idx = text.search(word, idx, nocase=1, stopindex=END)
            if idx:
                lastidx = '%s+%dc' % (idx, len(word))
                text.tag_add('found', idx, lastidx)
                print(lastidx)
                idx = lastidx


# implementation of search dialog box - calling the check method to search and find_text_cancel_button to close it
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


# FORMAT BAR METHODS

def bold(event=None):
    current_tags = text.tag_names()
    if "bold" in current_tags:
        # first char is bold, so unbold the range
        text.tag_delete("bold", 1.0, END)
    else:
        # first char is normal, so bold the whole selection
        text.tag_add("bold", 1.0, END)
    make_tag()


def italic(event=None):
    current_tags = text.tag_names()
    if "italic" in current_tags:
        text.tag_add("roman", 1.0, END)
        text.tag_delete("italic", 1.0, END)
    else:
        text.tag_add("italic", 1.0, END)
    make_tag()


def underline(event=None):
    current_tags = text.tag_names()
    if "underline" in current_tags:
        text.tag_delete("underline", 1.0, END)
    else:
        text.tag_add("underline", 1.0, END)
    make_tag()


def strike():
    current_tags = text.tag_names()
    if "overstrike" in current_tags:
        text.tag_delete("overstrike", "1.0", END)

    else:
        text.tag_add("overstrike", 1.0, END)

    make_tag()


def highlight():
    color = colorchooser.askcolor(initialcolor='white')
    color_rgb = color[1]
    global fontBackground
    fontBackground = color_rgb
    current_tags = text.tag_names()
    if "background_color_change" in current_tags:
        text.tag_delete("background_color_change", "1.0", END)
    else:
        text.tag_add("background_color_change", "1.0", END)
    make_tag()


# To make align functions work properly
def remove_align_tags():
    all_tags = text.tag_names(index=None)
    if "center" in all_tags:
        text.tag_remove("center", "1.0", END)
    if "left" in all_tags:
        text.tag_remove("left", "1.0", END)
    if "right" in all_tags:
        text.tag_remove("right", "1.0", END)


# align_center
def align_center(event=None):
    remove_align_tags()
    text.tag_configure("center", justify='center')
    text.tag_add("center", 1.0, "end")


# align_justify
def align_justify():
    remove_align_tags()


# align_left
def align_left(event=None):
    remove_align_tags()
    text.tag_configure("left", justify='left')
    text.tag_add("left", 1.0, "end")


# align_right
def align_right(event=None):
    remove_align_tags()
    text.tag_configure("right", justify='right')
    text.tag_add("right", 1.0, "end")


# Font and size change functions - BINDED WITH THE COMBOBOX SELECTION
# change font and size are methods binded with combobox, calling fontit and sizeit
# called when <<combobox>> event is called

def change_font(event):
    f = all_fonts.get()
    global current_font_family
    current_font_family = f
    make_tag()


def change_size(event):
    sz = int(all_size.get())
    global current_font_size
    current_font_size = sz
    make_tag()


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event):
        self.tooltip = Toplevel()
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def leave(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None




# Help Menu
def about(event=None):
    messagebox.showinfo("About",
                        "ScriptsEditor\nCreated in Python using Tkinter\nAxlfc, 2023")


def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        os.chdir(directory)
        directory_label.config(text=f"{directory}")
        # open_first_text_file(directory)


'''
def open_first_text_file(directory):
    text_files = get_text_files(directory)
    if text_files:
        file_path = os.path.join(directory, text_files[0])
        open_file(file_path)
'''


def get_text_files(directory):
    text_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            text_files.append(file)
    return text_files


def open_script():
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("Python Scripts", "*.py"), ("Shell Scripts", "*.sh"), ("Text Files", "*.txt"), ("TeX Files", "*.tex")])
    if file_path:
        open_file(file_path)
    set_modified_status(False)  # Reset the modification status


def open_file(file_path):
    script_name_label.config(text=f"{os.path.basename(file_path)}")
    with open(file_path, "r") as file:
        script_content = file.read()
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)
    colorize_text()


def set_modified_status(value):
    global is_modified
    is_modified = value
    update_title()


def update_title():
    title = root.title()
    if is_modified and not title.startswith("*"):
        root.title("*" + title)
    elif not is_modified and title.startswith("*"):
        root.title(title[1:])


def save_script():
    script_name = script_name_label.cget("text").split(": ")[-1]
    if script_name:
        script_content = script_text.get("1.0", "end")
        save_file(script_name, script_content)
        set_modified_status(False)  # Reset the modification status
    else:
        save_as_new_script()


def remove_asterisk_from_title():
    title = root.title()
    if title.startswith("*"):
        root.title(title[1:])


def save_as_new_script():
    file_types = [("Python Scripts", "*.py"),
                  ("Shell Scripts", "*.sh"),
                  ("Text Files", "*.txt"),
                  ("LaTeX Files", "*.tex"),
                  ("All Files", "*.*")]
    file = filedialog.asksaveasfile(filetypes=file_types)
    if file is not None:
        # Get the selected file type
        selected_extension = file.name.split('.')[-1]
        # Append the selected extension to the file name
        file_path = file.name + '.' + selected_extension
        # Implement your save logic here using the file_path
        file.close()


def save_file(file_name, content):
    with open(file_name, "w") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def colorize_text():
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def see_stdout():
    stdout_window = Toplevel(root)
    stdout_window.title("Standard Output (stdout)")
    stdout_text = Text(stdout_window)
    stdout_text.pack()

    script_out_name = script_name_label.cget('text') + ".out"
    try:
        with open(script_out_name, "r") as f:
            stdout_text.insert("1.0", f.read())
    except FileNotFoundError:
        stdout_text.insert("1.0", "No stdout data available.")


def see_stderr():
    stderr_window = Toplevel(root)
    stderr_window.title("Standard Error (stderr)")
    stderr_text = Text(stderr_window)
    stderr_text.pack()

    script_err_name = script_name_label.cget('text') + ".err"
    try:
        with open(script_err_name, "r") as f:
            stderr_text.insert("1.0", f.read())
    except FileNotFoundError:
        stderr_text.insert("1.0", "No stderr data available.")

    # Configure the text widget to use red font color
    stderr_text.tag_configure("red", foreground="red")
    stderr_text.tag_add("red", "1.0", "end")


def run_script():
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_with_timeout(timeout_seconds):
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(
            ["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        sleep(timeout_seconds)
        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_once(schedule_time):
    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Extract hour, minute, and AM/PM from the input time string
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', schedule_time)
    if not match:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM AM/PM format.")
        return

    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm = match.group(3)

    # Adjust hour for 12-hour clock format
    if am_pm and am_pm.lower() == 'pm' and hour != 12:
        hour += 12

    if am_pm and am_pm.lower() == 'am' and hour == 12:
        hour = 0

    if not validate_time(hour, minute):
        return

    try:
        # Use the 'at' command to schedule the script execution and redirection
        at_time = f"{hour:02d}:{minute:02d}"

        stdout_redirect = f">{script_name_label.cget('text')}.out" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{script_name_label.cget('text')}.err" if generate_stderr else "/dev/null"

        at_command = f"atq; at {at_time} <<EOF\n{script_path} {arguments} {stdout_redirect} {stderr_redirect}\nEOF"

        process = subprocess.Popen(at_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled to run at {at_time}.")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def run_script_crontab(minute, hour, day, month, day_of_week):
    if not minute or not hour or not day or not month or not day_of_week:
        messagebox.showerror("Error Scheduling Script", "All cron schedule fields must be filled.")
        return

    # Build the cron schedule string
    cron_schedule = f"{minute} {hour} {day} {month} {day_of_week}"

    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()

    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Determine the full path for .out and .err files based on the selected directory
    out_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.out")
    err_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.err")

    try:
        stdout_redirect = f">{out_file}" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{err_file}" if generate_stderr else "/dev/null"

        # Use the 'crontab' command to set up the script execution schedule
        crontab_command = f"(crontab -l; echo '{cron_schedule} {script_path} {arguments} {stdout_redirect} {stderr_redirect}') | crontab -"
        process = subprocess.Popen(crontab_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled with cron: {cron_schedule}")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def validate_time(hour, minute):
    try:
        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format.")
        return False


def open_at_window():
    def update_at_jobs():
        listbox.delete(0, END)
        populate_at_jobs(listbox)
        at_window.after(5000, update_at_jobs)

    global at_window
    at_window = Toplevel(root)
    at_window.title("AT Jobs")
    at_window.geometry("600x400")

    listbox = Listbox(at_window, width=80)
    listbox.pack(fill="both", expand=True)

    populate_at_jobs(listbox)

    remove_button = Button(at_window, text="Remove Selected", command=lambda: remove_selected_at_job(listbox))
    remove_button.pack(side="bottom")

    at_window.after(0, update_at_jobs)
    at_window.mainloop()


def populate_at_jobs(listbox):
    try:
        at_output = subprocess.check_output(["atq"], text=True).splitlines()
        if not at_output:
            username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
            listbox.insert(END, f"No AT jobs found for user {username}.")
        else:
            for line in at_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to retrieve AT jobs")


def remove_selected_at_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return

    selected_index = selected_indices[0]
    selected_item = listbox.get(selected_index)

    if "No AT jobs found for user" in selected_item:
        listbox.delete(selected_index)  # Delete the special message
    else:
        job_id = selected_item.split()[0]
        try:
            subprocess.run(["atrm", job_id], check=True)
            listbox.delete(selected_index)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to remove AT job {job_id}")


def open_cron_window():
    def update_cron_jobs():
        listbox.delete(0, END)
        populate_cron_jobs(listbox)
        crontab_window.after(5000, update_cron_jobs)

    global crontab_window
    crontab_window = Toplevel(root)
    crontab_window.title("Cron Jobs")
    crontab_window.geometry("600x400")

    listbox = Listbox(crontab_window, width=80)
    listbox.pack(fill="both", expand=True)

    listbox.insert(END, "Loading cron jobs...")  # Initial message while loading
    populate_cron_jobs(listbox)

    remove_button = Button(crontab_window, text="Remove Selected", command=lambda: remove_selected_cron_job(listbox))
    remove_button.pack(side="bottom")

    crontab_window.after(0, update_cron_jobs)
    crontab_window.mainloop()


def populate_cron_jobs(listbox):
    try:
        cron_output = subprocess.check_output(["crontab", "-l"], text=True).splitlines()
        # print("hola" + cron_output)
        if not cron_output:
            username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
            listbox.insert(END, f"No cron jobs found for user {username}.")
        else:
            for line in cron_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
        listbox.insert(END, f"No cron jobs found for user {username}.")
        #messagebox.showwarning("Warning", "Failed to retrieve cron jobs")



