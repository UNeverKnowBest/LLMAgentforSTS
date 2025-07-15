import sys
import json
import time
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents import create_tool_calling_agent
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, SystemMessage

from .states import GameState
from src.config import PRIMARY_CHARACTER
from src.core.llms import llm, output_parser, LLMResponse
from src.prompts.prompt_generator import PromptGenerator
from src.game.commands import _get_simple_command

def initial_game(state: GameState):
    print("ready", flush=True)
    time.sleep(1)
    print(f"start {PRIMARY_CHARACTER}", flush=True)
    time.sleep(3)
    return {}

def read_state(state: GameState):
    try:
        line = sys.stdin.readline()
        game_state_json = json.loads(line)
        return {"game_state_json": game_state_json}
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading or parsing game state: {e}", file=sys.stderr)
        return {}

def advice_on_command(state: GameState):
    game_state_json = state["game_state_json"] 
    prompt_generator = PromptGenerator(game_state_json)
    command, prompt = prompt_generator.get_command_or_prompt()
    
    if command:
        return {"final_command": command}
    elif prompt:
        try:
            prompt_with_format = f"{prompt}\n\n{output_parser.get_format_instructions()}"
            response = llm.invoke(prompt_with_format)
            parsed_response = output_parser.parse(response.content)
            return {
                "thinking_process": parsed_response.think,
                "final_command": parsed_response.command
            }
        except Exception as e:
            print(f"Error invoking LLM or parsing response: {e}", file=sys.stderr)
            return {"final_command": "state"}
    else:
        return {"final_command": "state"}

def execute_command(state: GameState):
    final_command = state.get("final_command")
    if final_command:
        print(final_command, flush=True)
        time.sleep(0.1)
    return {}

def validate_command_result(state: GameState):
    game_state_json = state.get("game_state_json", {})
    if "error" in game_state_json:
        return {
            "command_success": False,
            "error_message": game_state_json.get("error", "Unknown error")
        }
    return {"command_success": True}

def handle_command_error(state: GameState):
    error_message = state.get("error_message", "Unknown error")
    print(f"Command error: {error_message}", file=sys.stderr)
    return {"final_command": "state"}

def check_game_over(state: GameState):
    game_state_json = state.get("game_state_json", {})
    game_state = game_state_json.get("game_state", {})
    
    is_game_over = (
        game_state.get("screen_type") == "GAME_OVER" or
        game_state.get("screen_type") == "COMPLETE" or
        not game_state_json.get("ready_for_command", True)
    )
    
    return {"is_game_over": is_game_over}

def end_game(state: GameState):
    print("Game ended", flush=True)
    return {"final_command": "end"}

def wait_for_state_change(state: GameState):
    time.sleep(1)
    return {}

def debug_state(state: GameState):
    game_state_json = state.get("game_state_json", {})
    print(f"Debug - Current state: {json.dumps(game_state_json, indent=2)}", file=sys.stderr)
    return {}

def validate_state_format(state: GameState):
    game_state_json = state.get("game_state_json", {})
    
    required_fields = ["ready_for_command", "in_game"]
    is_valid = all(field in game_state_json for field in required_fields)
    
    if not is_valid:
        print(f"Invalid state format: missing required fields", file=sys.stderr)
        return {"state_valid": False}
    
    return {"state_valid": True}

def request_state_update(state: GameState):
    print("state", flush=True)
    time.sleep(0.1)
    return {}



    