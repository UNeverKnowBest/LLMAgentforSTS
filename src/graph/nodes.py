import sys
import json
import time
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents import create_tool_calling_agent
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, SystemMessage


from .states import GameState
from src.config import PRIMARY_CHARACTER
from core.llms import llm
from promopts.prompt_generator import PromptGenerator


def intial_game(state: GameState):
    print("ready", flush=True)
    time.sleep(1)
    print(f"start {PRIMARY_CHARACTER}", flush=True)
    time.sleep(3)
    return {}

def read_state(state: GameState):
    try:
        line = sys.stdin.readline()
        if not line:
            return {"final_command": "end"}
        game_state_data = json.loads(line)
        return {"game_state": game_state_data}
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading or parsing game state: {e}", file=sys.stderr)
    

def advice_on_command(state: GameState):
    game_state = state["game_state"] 
    if game_state['ready_for_command']:
        screen_type = game_state["game_state"]["screen_type"]
        if screen_type == "CHEST":   
            return {"final_command" : "choose open"}
        elif screen_type == "SHOP_ROOM":
            return {"final_command" : "choose shop"}
        elif screen_type == "COMPLETE":
            return {"final_command" : "proceed"}
        elif screen_type == "GAME_OVER":
            return {"final_command" : "end"}
        elif screen_type == "EVENT":
        
        elif screen_type == "REST":
        
        elif screen_type == "CARD_REWARD":
        
        elif screen_type == "COMBAT_REWARD":
        
        elif screen_type == "BOSS_REWARD":

        elif screen_type == "SHOP_SCREEN":
        
        elif screen_type == "GRID":
        
        elif screen_type == "HAND_SELECT":
        
        elif screen_type == "NONE":

        if game_state["game_state"]["room_phase"] == "COMBAT":
            response = llm.invoke(
                [
                    SystemMessage(
                        content=system_prompt
                    ),
                    HumanMessage(content=game_state_prompt)
                ]
            )
        


    