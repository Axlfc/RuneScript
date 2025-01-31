import os
import queue
import threading
import subprocess
from tkinter import Toplevel, Label, Entry, Button, END, messagebox, filedialog, NORMAL, DISABLED
from PIL import Image, ImageTk
import queue


class ImageGenerationWindow:
    def __init__(self):
        self.generation_window = Toplevel()
        self.generation_window.title("Image Generation")
        self.generation_window.geometry("480x580")

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI components."""
        Label(self.generation_window, text="Model Path:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.model_path_entry = Entry(self.generation_window, width=30)
        self.model_path_entry.grid(row=0, column=1, padx=10, pady=5)
        Button(self.generation_window, text="Browse", command=self.select_model_path).grid(row=0, column=2, padx=10,
                                                                                           pady=5)

        Label(self.generation_window, text="Prompt:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.prompt_entry = Entry(self.generation_window, width=30)
        self.prompt_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(self.generation_window, text="Output Path:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.output_path_entry = Entry(self.generation_window, width=30)
        self.output_path_entry.grid(row=2, column=1, padx=10, pady=5)
        Button(self.generation_window, text="Save As", command=self.select_output_path).grid(row=2, column=2, padx=10,
                                                                                             pady=5)

        self.generate_button = Button(self.generation_window, text="Generate Image", command=self.generate_image)
        self.generate_button.grid(row=3, column=0, columnspan=3, pady=10)

        self.status_label = Label(self.generation_window, text="Status: Waiting to start...", width=60, anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        Label(self.generation_window, text="Image Preview:").grid(row=5, column=0, columnspan=3, pady=10)
        self.image_label = Label(self.generation_window, text="No image generated yet", width=40, height=20,
                                 relief="sunken")
        self.image_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    def generate_image(self):
        """Starts the image generation in a separate thread."""
        model_path = self.model_path_entry.get()
        prompt = self.prompt_entry.get()
        output_path = self.output_path_entry.get()

        if not all([model_path, prompt, output_path]):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        self.status_label.config(text="Starting image generation...")
        self.generate_button.config(state=DISABLED)

        self.output_queue = queue.Queue()
        threading.Thread(
            target=self.run_image_generation,
            args=(model_path, prompt, output_path, self.output_queue),
            daemon=True
        ).start()

        self.generation_window.after(100, self.update_progress)

    def run_image_generation(self, model_path, prompt, output_path, output_queue):
        """Runs the image generation script."""
        try:
            process = subprocess.Popen(
                [
                    ".\\venv\\Scripts\\python.exe",
                    ".\\lib\\stableDiffusionCpp.py",
                    "--model_path", model_path,
                    "--prompt", prompt,
                    "--output_path", output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in process.stdout:
                output_queue.put(line.strip())
            process.wait()

            if process.returncode == 0:
                output_queue.put("Image generation completed successfully.")
                output_queue.put(f"LOAD_IMAGE:{output_path}")
            else:
                output_queue.put(f"Image generation failed: {process.stderr.read()}")
        except subprocess.CalledProcessError as e:
            output_queue.put(f"Image generation failed: {e}")

        output_queue.put("DONE")

    def update_progress(self):
        """Updates the status label with progress messages from the queue."""
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()

                if line.startswith("LOAD_IMAGE:"):
                    self.load_image(line.split(":", 1)[1])
                else:
                    self.status_label.config(text=f"Progress: {line}")

                if "Image generation completed" in line:
                    self.status_label.config(text=line)
                    self.generate_button.config(state=NORMAL)
                    break

        except queue.Empty:
            pass
        finally:
            if "Image generation completed" not in self.status_label.cget("text"):
                self.generation_window.after(100, self.update_progress)

    def load_image(self, image_path):
        """Loads the generated image and displays it."""
        try:
            img = Image.open(image_path)
            img = img.resize((250, 250), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk
            self.status_label.config(text=f"Image generated at {image_path}")
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load image: {e}")

    def select_model_path(self):
        """Opens file dialog to select model path."""
        path = filedialog.askopenfilename(filetypes=[("Checkpoint Files", "*.ckpt")])
        self.model_path_entry.delete(0, END)
        self.model_path_entry.insert(0, path)

    def select_output_path(self):
        """Opens file dialog to select output path."""
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        self.output_path_entry.delete(0, END)
        self.output_path_entry.insert(0, path)

