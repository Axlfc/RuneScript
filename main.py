from src.views.app_layers import create_app
from src.views.tk_utils import root


def main():
    def run_app():
        create_app()
        root.mainloop()

    run_app()


if __name__ == "__main__":
    main()
