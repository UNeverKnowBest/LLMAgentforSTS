from pydantic import BaseModel
from typing import Dict, Optional, Any

class GameState(BaseModel):
    game_state_json: Optional[Dict[str, Any]] = None
    thinking_process: Optional[str] = None
    final_command: Optional[str] = None
    command_success: Optional[bool] = None
    error_message: Optional[str] = None
    is_game_over: Optional[bool] = None
    state_valid: Optional[bool] = None