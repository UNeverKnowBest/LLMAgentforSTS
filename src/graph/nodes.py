import sys
import json
import re
import time

from .states import GameState
from src.core.llms import llm
from src.core.tracing import get_tracing_manager
from src.prompts.prompt_generator import PromptGenerator
from src.game.game_constants import ScreenType
from src.config import PRIMARY_CHARACTER

def initial_game(state: GameState):
    print("ready", flush=True)
    time.sleep(1)
    print(f"start {PRIMARY_CHARACTER}")
    return {}

def read_state(state: GameState):
    try:
        line = sys.stdin.readline()
        
        if not line:
            print("EOF received from stdin, terminating", file=sys.stderr)
            return {"game_state_json": None}
        
        line = line.strip()
        if not line:
            print("Empty line received, skipping", file=sys.stderr)
            return {"game_state_json": {}}
        
        game_state_json = json.loads(line)
        return {"game_state_json": game_state_json}
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}", file=sys.stderr)
        print(f"Raw input was: {line[:100]}...", file=sys.stderr)
        return {"game_state_json": {}}
    except Exception as e:
        print(f"Unexpected error reading state: {e}", file=sys.stderr)
        return {"game_state_json": None}

def advice_on_command(state: GameState):
    game_state_json = state.game_state_json 
    
    if not game_state_json:
        print("No game state received, sending state command", file=sys.stderr)
        return {"final_command": "state"}
    
    try:
        prompt_generator = PromptGenerator(game_state_json)
        command, prompt = prompt_generator.get_command_or_prompt()
        
        if command:
            print(f"Using simple command: {command}", file=sys.stderr)
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
                
                final_command = response.command.strip() if response.command else "state"
                
                return {
                    "thinking_process": response.think,
                    "final_command": final_command
                }
                
            except Exception as e:
                print(f"LLM invocation error: {e}", file=sys.stderr)
                return {"final_command": "state"}
        else:
            print("No command or prompt generated, using state", file=sys.stderr)
            return {"final_command": "state"}
            
    except Exception as e:
        print(f"Error in advice_on_command: {e}", file=sys.stderr)
        return {"final_command": "state"}

