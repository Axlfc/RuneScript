# ScriptsEditor

## TODO:
- Copy / Paste not working
- Fix Delete & Duplicate
- Fix freeze in delay execution (timeout does not affect operability)
- Save as New only create the file but the content of the document has to be pasted to new document and this document, opened.
- Undo / Redo
- When saving the file file is created but not been written and opened.

- Open file using the path variable from starting point so when opening file that is the root directory in the dialog.
- Save as new file, asks if the user wants to discard its changes and loads the new file and updates the title.
- We need to be able to track the editions real time if the file is externally edited. Update every 5 seconds.
- Add Functional Program Keyboard Shortcuts

- Show file line numbers in the left
- Find / Replace
- Adding fonts
- Format bar


## TODO:
Show / Export markdown document

```shell
/home/axl/Documents/git/ScriptsEditor/venv/bin/python3 -m pip install -r /home/axl/Documents/git/ScriptsEditor/requirements.txt
/home/axl/Documents/git/ScriptsEditor/venv/bin/python3 /home/axl/Documents/git/ScriptsEditor/ScriptsEditor.py

```


- Text Editor GUI Setup:
The code creates a text editor window using the Tkinter library. This window includes a text area where you can write and edit scripts. It also has a menu bar with options for file operations (New, Open, Save, etc.) and edit operations (Cut, Copy, Paste, etc.).

- File Operations:
The text editor supports typical file operations like New, Open, Save, and Save As. You can create a new script, open an existing script file, and save or save as the script you've written.

- Edit Operations:
The edit operations include Cut, Copy, Paste, Undo, and Redo. These are common actions you can perform on the text content within the editor.

- Text Appearance:
The code includes options to modify the appearance of the selected text. You can make the selected text bold, italic, underline, or overstrike it. Additionally, you can change the font color of the selected text.

- Search and Highlight:
The code provides a basic text search functionality. You can search for a specific word or phrase within the text content, and the matches will be highlighted.

- Script Execution:
The code allows you to execute scripts by running them in a subprocess. There are options to provide arguments to the script and capture its standard output and standard error.

- Script Scheduling:
The GUI provides options to schedule script execution at a specific time using the at command or based on a cron-like schedule using the crontab command.

- Viewing Standard Output and Error:
After running a script, you can view its standard output and standard error in separate windows.

- About and Help:
There's an "About" option that displays information about the application.

- AT Jobs and Cron Jobs Lists:
The GUI allows you to view and manage scheduled AT jobs and cron jobs in separate windows. You can see the list of scheduled jobs and remove specific jobs from the list.
