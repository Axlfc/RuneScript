import pyttsx3
import queue
import threading


class TTSManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True  # Daemon thread will exit when the main program exits
        self.thread.start()

    def say(self, text):
        self.queue.put(text)

    def run(self):
        engine = pyttsx3.init()
        while True:
            text = self.queue.get()
            if text is None:
                break  # Exit the thread
            engine.say(text)
            engine.runAndWait()
