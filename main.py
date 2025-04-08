from src.views.app_layers import create_app
from src.views.tk_utils import root


def main():
    create_app()
    root.mainloop()


if __name__ == "__main__":
    main()
