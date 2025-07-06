import json
import time
from typing import List, Optional
from .client import Client
from .llm_client import LLMClient
from .handler import LLMHandler
from .logger import log, log_info, log_error, log_game_state, log_action_execution

class LLMGame:

    def __init__(self, client: Client, llm_client: LLMClient, character: str):
        self.client = client
        self.llm_client = llm_client
        self.character = character
        self.handler = LLMHandler(llm_client)
        self.last_state = None
        self.stuck_counter = 0
    
    def start_game(self):
        log_info("正在启动新游戏...", character=self.character)
        start_command = f"start {self.character}"
        self.client.send_message(start_command)
        self.last_state = None
        
    def run(self):
        log_info("等待游戏初始化...")
        time.sleep(5)
        
        # 请求游戏状态
        log_info("正在获取初始游戏状态...")
        self.last_state = self.client.get_state()

        while self.last_state.get("in_game", False):
            try:
                # 记录当前状态以供调试
                log_game_state(self.last_state)
                
                class GameState:
                    def __init__(self, json_data):
                        self.json = json_data
                
                game_state = GameState(self.last_state)
                if self.last_state.get("ready_for_command"):
                    action = self.handler.handle(game_state)
                    command = action
                    
                    if command == "wait":
                        command = "wait 10"

                    log_action_execution(command, True)
                    self.client.send_message(command)
                    self.last_state = self.client.get_state()
                else:
                    # 如果不需要命令，短暂等待后获取新状态
                    time.sleep(0.5) 
                    self.last_state = self.client.get_state()

            except json.JSONDecodeError as e:
                log_error("解析状态JSON失败，正在尝试恢复...", exception=e)
                try:
                    # 尝试重新获取状态
                    self.last_state = self.client.get_state()
                    log_info("状态恢复成功")
                except Exception as recovery_e:
                    log_error("恢复失败，正在发送 'state' 命令重置...", exception=recovery_e)
                    try:
                        # 最后尝试：发送state命令重置连接
                        self.last_state = self.client.get_state()
                        log_info("状态重置成功")
                    except Exception as final_e:
                        log_error("所有恢复尝试均失败，游戏停止", exception=final_e)
                        break
            except Exception as e:
                log_error("游戏主循环发生未知错误", exception=e)
                try:
                    response = self.client.send_message("wait 10")
                    self.last_state = json.loads(response) if response else self.client.get_state()
                    log_info("使用 'wait' 命令恢复成功")
                except Exception as recovery_e:
                    log_error("使用 'wait' 命令恢复失败，游戏停止", exception=recovery_e)
                    break

        log_info("="*20 + " 游戏主循环结束 " + "="*20)
        if not self.last_state.get("in_game", False):
            log_info("原因: 游戏状态为 'in_game: false'。这通常意味着一局游戏正常结束（胜利或失败）。")
        else:
            log_info("原因: 循环因未知错误或异常情况退出。")
        log_info("="*57) 