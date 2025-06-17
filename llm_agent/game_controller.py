import json
import time
from typing import List, Optional
from .client import Client
from .llm_client import LLMClient
from .handler import LLMHandler
from .logger import log, log_to_run

class LLMGame:

    def __init__(self, client: Client, llm_client: LLMClient, character: str):
        self.client = client
        self.llm_client = llm_client
        self.character = character
        self.handler = LLMHandler(llm_client)
        self.last_state = None
        self.stuck_counter = 0
    
    def start_game(self):
        log("Game starting...")
        start_command = f"start {self.character}"
        self.client.send_message(start_command)
        self.last_state = None
        
    def run(self):
        log_to_run("Starting Run...")
        log_to_run("Waiting 5 seconds for game to initialize...")
        time.sleep(5)
        
        # Request the game state
        log_to_run("Fetching initial game state...")
        self.last_state = self.client.get_state()

        while self.last_state.get("in_game", False):
            try:
                log_to_run(f"State received. Passing to handler...")
                class GameState:
                    def __init__(self, json_data):
                        self.json = json_data
                
                game_state = GameState(self.last_state)
                if self.last_state.get("ready_for_command"):
                    action = self.handler.handle(game_state)
                    command = action
                    log_to_run(f"Executing command: {command}")
                    self.client.send_message(command)
                    log_to_run("Command sent. Fetching authoritative new state...")
                    self.last_state = self.client.get_state()
                    log_to_run("New state established.")

                else:
                    log_to_run(f"No action required now")
                    self.last_state = self.client.get_state()

            except json.JSONDecodeError as e:
                log_to_run(f"Failed to parse state JSON: {e}. Attempting to recover...")
                try:
                    # 尝试重新获取状态
                    self.last_state = self.client.get_state()
                    log_to_run("Recovery successful.")
                except Exception as recovery_e:
                    log_to_run(f"Recovery failed: {recovery_e}. Sending 'state' command to reset...")
                    try:
                        # 最后尝试：发送state命令重置连接
                        self.last_state = self.client.get_state()
                        log_to_run("State reset successful.")
                    except Exception as final_e:
                        log_to_run(f"All recovery attempts failed: {final_e}. Stopping game.")
                        break
            except Exception as e:
                log_to_run(f"Error in game loop: {e}")
                try:
                    log_to_run("Attempting to recover with 'wait' command...")
                    response = self.client.send_message("wait")
                    self.last_state = json.loads(response) if response else self.client.get_state()
                    log_to_run("Recovery with 'wait' successful.")
                except Exception as recovery_e:
                    log_to_run(f"Recovery with 'wait' failed: {recovery_e}. Stopping game.")
                    break

        log_to_run("\n" + "="*20 + " Game Loop Ended " + "="*20)
        if not self.last_state.get("in_game", False):
            log_to_run("Reason: Game reported 'in_game: false'. This is a normal end to a run (win or death).")
        else:
            log_to_run(f"Reason: Loop exited due to an unhandled error or condition.")
        log_to_run("="*57) 