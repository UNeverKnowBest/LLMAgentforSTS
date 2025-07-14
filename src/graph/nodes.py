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
from game.commands import _get_simple_command

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
            return {"final_command" : "end"}
        game_state_data = json.loads(line)
        return {"game_state": game_state_data}
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading or parsing game state: {e}", file=sys.stderr)
    

def advice_on_command(state: GameState):
    game_infos = state["game_state"] 
    promopt_generator = PromptGenerator(game_infos)
    if command:
        return {"final_command" : command}
    else:
        response = llm.invoke(

        )


    