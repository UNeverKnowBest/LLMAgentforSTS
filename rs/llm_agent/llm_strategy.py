import json
from typing import List, Optional
from rs.api.client import Client
from rs.helper.logger import log, log_to_run
from rs.llm_agent.llm_client import LLMClient, ScreenType
from rs.llm_agent.action_converter import ActionConverter
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.handlers.handler import Handler


class LLMHandler(Handler):
    """LLM驱动的游戏处理器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    def can_handle(self, game_state) -> bool:
        """LLM处理器可以处理所有游戏状态"""
        return True
    
    def handle(self, game_state) -> Optional[HandlerAction]:
        """使用LLM生成游戏动作，并为简单场景提供硬编码的快速路径。"""
        try:
            # 首先，确定上下文
            context = self.llm_client._get_context(game_state.json)
            log_to_run(f"Determined context: {context}")
            
            # 为简单、确定的场景提供硬编码的快速路径
            gs = game_state.json.get("game_state", {})
            screen_type = gs.get("screen_type")

            if context == "游戏加载中":
                log_to_run("Game is loading, forcing a 'wait' command.")
                return HandlerAction(commands=["wait"])
            
            if screen_type == ScreenType.CHEST:
                # 宝箱总是打开
                log_to_run("Chest found, forcing 'open' command.")
                return HandlerAction(commands=["choose 0"]) # 假设 'open' 总是第一个选项

            if screen_type == ScreenType.COMBAT_REWARD:
                # 战斗奖励界面，如果没有选项了，就总是点 "继续"
                if not gs.get("choice_list"):
                     log_to_run("Combat reward screen is empty, forcing 'proceed'.")
                     return HandlerAction(commands=["proceed"])


            # 如果不是需要硬编码的简单场景，则正常调用LLM
            log_to_run("Calling LLM to generate action for complex scenario...")
            action_json, _ = self.llm_client.generate_action(game_state.json) # context已经确定，此处返回的context可以忽略
            log_to_run(f"LLM generated action JSON: {action_json}")
            
            # 转换为游戏命令 (传递调试文件路径)
            debug_file = getattr(self.llm_client, 'debug_file', None)
            commands = ActionConverter.convert_to_game_commands(json.dumps(action_json), game_state.json, debug_file)
            
            if commands:
                log_to_run(f"LLM Handler executing commands: {commands}")
                
                # 记录最终执行的命令到调试文件
                if debug_file and self.llm_client.enable_debug_output:
                    self._log_final_command(debug_file, commands, context)
                
                return HandlerAction(commands=commands)
            else:
                log_to_run("LLM Handler: No valid commands generated")
                return None
                
        except Exception as e:
            log_to_run(f"Error in LLM Handler: {e}")
            # 返回默认动作
            return HandlerAction(commands=["end"])
    
    def _log_final_command(self, debug_file: str, commands: List[str], context: str):
        """记录最终执行的命令"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Final Command Sent ---\n")
                f.write(f"  - Context: {context}\n")
                f.write(f"  - Timestamp: {timestamp}\n")
                f.write(f"  - Command: {commands}\n")
        except Exception as e:
            log_to_run(f"记录最终命令失败: {e}")


