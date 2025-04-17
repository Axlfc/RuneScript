from tkinter import Toplevel, Label, Canvas, Frame, Scrollbar


class Tooltip:
    """ ""\"
    Tooltip

    Description of the class.
    ""\" """

    def __init__(self, widget, text):
        """ ""\"
        __init__

            Args:
                self (Any): Description of self.
                widget (Any): Description of widget.
                text (Any): Description of text.

            Returns:
                None: Description of return value.
        ""\" """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event):
        """ ""\"
        enter

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        if not self.tooltip:
            self.show_tooltip(event)

    def leave(self, event):
        """ ""\"
        leave

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        self.destroy_tooltip()

    def motion(self, event):
        """ ""\"
        motion

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        if self.tooltip:
            self.adjust_tooltip_position(event.x_root, event.y_root)

    def adjust_tooltip_position(self, x, y):
        """ ""\"
        adjust_tooltip_position

            Args:
                self (Any): Description of self.
                x (Any): Description of x.
                y (Any): Description of y.

            Returns:
                None: Description of return value.
        ""\" """
        screen_width = self.tooltip.winfo_screenwidth()
        screen_height = self.tooltip.winfo_screenheight()
        tooltip_width = 200
        tooltip_height = 50
        offset_x = 14
        offset_y = 14
        x = min(x + offset_x, screen_width - tooltip_width)
        y = min(y + offset_y, screen_height - tooltip_height)
        self.tooltip.wm_geometry(f"+{x}+{y}")

    def show_tooltip(self, event):
        """ ""\"
        show_tooltip

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        self.tooltip = Toplevel()
        self.tooltip.wm_geometry("+0+0")
        self.tooltip.wm_overrideredirect(True)
        label = Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
        )
        label.pack()
        self.adjust_tooltip_position(event.x_root, event.y_root)

    def destroy_tooltip(self):
        """ ""\"
        destroy_tooltip

            Args:
                self (Any): Description of self.

            Returns:
                None: Description of return value.
        ""\" """
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class LineNumberCanvas(Canvas):
    def __init__(self, text_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_widget = text_widget

        # Reduce event bindings to just what's necessary
        self.text_widget.bind("<<Modified>>", self._on_text_modified)
        self.text_widget.bind("<Configure>", self._on_configure, add="+")

        # Initial draw
        self.after(100, self.redraw)

    def _on_text_modified(self, event=None):
        # Reset the modified flag
        self.text_widget.edit_modified(False)
        self.redraw()

    def _on_configure(self, event=None):
        # Delayed redraw on configure to prevent excessive updates
        self.after(50, self.redraw)

    def redraw(self):
        """Redraw line numbers with improved recursion protection"""
        # Use a class variable to prevent recursive calls
        if hasattr(self, '_is_redrawing') and self._is_redrawing:
            return  # Prevent recursive calls

        try:
            self._is_redrawing = True
            self.delete("all")

            # Get first visible index at the top of the viewport
            first_index = self.text_widget.index("@0,0")
            first_line = int(first_index.split('.')[0])

            # Get visible height of text widget
            text_height = self.text_widget.winfo_height()

            # Start with empty list of lines to draw
            lines_to_draw = []

            # Start from first visible line and go down until we're off screen
            current_line = first_line
            last_line = int(self.text_widget.index("end-1c").split('.')[0])

            # Limit the number of iterations to prevent infinite loops
            max_iterations = 1000
            iteration_count = 0

            while current_line <= last_line and iteration_count < max_iterations:
                iteration_count += 1

                # Get coordinates of current line
                try:
                    dline = self.text_widget.dlineinfo(f"{current_line}.0")
                except Exception:
                    # Handle any errors in dlineinfo
                    current_line += 1
                    continue

                if dline is None:
                    # We've reached a line that's not mapped in the display
                    current_line += 1
                    continue

                y_coord = dline[1]  # Y coordinate of this line

                # If we're past the visible area, stop
                if y_coord > text_height:
                    break

                # Add this line to our drawing list
                lines_to_draw.append((current_line, y_coord))
                current_line += 1

            # Draw the line numbers
            for line_num, y_pos in lines_to_draw:
                self.create_text(2, y_pos, anchor="nw", text=str(line_num), fill="#CE9178")

            # Update the canvas width if needed
            total_lines = last_line
            width_needed = max(len(str(total_lines)) * 8, 30)  # Minimum width of 30
            if self.winfo_width() != width_needed:
                self.config(width=width_needed)

        except Exception as e:
            print(f"Error in line number redraw: {e}")
        finally:
            # Reset the redrawing flag after a short delay
            self.after(10, self._reset_redraw_flag)

    def _reset_redraw_flag(self):
        """Safely reset the redrawing flag"""
        self._is_redrawing = False


class ScrollableFrame(Frame):
    """ ""\"
    ScrollableFrame

    Description of the class.
    ""\" """

    def __init__(self, parent, *args, **kwargs):
        """ ""\"
        __init__

            Args:
                self (Any): Description of self.
                parent (Any): Description of parent.

            Returns:
                None: Description of return value.
        ""\" """
        Frame.__init__(self, parent, *args, **kwargs)
        canvas = Canvas(self)
        scrollbar = Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.scrollable_frame.bind("<Enter>", self._bind_to_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_from_mousewheel)

    def _bind_to_mousewheel(self, event):
        """ ""\"
        _bind_to_mousewheel

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_from_mousewheel(self, event):
        """ ""\"
        _unbind_from_mousewheel

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        self.scrollable_frame.unbind_all("<MouseWheel>")
        self.scrollable_frame.unbind_all("<Button-4>")
        self.scrollable_frame.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """ ""\"
        _on_mousewheel

            Args:
                self (Any): Description of self.
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
        if event.num == 4 or event.delta > 0:
            self.scrollable_frame.master.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.scrollable_frame.master.yview_scroll(1, "units")
