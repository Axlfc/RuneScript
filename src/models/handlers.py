from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.messages import BaseMessage
from langchain.schema import LLMResult
from typing import Dict, List, Any


class MyCustomHandler(BaseCallbackHandler):
    """ ""\"
    ""\"
    MyCustomHandler

    Description of the class.
    ""\"
    ""\" """

    def __init__(self, queue) -> None:
        """ ""\"
        ""\"
            __init__

                Args:
                    self (Any): Description of self.
                    queue (Any): Description of queue.

                Returns:
                    Any: Description of return value.
            ""\"
        ""\" """
        super().__init__()
        self._queue = queue
        self._stop_signal = None
        print("Custom handler Initialized")

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """ ""\"
        ""\"
            on_llm_new_token

                Args:
                    self (Any): Description of self.
                    token (Any): Description of token.

                Returns:
                    Any: Description of return value.
            ""\"
        ""\" """
        self._queue.put(token)

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """ ""\"
        ""\"
            Run when LLM starts running.
            ""\"
        ""\" """
        print("generation started")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """ ""\"
        ""\"
            Run when LLM ends running.
            ""\"
        ""\" """
        print("\n\ngeneration concluded")
        self._queue.put(self._stop_signal)
