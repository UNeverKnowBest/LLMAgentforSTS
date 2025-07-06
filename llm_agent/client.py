import sys
import json
import requests
import time
from .logger import log_info, log_error, log_debug, log_to_run, log_function_call

class Client:

    @log_function_call
    def __init__(self):
        # 发送ready信号到stdout
        print("ready", flush=True)
        log_info("向Communication Mod发送ready信号")

    @log_function_call
    def send_message(self, message: str) -> str:
        log_debug(f"准备发送命令", command=message, command_length=len(message))
        log_to_run(f"Sending command: {message}")
        
        print(message, flush=True)

        try:
            response = sys.stdin.readline().strip()
            
            log_debug(f"收到响应", 
                     response_preview=response[:100] + "..." if len(response) > 100 else response,
                     response_length=len(response))
            log_to_run(f"Received response: {response}")
            
            return response
            
        except EOFError:
            error_msg = "与Communication Mod的连接丢失 (EOF)"
            log_error(error_msg, attempted_command=message)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"从Communication Mod读取数据时出错"
            log_error(error_msg, exception=e, attempted_command=message)
            raise Exception(f"{error_msg}: {e}")

    @log_function_call
    def get_state(self) -> dict:
        try:
            log_debug("请求游戏状态")
            response_str = self.send_message("state")
            
            # 尝试解析JSON
            game_state = json.loads(response_str)
            
            # 记录状态信息摘要
            if 'game_state' in game_state:
                gs = game_state['game_state']
                log_debug("成功获取游戏状态",
                         screen_type=gs.get('screen_type', 'UNKNOWN'),
                         room_phase=gs.get('room_phase', 'UNKNOWN'),
                         floor=gs.get('floor', '?'),
                         hp=f"{gs.get('current_hp', '?')}/{gs.get('max_hp', '?')}",
                         available_commands_count=len(game_state.get('available_commands', [])))
            
            return game_state
            
        except json.JSONDecodeError as e:
            log_error("解析游戏状态JSON失败", 
                     exception=e,
                     raw_response=response_str[:200] + "..." if len(response_str) > 200 else response_str)
            raise
        except Exception as e:
            log_error("获取游戏状态时发生意外错误", exception=e)
            raise
