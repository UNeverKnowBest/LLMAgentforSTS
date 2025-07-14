from langgraph.graph import MessagesState
from pydantic import BaseModel

class GameState(BaseModel):
    game_state_json: str
    think_process: str
    final_command: str
    feedback: str
    game_state: str