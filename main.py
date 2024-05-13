from src.views.app_layers import create_app
from src.views.tk_utils import root


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

    def run_app():
        # TODO: LOADS FROM USER CONFIG IF THERE IS ONE
        create_app()
        root.mainloop()

    run_app()


if __name__ == '__main__':
    main()
