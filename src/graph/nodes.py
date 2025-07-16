import sys
import json
import time
import re

from .states import GameState
from src.config import PRIMARY_CHARACTER
from src.core.llms import llm
from src.core.tracing import get_tracing_manager
from src.prompts.prompt_generator import PromptGenerator
from src.game.game_constants import ScreenType

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
    game_state_json = state.game_state_json 
    prompt_generator = PromptGenerator(game_state_json)
    command, prompt = prompt_generator.get_command_or_prompt()
    
    if command:
        return {"final_command": command}
    elif prompt:
        try:
            print("--- Invoking LLM ---", file=sys.stderr, flush=True)
            tracing_manager = get_tracing_manager()
            if game_state_json and "game_state" in game_state_json:
                gs = game_state_json["game_state"]
                metadata = tracing_manager.create_run_metadata(
                    screen_type=gs.get("screen_type", "UNKNOWN"),
                    floor=gs.get("floor", 0),
                    act=gs.get("act", 0)
                )
                
                config = {"metadata": metadata}
                response = llm.invoke([("human", prompt)], config=config)
            else:
                response = llm.invoke([("human", prompt)])

            print("--- LLM invocation complete ---", file=sys.stderr, flush=True)
            return {
                "thinking_process": response.think,
                "final_command": response.command
            }
        except Exception as e:
            print(f"Error invoking LLM or parsing response: {e}", file=sys.stderr)
            return {"final_command": "state"}
    else:
        return {"final_command": "state"}

def execute_command(state: GameState):
    final_command = state.final_command
    if final_command:
        print(final_command, flush=True)
        time.sleep(0.1)
    return {}

def request_state_update(state: GameState):
    print("state", flush=True)
    time.sleep(0.1)
    return {}

