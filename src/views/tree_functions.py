import os
from src.controllers.file_operations import open_file
from src.controllers.parameters import write_config_parameter
from src.views.tk_utils import tree, menu


def update_tree(path):
    """ ""\"
    update_tree

    Args:
        path (Any): Description of path.

    Returns:
        None: Description of return value.
    ""\" """
    for item in tree.get_children():
        tree.delete(item)
    abspath = os.path.abspath(path)
    root_node = tree.insert("", "end", text=abspath, values=(abspath,), open=True)
    populate_tree(root_node, abspath)


def populate_tree(parent, path):
    """ ""\"
    populate_tree

    Args:
        parent (Any): Description of parent.
        path (Any): Description of path.

    Returns:
        None: Description of return value.
    ""\" """
    for item in os.listdir(path):
        if item != ".git" and item != ".idea":
            abspath = os.path.join(path, item)
            node = tree.insert(parent, "end", text=item, values=(abspath,), open=False)
            if os.path.isdir(abspath):
                tree.insert(node, "end")


def item_opened(event):
    """ ""\"
    item_opened

    Args:
        event (Any): Description of event.

    Returns:
        None: Description of return value.
    ""\" """
    item = tree.focus()
    abspath = tree.item(item, "values")[0]
    if os.path.isdir(abspath):
        tree.delete(*tree.get_children(item))
        populate_tree(item, abspath)


def on_item_select(event):
    """ ""\"
    on_item_select

    Args:
        event (Any): Description of event.

    Returns:
        None: Description of return value.
    ""\" """
    item = tree.focus()
    print(f"Selected: {tree.item(item, 'text')}")
    print(f"Full path: {tree.item(item, 'values')[0]}")

# TODO: Implement on right click over filesystem
def on_double_click(event):
    item = tree.identify("item", event.x, event.y)
    filepath = tree.item(item, "values")[0]
    if os.path.isfile(filepath):
        open_file(filepath)
        write_config_parameter("options.file_management.current_file_path", filepath)
