import os
from src.views.tk_utils import tree


# Function to update the tree view with directory contents
def update_tree(path):
    for item in tree.get_children():
        tree.delete(item)
    abspath = os.path.abspath(path)
    root_node = tree.insert('', 'end', text=abspath, values=(abspath,), open=True)
    populate_tree(root_node, abspath)


# Recursive function to populate the tree view
def populate_tree(parent, path):
    for item in os.listdir(path):
        if item != '.git' and item != '.idea':
            abspath = os.path.join(path, item)
            node = tree.insert(parent, 'end', text=item, values=(abspath,), open=False)
            if os.path.isdir(abspath):
                tree.insert(node, 'end')


# Function to expand directory when double-clicked
def item_opened(event):
    item = tree.focus()
    abspath = tree.item(item, "values")[0]
    if os.path.isdir(abspath):
        tree.delete(*tree.get_children(item))
        populate_tree(item, abspath)


def on_item_select(event):
    item = tree.focus()
    print(f"Selected: {tree.item(item, 'text')}")
    print(f"Full path: {tree.item(item, 'values')[0]}")