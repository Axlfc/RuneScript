import queue

class MessageQueue:
    def __init__(self):
        """
        Initialize a thread-safe queue for communication.
        """
        self.queue = queue.Queue()

    def put(self, message):
        """
        Add a message to the queue.

        Args:
            message (dict): The message to add to the queue.
        """
        try:
            self.queue.put(message, block=False)
        except queue.Full:
            print("Queue is full. Message could not be added.")

    def get(self):
        """
        Retrieve a message from the queue.

        Returns:
            dict: The next message in the queue.
        """
        try:
            return self.queue.get(block=False)
        except queue.Empty:
            return None

    def get_nowait(self):
        """
        Retrieve a message from the queue without waiting.

        Returns:
            dict: The next message in the queue.
        """
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

    def clear(self):
        """
        Clear all messages in the queue.
        """
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def size(self):
        """
        Get the number of items currently in the queue.

        Returns:
            int: The number of items in the queue.
        """
        return self.queue.qsize()

    def is_empty(self):
        """
        Check if the queue is empty.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        return self.queue.empty()
