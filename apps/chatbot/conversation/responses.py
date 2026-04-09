from dataclasses import dataclass
from typing import Optional


@dataclass
class BotResponse:
    """
    Encapsulates an AI Agent's response.
    
    Attributes:
        text (str): The natural language response to be sent as a text message.
        interactive (dict, optional): The Meta Interactive Message payload (List or Buttons).
    """
    text: str
    interactive: Optional[dict] = None
