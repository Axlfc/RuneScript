import requests
from src.models.strategies.BaseStrategy import CommunicationStrategy


class LocalServerStrategy(CommunicationStrategy):
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def send_message(self, thread_id, content, role):
        response = requests.post(
            f"{self.base_url}/send_message",
            json={"thread_id": thread_id, "content": content, "role": role},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json().get("content")

    def run_assistant(self, thread_id, assistant_id):
        pass

    def get_responses(self, thread_id):
        pass
