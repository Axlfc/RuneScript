import os
import subprocess
import tempfile
from tkinter import END, Toplevel, Listbox, Button, messagebox, Label, Entry
from src.views.tk_utils import root
from lib.winTaskScheduler import list_tasks, delete_task, at_function, crontab_function

def open_at_window():

    def update_at_jobs():
        listbox.delete(0, END)
        populate_at_jobs(listbox)
        at_window.after(5000, update_at_jobs)
    global at_window
    at_window = Toplevel(root)
    at_window.title('AT Jobs')
    at_window.geometry('600x400')
    listbox = Listbox(at_window, width=80)
    listbox.pack(fill='both', expand=True)
    populate_at_jobs(listbox)
    remove_button = Button(at_window, text='Remove Selected', command=lambda: remove_selected_at_job(listbox))
    remove_button.pack(side='bottom')
    at_window.after(0, update_at_jobs)
    at_window.mainloop()

def populate_at_jobs(listbox):
    try:
        at_output = subprocess.check_output(['atq'], text=True).splitlines()
        if not at_output:
            username = subprocess.check_output(['whoami'], text=True).strip()
            listbox.insert(END, f'No AT jobs found for user {username}.')
        else:
            for line in at_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        messagebox.showerror('Error', 'Failed to retrieve AT jobs')

def remove_selected_at_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return
    selected_index = selected_indices[0]
    selected_item = listbox.get(selected_index)
    if 'No AT jobs found for user' in selected_item:
        listbox.delete(selected_index)
    else:
        job_id = selected_item.split()[0]
        try:
            subprocess.run(['atrm', job_id], check=True)
            listbox.delete(selected_index)
        except subprocess.CalledProcessError:
            messagebox.showerror('Error', f'Failed to remove AT job {job_id}')

def open_cron_window():

    def update_cron_jobs():
        listbox.delete(0, END)
        populate_cron_jobs(listbox)
        crontab_window.after(5000, update_cron_jobs)
    global crontab_window
    crontab_window = Toplevel(root)
    crontab_window.title('Cron Jobs')
    crontab_window.geometry('600x400')
    listbox = Listbox(crontab_window, width=80)
    listbox.pack(fill='both', expand=True)
    listbox.insert(END, 'Loading cron jobs...')
    populate_cron_jobs(listbox)
    remove_button = Button(crontab_window, text='Remove Selected', command=lambda: remove_selected_cron_job(listbox))
    remove_button.pack(side='bottom')
    crontab_window.after(0, update_cron_jobs)
    crontab_window.mainloop()

def populate_cron_jobs(listbox):
    try:
        cron_output = subprocess.check_output(['crontab', '-l'], text=True).splitlines()
        if not cron_output:
            username = subprocess.check_output(['whoami'], text=True).strip()
            listbox.insert(END, f'No cron jobs found for user {username}.')
        else:
            for line in cron_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        username = subprocess.check_output(['whoami'], text=True).strip()
        listbox.insert(END, f'No cron jobs found for user {username}.')

def remove_selected_cron_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return
    selected_index = selected_indices[0]
    selected_job = listbox.get(selected_index)
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        subprocess.run(['crontab', '-l'], text=True, stdout=temp_file)
        temp_file.seek(0)
        selected_job_bytes = selected_job.encode('utf-8')
        filtered_lines = [line for line in temp_file if selected_job_bytes not in line]
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            f.writelines(filtered_lines)
        subprocess.run(['crontab', temp_file.name], check=True)
        os.remove(temp_file.name)
        listbox.delete(selected_index)
    except subprocess.CalledProcessError:
        messagebox.showerror('Error', 'Failed to remove cron job')

