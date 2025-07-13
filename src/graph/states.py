from langgraph.graph import MessagesState
from typing import List, TypedDict, Annotated

class GameState(TypedDict):
    game_state_json: str
    think_process: str
    final_command: str
    feedback: str
    game_state: str