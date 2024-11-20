import openai
from src.models.strategies.BaseStrategy import CommunicationStrategy


class OpenAIStrategy(CommunicationStrategy):
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key

    def send_message(self, thread_id, content, role):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": role, "content": content}
            ]
        )
        return response.choices[0].message['content']

    def run_assistant(self, thread_id, assistant_id):
        pass

    def get_responses(self, thread_id):
        pass