class LLMGame:
    """使用LLM的简化游戏控制器"""
    
    def __init__(self, client: Client, llm_client: LLMClient, character: str = "IRONCLAD"):
        self.client = client
        self.llm_client = llm_client
        self.character = character
        self.handler = LLMHandler(llm_client)
        self.last_state = None
        self.stuck_counter = 0
    
    def start_game(self):
        """启动游戏或连接到已在运行的游戏，并确保在进入主循环前获得一个有效的游戏状态。"""
        log("Attempting to start or connect to game...")
        
        # 检查初始状态，看游戏是否已在运行
        initial_state = self.client.get_state(silent=True)
        
        # 如果游戏未运行，则启动并等待
        if not initial_state.get("in_game", False):
            log("Game not in progress. Sending start command and waiting for game to be ready...")
            start_command = f"start {self.character}"
            self.client.send_message(start_command)
            
            # 循环等待，直到游戏真正开始
            import time
            max_wait_time = 30  # seconds
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                current_state = self.client.get_state(silent=True)
                if current_state and current_state.get("in_game", False):
                    self.last_state = current_state
                    log(f"Game is ready. Initial state established. In-game: True")
                    return # 成功获取状态，退出方法
                time.sleep(0.5) # 短暂等待后重试

            # 如果超时
            log("FATAL: Waited too long for the game to start. Exiting.")
            raise Exception("Game did not start within the expected time.")

        else:
            log("Game already in progress. Using existing state.")
            self.last_state = initial_state
            log(f"Initial state established. In-game: True")
        
    
    def run(self):
        """运行健壮的游戏主循环，能够处理游戏暂时的"未就绪"状态。"""
        log("DEBUG: Entered run() method. Checking state...")
        log(f"DEBUG: self.last_state at start of run(): {self.last_state}")

        log_to_run("Starting Robust LLM Game Loop")
        log("DEBUG: Starting main game loop...")
        
        while self.last_state.get("in_game", False):
            # 卡死检测：在处理前，复制当前状态
            previous_state_for_stuck_detection = self.last_state.copy()

            try:
                # 简化循环: 始终让处理器来决定动作，不再依赖 ready_for_command
                log_to_run(f"State received. Passing to handler...")
                
                # 创建简化的game_state对象用于处理器
                class SimpleGameState:
                    def __init__(self, json_data):
                        self.json = json_data
                
                simple_state = SimpleGameState(self.last_state)
                
                # 使用LLM处理器生成动作
                action = self.handler.handle(simple_state)
                
                if action and action.commands:
                    command = action.commands[0]
                    log_to_run(f"Executing command: {command}")
                    
                    # 发送命令，但不处理直接的响应
                    self.client.send_message(command, silent=True) # silent=True避免重复记录
                    
                    # 总是通过再次请求来获取权威的新状态
                    # 这能解决游戏Mod连续发送多个状态的同步问题
                    log_to_run("Command sent. Fetching authoritative new state...")
                    self.last_state = self.client.get_state()
                    log_to_run("New state established.")

                else:
                    # 如果处理器没有返回任何动作（例如，在某些过渡状态下），
                    # 我们不发送任何命令，而是直接等待并获取下一个状态。
                    # 这可以处理游戏主动发送多个连续状态的情况。
                    log_to_run(f"No action generated by handler. Waiting for the next state from the game...")
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
                # 尝试发送一个安全的命令来恢复
                try:
                    log_to_run("Attempting to recover with 'wait' command...")
                    response = self.client.send_message("wait")
                    self.last_state = json.loads(response) if response else self.client.get_state()
                    log_to_run("Recovery with 'wait' successful.")
                except Exception as recovery_e:
                    log_to_run(f"Recovery with 'wait' failed: {recovery_e}. Stopping game.")
                    break
            
            # 卡死检测：在处理后，比较状态
            if self.last_state == previous_state_for_stuck_detection:
                self.stuck_counter += 1
                log_to_run(f"WARNING: Game state has not changed. Stuck counter: {self.stuck_counter}")
            else:
                self.stuck_counter = 0 # 状态改变，重置计数器

            if self.stuck_counter > 5: # 如果连续5次状态都未改变
                log_to_run("FATAL: Game is stuck in a loop. Terminating.")
                break # 退出主循环

        # 游戏结束原因
        log_to_run("\n" + "="*20 + " Game Loop Ended " + "="*20)
        if not self.last_state.get("in_game", False):
            log_to_run("Reason: Game reported 'in_game: false'. This is a normal end to a run (win or death).")
        else:
            log_to_run(f"Reason: Loop exited due to an unhandled error or condition.")
        log_to_run("="*57) 