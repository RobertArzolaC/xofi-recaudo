from dataclasses import dataclass
from typing import Optional


@dataclass
class BotResponse:
    """
    Encapsulates an AI Agent's response.
    
    Attributes:
        text (str): The natural language response to be sent as a text message.
        interactive (dict, optional): The Meta Interactive Message payload (List or Buttons).
        template (dict, optional): The Meta Template Message payload.
    """
    text: str
    interactive: Optional[dict] = None
    template: Optional[dict] = None
