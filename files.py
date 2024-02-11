from app_layers import (
    create_directory_line,
    create_open_script_line,
    create_content_file_window,
    create_arguments_lines,
    create_immediately_run_line,
    create_execute_in_line,
    create_execute_one_time_with_format,
    create_program_daily_with_format
)
from menu_functions import create_menu
from tk_utils import root


def main():
    """
        Initializes and runs the main application window.

        This function sets up the main window for the Scripts Editor application. It defines window properties,
        initializes the user interface components, and enters the main event loop to start the application.

        Parameters:
        None

        Returns:
        None
    """

    width = 485
    height = int(width * (1 + 5 ** 0.5) / 2)

    # root.title("Untitled* - Script Editor")
    root.title("Scripts Editor")
    root.geometry(f"{width}x{height}")

    # setting resizable window
    root.resizable(True, True)
    root.minsize(width, height)  # minimimum size possible

    is_modified = False

    create_menu()

    create_directory_line()

    create_open_script_line()

    create_content_file_window()

    # Open first text file if exists when changing directory
    # open_first_text_file(os.getcwd())

    create_arguments_lines()

    create_immediately_run_line()

    create_execute_in_line()



    create_execute_one_time_with_format()

    create_program_daily_with_format()

    root.grid_rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)

    root.mainloop()



if __name__ == '__main__':
    main()