def execute_command(state: GameState):
    final_command = state.final_command
    
    if not final_command:
        print("state", flush=True)
        print("Warning: Empty command, sent 'state' instead", file=sys.stderr)

    else:
        clean_command = final_command.strip().replace('\n', ' ').replace('\r', ' ')
        print(clean_command, flush=True)
        print(f"Sent command: {clean_command}", file=sys.stderr)
    
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
    
    try:
        prompt_generator = PromptGenerator(game_state_json)
        current_screen_type = prompt_generator.get_screen_type()
    except Exception as e:
        validation_result["errors"].append(f"Cannot get screen type: {e}")
        return {"validation_result": validation_result}
    
    available_commands = game_state_json.get("available_commands", [])
    if available_commands:
        command_base = final_command.split()[0].lower()
        if any(cmd.lower() == command_base for cmd in available_commands):
            validation_result["warnings"].append(f"Command base '{command_base}' found in available commands")
        else:
            validation_result["warnings"].append(f"Command base '{command_base}' not explicitly in available commands: {available_commands}")
    
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
        else:
            card_index = int(tokens[1])
            if card_index == 0:
                validation_result["warnings"].append("Card index 0 will be treated as 10")
            elif card_index < 0:
                validation_result["errors"].append("play command card index must be non-negative")
            
            if len(tokens) == 3:
                if not tokens[2].isdigit():
                    validation_result["errors"].append("play command target index must be a number")
                elif int(tokens[2]) < 0:
                    validation_result["errors"].append("play command target index must be non-negative")
            elif len(tokens) > 3:
                validation_result["errors"].append("play command has too many arguments")
        
        if not validation_result["errors"]:
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
            validation_result["is_valid"] = True
    
    elif command_word == "potion":
        if len(tokens) < 3:
            validation_result["errors"].append("potion command format: potion use/discard [index] [target]")
        elif tokens[1].lower() not in ["use", "discard"]:
            validation_result["errors"].append("potion command second parameter must be 'use' or 'discard'")
        elif not tokens[2].isdigit():
            validation_result["errors"].append("potion command potion index must be a number")
        elif int(tokens[2]) < 0:
            validation_result["errors"].append("potion command potion index must be non-negative")
        elif len(tokens) == 4 and not tokens[3].isdigit():
            validation_result["errors"].append("potion command target index must be a number")
        elif len(tokens) == 4 and int(tokens[3]) < 0:
            validation_result["errors"].append("potion command target index must be non-negative")
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
        else:
            character = tokens[1].lower()
            valid_characters = [
                "ironclad", "the_silent", "silent", "defect", "watcher",
                "the_ironclad", "the_defect", "the_watcher"
            ]
            
            if character not in valid_characters:
                validation_result["warnings"].append(f"Character '{tokens[1]}' may not be recognized by CommunicationMod")
            
            if len(tokens) >= 3:
                try:
                    ascension_level = int(tokens[2])
                    if ascension_level < 0 or ascension_level > 20:
                        validation_result["errors"].append("start command ascension level must be between 0 and 20")
                except ValueError:
                    validation_result["errors"].append("start command ascension level must be a number")
            
            if len(tokens) >= 4:
                seed = tokens[3].upper()
                if not re.match(r'^[A-Z0-9]+$', seed):
                    validation_result["errors"].append("start command seed must be alphanumeric")
            
            if len(tokens) > 4:
                validation_result["errors"].append("start command has too many arguments")
        
        if not validation_result["errors"]:
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
                "CONFIRM", "CANCEL", "MAP", "DECK", "DRAW_PILE", "DISCARD_PILE", 
                "EXHAUST_PILE", "END_TURN", "UP", "DOWN", "LEFT", "RIGHT", 
                "DROP_CARD", "CARD_1", "CARD_2", "CARD_3", "CARD_4", "CARD_5",
                "CARD_6", "CARD_7", "CARD_8", "CARD_9", "CARD_10"
            }
            
            key_name = tokens[1].upper()
            if key_name not in valid_keys:
                validation_result["errors"].append(f"key command key invalid: {tokens[1]}")
            
            if len(tokens) >= 3:
                try:
                    timeout = int(tokens[2])
                    if timeout < 0:
                        validation_result["errors"].append("key command timeout must be non-negative")
                except ValueError:
                    validation_result["errors"].append("key command timeout must be a number")
            
            if len(tokens) > 3:
                validation_result["errors"].append("key command has too many arguments")
        
        if not validation_result["errors"]:
            validation_result["is_valid"] = True
    
    elif command_word == "click":
        if len(tokens) < 4:
            validation_result["errors"].append("click command format: click left/right [x] [y] [timeout]")
        elif tokens[1].upper() not in ["LEFT", "RIGHT"]:
            validation_result["errors"].append("click command button parameter must be 'left' or 'right'")
        else:
            try:
                x = float(tokens[2])
                y = float(tokens[3])
                
                if x < 0 or x > 1920:
                    validation_result["warnings"].append("X coordinate outside standard range (0-1920)")
                if y < 0 or y > 1080:
                    validation_result["warnings"].append("Y coordinate outside standard range (0-1080)")
                
                if len(tokens) >= 5:
                    try:
                        timeout = int(tokens[4])
                        if timeout < 0:
                            validation_result["errors"].append("click command timeout must be non-negative")
                    except ValueError:
                        validation_result["errors"].append("click command timeout must be a number")
                
                if len(tokens) > 5:
                    validation_result["errors"].append("click command has too many arguments")
                
            except ValueError:
                validation_result["errors"].append("click command coordinates must be numbers")
        
        if not validation_result["errors"]:
            validation_result["is_valid"] = True
    
    elif command_word == "wait":
        if len(tokens) < 2:
            validation_result["errors"].append("wait command missing time parameter")
        else:
            try:
                timeout = int(tokens[1])
                if timeout < 0:
                    validation_result["errors"].append("wait command time must be non-negative")
            except ValueError:
                validation_result["errors"].append("wait command time must be a number")
            
            if len(tokens) > 2:
                validation_result["errors"].append("wait command has too many arguments")
        
        if not validation_result["errors"]:
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