def validate_command(state: GameState):
    final_command = (state.final_command or "").strip()
    game_state_json = state.game_state_json or {}
    game_state = game_state_json.get("game_state", {})
    
    validation_result = {
        "is_valid": False,
        "command": final_command,
        "errors": [],
        "warnings": [],
        "validated_command": final_command
    }
    
    if not final_command:
        validation_result["errors"].append("Command is empty")
        return {"validation_result": validation_result}
    
    if len(final_command) > 1000:
        validation_result["errors"].append("Command too long")
        return {"validation_result": validation_result}
    
    if not re.match(r'^[a-zA-Z0-9\s\-_,.:;!?()[\]{}]+$', final_command):
        validation_result["warnings"].append("Command contains special characters, may be invalid")
    
    try:
        prompt_generator = PromptGenerator(game_state_json)
        current_screen_type = prompt_generator.get_screen_type()
    except Exception as e:
        validation_result["errors"].append(f"Cannot get screen type: {e}")
        return {"validation_result": validation_result}
    
    available_commands = game_state_json.get("available_commands", [])
    if available_commands:
        if final_command in available_commands:
            validation_result["is_valid"] = True
        else:
            partial_match = False
            for cmd in available_commands:
                if final_command.startswith(cmd):
                    partial_match = True
                    validation_result["warnings"].append(f"Command may match: {cmd}")
                    break
            
            if not partial_match:
                validation_result["errors"].append(f"Command not in available commands: {available_commands}")
    
    tokens = final_command.split()
    if not tokens:
        validation_result["errors"].append("Invalid command format")
        return {"validation_result": validation_result}
    
    command_word = tokens[0].lower()
    
    valid_commands = {
        "play", "end", "choose", "potion", "confirm", "proceed", 
        "skip", "cancel", "return", "leave", "start", "state", 
        "key", "click", "wait"
    }
    
    if command_word not in valid_commands:
        validation_result["errors"].append(f"Unknown command: {command_word}")
        return {"validation_result": validation_result}
    
    if command_word == "play":
        if len(tokens) < 2:
            validation_result["errors"].append("play command missing card index")
        elif not tokens[1].isdigit():
            validation_result["errors"].append("play command card index must be a number")
        elif len(tokens) == 3 and not tokens[2].isdigit():
            validation_result["errors"].append("play command target index must be a number")
        elif len(tokens) > 3:
            validation_result["errors"].append("play command has too many arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word == "end":
        if len(tokens) > 1:
            validation_result["errors"].append("end command does not need arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word == "choose":
        if len(tokens) < 2:
            validation_result["errors"].append("choose command missing choice parameter")
        else:
            choice_arg = " ".join(tokens[1:])
            if choice_arg.isdigit() or any(choice_arg.lower() in cmd.lower() for cmd in available_commands):
                validation_result["is_valid"] = True
            else:
                validation_result["warnings"].append(f"choose command parameter may be invalid: {choice_arg}")
                validation_result["is_valid"] = True
    
    elif command_word == "potion":
        if len(tokens) < 3:
            validation_result["errors"].append("potion command format: potion use/discard [index] [target]")
        elif tokens[1].lower() not in ["use", "discard"]:
            validation_result["errors"].append("potion command second parameter must be 'use' or 'discard'")
        elif not tokens[2].isdigit():
            validation_result["errors"].append("potion command potion index must be a number")
        elif len(tokens) == 4 and not tokens[3].isdigit():
            validation_result["errors"].append("potion command target index must be a number")
        elif len(tokens) > 4:
            validation_result["errors"].append("potion command has too many arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word in ["confirm", "proceed"]:
        if len(tokens) > 1:
            validation_result["errors"].append(f"{command_word} command does not need arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word in ["skip", "cancel", "return", "leave"]:
        if len(tokens) > 1:
            validation_result["errors"].append(f"{command_word} command does not need arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word == "start":
        if len(tokens) < 2:
            validation_result["errors"].append("start command missing character parameter")
        elif tokens[1].lower() not in ["ironclad", "the_silent", "silent", "defect", "watcher"]:
            validation_result["errors"].append("start command character parameter invalid")
        elif len(tokens) >= 3 and not tokens[2].isdigit():
            validation_result["errors"].append("start command ascension level must be a number")
        elif len(tokens) >= 4 and not re.match(r'^[A-Z0-9]+$', tokens[3].upper()):
            validation_result["errors"].append("start command seed format invalid")
        elif len(tokens) > 4:
            validation_result["errors"].append("start command has too many arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word == "state":
        if len(tokens) > 1:
            validation_result["errors"].append("state command does not need arguments")
        else:
            validation_result["is_valid"] = True
    
    elif command_word == "key":
        if len(tokens) < 2:
            validation_result["errors"].append("key command missing key parameter")
        else:
            valid_keys = {
                "confirm", "cancel", "map", "deck", "draw_pile", "discard_pile", 
                "exhaust_pile", "end_turn", "up", "down", "left", "right", 
                "drop_card", "card_1", "card_2", "card_3", "card_4", "card_5",
                "card_6", "card_7", "card_8", "card_9", "card_10"
            }
            if tokens[1].upper() not in [k.upper() for k in valid_keys]:
                validation_result["errors"].append(f"key command key invalid: {tokens[1]}")
            elif len(tokens) >= 3 and not tokens[2].isdigit():
                validation_result["errors"].append("key command timeout must be a number")
            elif len(tokens) > 3:
                validation_result["errors"].append("key command has too many arguments")
            else:
                validation_result["is_valid"] = True
    
    elif command_word == "click":
        if len(tokens) < 4:
            validation_result["errors"].append("click command format: click left/right [x] [y] [timeout]")
        elif tokens[1].upper() not in ["LEFT", "RIGHT"]:
            validation_result["errors"].append("click command button parameter must be 'left' or 'right'")
        else:
            try:
                float(tokens[2])
                float(tokens[3])
                if len(tokens) >= 5 and not tokens[4].isdigit():
                    validation_result["errors"].append("click command timeout must be a number")
                elif len(tokens) > 5:
                    validation_result["errors"].append("click command has too many arguments")
                else:
                    validation_result["is_valid"] = True
            except ValueError:
                validation_result["errors"].append("click command coordinates must be numbers")
    
    elif command_word == "wait":
        if len(tokens) < 2:
            validation_result["errors"].append("wait command missing time parameter")
        elif not tokens[1].isdigit():
            validation_result["errors"].append("wait command time must be a number")
        elif len(tokens) > 2:
            validation_result["errors"].append("wait command has too many arguments")
        else:
            validation_result["is_valid"] = True
    
    # If there are errors, command is invalid
    if validation_result["errors"]:
        validation_result["is_valid"] = False
    # If no errors and not yet marked as valid, it might be valid
    elif not validation_result["is_valid"]:
        validation_result["warnings"].append("Command format unknown, but may be valid")
        validation_result["is_valid"] = True
    
    validation_result["screen_type"] = current_screen_type.value if current_screen_type else "UNKNOWN"
    
    return {"validation_result": validation_result}

def handle_validation_failure(state: GameState):
    validation_result = state.validation_result or {}
    final_command = state.final_command or ""
    
    if not validation_result:
        print(f"Error: No validation result found for command: {final_command}", file=sys.stderr)
        return {"fallback_command": "state"}
    
    errors = validation_result.get("errors", [])
    warnings = validation_result.get("warnings", [])
    screen_type = validation_result.get("screen_type", "UNKNOWN")
    
    print(f"Command validation failed: {final_command}", file=sys.stderr)
    
    if errors:
        print(f"Errors: {'; '.join(errors)}", file=sys.stderr)
    
    if warnings:
        print(f"Warnings: {'; '.join(warnings)}", file=sys.stderr)
    
    fallback_command = generate_fallback_command(screen_type, final_command, errors)
    
    print(f"Using fallback command: {fallback_command}", file=sys.stderr)
    
    return {"fallback_command": fallback_command}

def generate_fallback_command(screen_type: str, original_command: str, errors: list) -> str:
    safe_commands = {
        "MAP": "state",
        "CARD_REWARD": "skip", 
        "COMBAT_REWARD": "proceed",
        "SHOP_SCREEN": "leave",
        "REST": "proceed",
        "EVENT": "state",
        "GRID": "cancel",
        "HAND_SELECT": "confirm",
        "BOSS_REWARD": "skip",
        "GAME_OVER": "proceed",
        "COMPLETE": "proceed",
        "CHEST": "proceed",
        "SHOP_ROOM": "proceed",
        "COMBAT": "state",
        "NONE": "state"
    }
    
    if "missing" in " ".join(errors).lower() or "format" in " ".join(errors).lower():
        return "state"
    
    if "unknown command" in " ".join(errors).lower():
        return "state" 
    
    return safe_commands.get(screen_type, "state")

def execute_fallback_command(state: GameState):
    fallback_command = state.fallback_command or "state"
    print(f"Executing fallback command: {fallback_command}", flush=True)
    time.sleep(0.1)
    return {}
