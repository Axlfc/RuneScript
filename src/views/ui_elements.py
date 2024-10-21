from tkinter import Toplevel, Label, Canvas, Frame, Scrollbar


class Tooltip:
    

    def __init__(self, widget, text):
        
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event):
        
        if not self.tooltip:
            self.show_tooltip(event)

    def leave(self, event):
        
        self.destroy_tooltip()

    def motion(self, event):
        
        if self.tooltip:
            self.adjust_tooltip_position(event.x_root, event.y_root)

    def adjust_tooltip_position(self, x, y):
        
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
        
        self.tooltip = Toplevel()
        self.tooltip.wm_geometry("+0+0")
        self.tooltip.wm_overrideredirect(True)
        label = Label(
            self.tooltip,
            text=self.text,
            background="
            relief="solid",
            borderwidth=1,
        )
        label.pack()
        self.adjust_tooltip_position(event.x_root, event.y_root)

    def destroy_tooltip(self):
        
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class LineNumberCanvas(Canvas):
    

    def __init__(self, text_widget, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind("<KeyPress>", self.on_text_change)
        self.text_widget.bind("<MouseWheel>", self.on_text_change)
        self.text_widget.bind("<KeyRelease>", self.on_text_change)
        self.text_widget.bind("<Button-1>", self.on_text_change)
        self.text_widget.bind("<<Modified>>", self.on_text_change)
        self.text_widget.bind("<Configure>", self.on_text_change)

    def on_text_change(self, event=None):
        
        self.redraw()

    def redraw(self):
        
        self.delete("all")
        end_line_num = int(self.text_widget.index("end-1c").split(".")[0])
        max_line_num_length = len(str(end_line_num))
        width = max_line_num_length * 8
        self.config(width=width)
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line_num = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=line_num, fill="
            i = self.text_widget.index(f"{i}+1line")


class ScrollableFrame(Frame):
    

    def __init__(self, parent, *args, **kwargs):
        
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
        
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_from_mousewheel(self, event):
        
        self.scrollable_frame.unbind_all("<MouseWheel>")
        self.scrollable_frame.unbind_all("<Button-4>")
        self.scrollable_frame.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        
        if event.num == 4 or event.delta > 0:
            self.scrollable_frame.master.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.scrollable_frame.master.yview_scroll(1, "units")
