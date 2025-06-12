import sys
import json
from rs.helper.logger import log, log_to_run


class Client:

    def __init__(self):
        # 发送ready信号到stdout
        print("ready", flush=True)
        log("Sent ready signal to Communication Mod")

    def send_message(self, message: str, silent: bool = False) -> str:
        """
        向Communication Mod发送命令并接收响应
        
        Args:
            message: 要发送的命令
            silent: 如果为True，则不记录到逐回合日志
            
        Returns:
            从Communication Mod接收的响应
        """
        if not silent:
            log_message = f"Sending command: {message}"
            log_to_run(log_message)
        
        # 发送命令到stdout
        print(message, flush=True)
        
        # 从stdin读取响应
        try:
            response = sys.stdin.readline().strip()
            
            # 截断长响应以避免日志过长
            display_response = response
            if len(response) > 200:
                display_response = response[:200] + "...(truncated)"
            
            if not silent:
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

    def get_initial_state(self) -> str:
        """
        获取初始游戏状态
        Communication Mod会在ready后自动发送初始状态
        """
        try:
            log("Waiting for initial game state...")
            initial_state = sys.stdin.readline().strip()
            
            if not initial_state:
                raise Exception("Received empty initial state")
                
            log("Received initial game state")
            return initial_state
            
        except EOFError:
            error_msg = "Failed to receive initial state (EOF)"
            log(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error receiving initial state: {e}"
            log(error_msg)
            raise Exception(error_msg)

    def get_state(self, silent: bool = False) -> dict:
        """
        发送 'state' 命令并获取当前的游戏状态JSON
        """
        try:
            response_str = self.send_message("state", silent=silent)
            return json.loads(response_str)
        except json.JSONDecodeError:
            log("Error: Failed to decode state JSON from response.")
            raise
        except Exception as e:
            log(f"An unexpected error occurred while getting state: {e}")
            raise
