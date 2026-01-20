class EventBus:
    """
    Simple event bus implementation for decoupling components.
    Allows components to publish events and subscribe to them.
    """

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_name, callback):
        """Subscribe to an event with a callback function"""
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        """Unsubscribe from an event"""
        if event_name in self.subscribers and callback in self.subscribers[event_name]:
            self.subscribers[event_name].remove(callback)

    def publish(self, event_name, data=None):
        """Publish an event with optional data"""
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(data) if data is not None else callback()
