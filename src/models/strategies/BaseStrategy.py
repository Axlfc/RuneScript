from abc import ABC, abstractmethod


class CommunicationStrategy(ABC):
    @abstractmethod
    def send_message(self, thread_id, content, role):
        pass

    @abstractmethod
    def run_assistant(self, thread_id, assistant_id):
        pass

    @abstractmethod
    def get_responses(self, thread_id):
        pass
