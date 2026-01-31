import os
import queue
import threading
import subprocess
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from src.ui.themed_window import ThemedWindow


class GenerationWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.generation_window = self # self is the window
        self.title("Generation Window")
        self.geometry("600x700")

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI components."""
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Model Path
        ctk.CTkLabel(self.main_container, text="Model Path:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.model_path_entry = ctk.CTkEntry(self.main_container, width=250)
        self.model_path_entry.grid(row=0, column=1, padx=10, pady=5)
        ctk.CTkButton(self.main_container, text="Browse", width=80, command=self.select_model_path).grid(row=0, column=2, padx=10, pady=5)

        # Prompt
        ctk.CTkLabel(self.main_container, text="Prompt:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.prompt_entry = ctk.CTkEntry(self.main_container, width=250)
        self.prompt_entry.grid(row=1, column=1, padx=10, pady=5)

        # Output Path
        ctk.CTkLabel(self.main_container, text="Output Path:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.output_path_entry = ctk.CTkEntry(self.main_container, width=250)
        self.output_path_entry.grid(row=2, column=1, padx=10, pady=5)
        ctk.CTkButton(self.main_container, text="Save As", width=80, command=self.select_output_path).grid(row=2, column=2, padx=10, pady=5)

        # Media Type Selection
        ctk.CTkLabel(self.main_container, text="Media Type:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.media_type = ctk.CTkComboBox(self.main_container, values=["Text", "Image", "Audio", "Music", "Video", "3D Model", "Personalized Avatar"], width=250)
        self.media_type.grid(row=3, column=1, padx=10, pady=5)
        self.media_type.set("Text")

        # Generate Button
        self.generate_button = ctk.CTkButton(self.main_container, text="Generate", command=self.generate_media)
        self.generate_button.grid(row=4, column=0, columnspan=3, pady=20)

        # Status Label
        self.status_label = ctk.CTkLabel(self.main_container, text="Status: Waiting to start...", width=400, anchor="w")
        self.status_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

        # Preview Area
        ctk.CTkLabel(self.main_container, text="Preview:").grid(row=6, column=0, columnspan=3, pady=(10, 0))
        self.preview_area = ctk.CTkLabel(self.main_container, text="No preview available", width=400, height=200,
                                 fg_color=("gray85", "gray15"), corner_radius=6)
        self.preview_area.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

    def generate_media(self):
        """Starts the media generation in a separate thread."""
        model_path = self.model_path_entry.get()
        prompt = self.prompt_entry.get()
        output_path = self.output_path_entry.get()
        media_type = self.media_type.get()

        if not all([model_path, prompt, output_path, media_type]):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        self.status_label.configure(text="Starting media generation...")
        self.generate_button.configure(state=DISABLED)

        self.output_queue = queue.Queue()
        threading.Thread(
            target=self.run_media_generation,
            args=(model_path, prompt, output_path, media_type, self.output_queue),
            daemon=True
        ).start()

        self.generation_window.after(100, self.update_progress)

    def run_media_generation(self, model_path, prompt, output_path, media_type, output_queue):
        """Runs the media generation script."""
        try:
            process = subprocess.Popen(
                [
                    ".\\venv\\Scripts\\python.exe",
                    f".\\lib\\{media_type.lower()}Generation.py",
                    "--model_path", model_path,
                    "--prompt", prompt,
                    "--output_path", output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True)
            for line in process.stdout:
                output_queue.put(line.strip())
            process.wait()

            if process.returncode == 0:
                output_queue.put(f"{media_type} generation completed successfully.")
                output_queue.put(f"LOAD_{media_type.upper()}:{output_path}")
            else:
                output_queue.put(f"{media_type} generation failed: {process.stderr.read()}")
        except subprocess.CalledProcessError as e:
            output_queue.put(f"{media_type} generation failed: {e}")

        output_queue.put("DONE")

    def update_progress(self):
        """Updates the status label with progress messages from the queue."""
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()

                if line.startswith("LOAD_"):
                    media_type, path = line.split(":", 1)
                    media_type = media_type.split("_")[1]
                    self.load_media(media_type, path)
                else:
                    self.status_label.configure(text=f"Progress: {line}")

                if f"{self.media_type.get()} generation completed" in line:
                    self.status_label.configure(text=line)
                    self.generate_button.configure(state=NORMAL)
                    break

        except queue.Empty:
            pass
        finally:
            if f"{self.media_type.get()} generation completed" not in self.status_label.cget("text"):
                self.generation_window.after(100, self.update_progress)

    def load_media(self, media_type, media_path):
        """Loads the generated media and displays it."""
        try:
            if media_type == "Image":
                img = Image.open(media_path)
                img = img.resize((250, 250), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.preview_area.configure(image=img_tk)
                self.preview_area.image = img_tk
            elif media_type == "Audio":
                # Load and play audio
                pass
            elif media_type == "Video":
                # Load and play video
                pass
            elif media_type == "3D Model":
                # Load and display 3D model
                pass
            elif media_type == "Personalized Avatar":
                # Load and display avatar
                pass
            self.status_label.configure(text=f"{media_type} generated at {media_path}")
        except Exception as e:
            messagebox.showerror(f"{media_type} Error", f"Could not load {media_type.lower()}: {e}")

    def select_model_path(self):
        """Opens file dialog to select model path."""
        path = filedialog.askopenfilename(filetypes=[("Checkpoint Files", "*.ckpt"), ("GGUF Files", "*.gguf")])
        self.model_path_entry.delete(0, tk.END)
        self.model_path_entry.insert(0, path)

    def select_output_path(self):
        """Opens file dialog to select output path."""
        media_type = self.media_type.get()
        if media_type == "Image":
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        elif media_type == "Audio":
            path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
        elif media_type == "Video":
            path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Files", "*.mp4")])
        elif media_type == "3D Model":
            path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("OBJ Files", "*.obj")])
        elif media_type == "Personalized Avatar":
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        else:
            path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

        self.output_path_entry.delete(0, tk.END)
        self.output_path_entry.insert(0, path)

def open_generate_window(event=None):
    return GenerationWindow()