def open_scheduled_tasks_window():
    window = Toplevel()
    window.title('Scheduled Tasks')
    window.geometry('600x400')
    listbox = Listbox(window, width=80)
    listbox.pack(fill='both', expand=True)
    last_selected_index = [None]

    def populate_tasks():
        if listbox.curselection():
            last_selected_index[0] = listbox.curselection()[0]
        listbox.delete(0, END)
        tasks = list_tasks()
        for task in tasks:
            listbox.insert(END, task)
        if last_selected_index[0] is not None and last_selected_index[0] < listbox.size():
            listbox.selection_set(last_selected_index[0])
            listbox.see(last_selected_index[0])

    def delete_selected_task():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror('Error', 'No task selected')
            return
        selected_task_info = listbox.get(selection[0])
        print('THE SELECTED_TASK_INFO IS:\n', selected_task_info)
        task_name = selected_task_info.split('"')[1]
        try:
            delete_task(task_name)
            populate_tasks()
            last_selected_index[0] = None
        except Exception as e:
            messagebox.showerror('Error', f'Failed to delete task: {e}')

    def update_tasks():
        populate_tasks()
        window.after(5000, update_tasks)
    populate_tasks()
    update_tasks()
    delete_button = Button(window, text='Delete Selected', command=delete_selected_task)
    delete_button.pack()
    window.mainloop()

def open_new_at_task_window():
    new_task_window = Toplevel(root)
    new_task_window.title("New 'at' Task")
    new_task_window.geometry('400x150')
    Label(new_task_window, text='Task Name:').grid(row=0, column=0)
    task_name_entry = Entry(new_task_window)
    task_name_entry.grid(row=0, column=1)
    Label(new_task_window, text='Time (HH:MM):').grid(row=1, column=0)
    time_entry = Entry(new_task_window)
    time_entry.grid(row=1, column=1)
    Label(new_task_window, text='Program Path:').grid(row=2, column=0)
    program_path_entry = Entry(new_task_window)
    program_path_entry.grid(row=2, column=1)

    def create_at_job():
        task_name = task_name_entry.get()
        time = time_entry.get()
        program_path = program_path_entry.get()
        try:
            at_function(task_name, time, program_path)
            messagebox.showinfo('Scheduled', f"Task '{task_name}' scheduled at {time} to run {program_path}")
        except Exception as e:
            messagebox.showerror('Task Execution', f'Error creating at task:\n{str(e)}')
    Button(new_task_window, text="Create 'at' Job", command=create_at_job).grid(row=3, column=0)
    new_task_window.mainloop()

def open_new_crontab_task_window():
    new_cron_task_window = Toplevel(root)
    new_cron_task_window.title("New 'crontab' Task")
    new_cron_task_window.geometry('500x300')
    Label(new_cron_task_window, text='Name:').grid(row=0, column=0)
    name_entry = Entry(new_cron_task_window)
    name_entry.grid(row=0, column=1)
    Label(new_cron_task_window, text='Minute:').grid(row=1, column=0)
    minute_entry = Entry(new_cron_task_window)
    minute_entry.grid(row=1, column=1)
    Label(new_cron_task_window, text='Hour:').grid(row=2, column=0)
    hour_entry = Entry(new_cron_task_window)
    hour_entry.grid(row=2, column=1)
    Label(new_cron_task_window, text='Day (Month):').grid(row=3, column=0)
    day_month_entry = Entry(new_cron_task_window)
    day_month_entry.grid(row=3, column=1)
    Label(new_cron_task_window, text='Month:').grid(row=4, column=0)
    month_entry = Entry(new_cron_task_window)
    month_entry.grid(row=4, column=1)
    Label(new_cron_task_window, text='Day (Week):').grid(row=5, column=0)
    day_week_entry = Entry(new_cron_task_window)
    day_week_entry.grid(row=5, column=1)
    Label(new_cron_task_window, text='Script Path:').grid(row=6, column=0)
    script_path_entry = Entry(new_cron_task_window)
    script_path_entry.grid(row=6, column=1)

    def create_crontab_job():
        name = name_entry.get()
        minute = minute_entry.get()
        hour = hour_entry.get()
        day_month = day_month_entry.get()
        month = month_entry.get()
        day_week = day_week_entry.get()
        script_path = script_path_entry.get()
        if not all([name, minute, hour, day_month, month, day_week, script_path]):
            messagebox.showerror('Error', 'All fields must be filled.')
            return
        crontab_function(name, minute, hour, day_month, month, day_week, script_path)
        messagebox.showinfo('Scheduled', f'Crontab task scheduled to run script at {minute} {hour} {day_month} {month} {day_week}.')
    Button(new_cron_task_window, text="Create 'crontab' Job", command=create_crontab_job).grid(row=7, column=0, columnspan=2)
    new_cron_task_window.mainloop()