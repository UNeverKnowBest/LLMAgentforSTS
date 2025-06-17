import sys
import json
import requests
import time
from .logger import log, log_to_run



class Client:

    def __init__(self):
        # 发送ready信号到stdout
        print("ready", flush=True)
        log("Sent ready signal to Communication Mod")

    def send_message(self, message: str) -> str:

        log_message = f"Sending command: {message}"
        log_to_run(log_message)
        print(message, flush=True)

        try:
            response = sys.stdin.readline().strip()
            
            # 截断长响应以避免日志过长
            display_response = response
            if len(response) > 200:
                display_response = response[:200] + "...(truncated)"

            log_message = f"Received response: {display_response}"
            log_to_run(log_message)
            
            return response
            
        except EOFError:
            error_msg = "Connection to Communication Mod lost (EOF)"
            log(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error reading from Communication Mod: {e}"
            log(error_msg)
            raise Exception(error_msg)


    def get_state(self) -> dict:
        try:
            response_str = self.send_message("state")
            return json.loads(response_str)
        except json.JSONDecodeError:
            log("Error: Failed to decode state JSON from response.")
            raise
        except Exception as e:
            log(f"An unexpected error occurred while getting state: {e}")
            raise
