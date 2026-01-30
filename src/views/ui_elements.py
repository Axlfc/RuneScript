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
            borderwidth=1)
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
        # Set default background if not provided
        if "highlightthickness" not in kwargs:
            kwargs["highlightthickness"] = 0
        super().__init__(*args, **kwargs)

        # Store both for reference
        self.container = text_widget
        self._is_redrawing = False
        self.set_text_widget(text_widget)

        # Initial draw
        self.after(200, self.redraw)

    def set_text_widget(self, text_widget):
        self.container = text_widget
        self.text_widget = getattr(text_widget, "_textbox", text_widget)
        # Improve event bindings
        self.text_widget.bind("<<Modified>>", self._on_text_modified, add="+")
        self.text_widget.bind("<Configure>", self._on_configure, add="+")

    def get_font(self):
        """Try to get font from the text widget or container"""
        try:
            if hasattr(self.container, "cget"):
                return self.container.cget("font")
            return self.text_widget.cget("font")
        except:
            return ("Consolas", 12)

    def _on_text_modified(self, event=None):
        self.redraw()

    def _on_configure(self, event=None):
        # Delayed redraw on configure to prevent excessive updates
        self.after(50, self.redraw)

    def redraw(self):
        """Redraw line numbers with improved performance and alignment"""
        # Prevent recursive calls
        if self._is_redrawing:
            return

        try:
            if not self.winfo_exists() or not self.text_widget.winfo_exists():
                return
        except Exception:
            return

        try:
            self._is_redrawing = True
            self.delete("all")

            # Sync background color
            try:
                import customtkinter
                bg_color = self.container.cget("fg_color")
                if isinstance(bg_color, (list, tuple)) or bg_color == "transparent":
                    # Get color from theme
                    is_dark = customtkinter.get_appearance_mode().lower() == "dark"
                    bg_color = customtkinter.ThemeManager.theme["CTkTextbox"]["fg_color"][1 if is_dark else 0]
                self.configure(bg=bg_color)
            except:
                pass

            # Get vertical offset of internal textbox within the container
            y_offset = self.text_widget.winfo_y()

            # Get font
            font = self.get_font()

            # Get visible information
            first_index = self.text_widget.index("@0,0")
            first_line = int(first_index.split('.')[0])
            last_visible_index = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            last_visible_line = int(last_visible_index.split('.')[0])
            last_line = int(self.text_widget.index("end-1c").split('.')[0])

            # Draw visible line numbers
            for line_num in range(first_line, min(last_visible_line + 3, last_line + 1)):
                try:
                    dline = self.text_widget.dlineinfo(f"{line_num}.0")
                    if dline:  # Only draw if the line is actually visible
                        # y_pos is relative to the text widget.
                        # We add y_offset to align with the text widget's position in the frame.
                        y_pos = dline[1] + y_offset
                        # Use a color that contrasts with the background
                        try:
                            is_dark = customtkinter.get_appearance_mode().lower() == "dark"
                            text_color = customtkinter.ThemeManager.theme["CTkTextbox"]["text_color"][1 if is_dark else 0]
                        except:
                            text_color = "#CE9178" # Fallback to original color if theme fails

                        self.create_text(
                            self.winfo_width() - 5,
                            y_pos,
                            anchor="ne",
                            text=str(line_num),
                            fill=text_color,
                            font=font
                        )
                except Exception:
                    continue

            # Update canvas width if needed
            width_needed = max(len(str(last_line)) * 10, 35)
            if self.winfo_width() != width_needed:
                self.configure(width=width_needed)

        finally:
            # Reset the redrawing flag
            self._is_redrawing = False

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

