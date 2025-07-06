import traceback
import os
import logging

from llm_agent.client import Client
from llm_agent.llm_client import  LLMClient
from llm_agent.game_controller import LLMGame
from llm_agent.logger import (
    log, log_info, log_error, log_debug, log_to_run, 
    log_function_call
)

character = "THE_SILENT"

@log_function_call
def run_agent():
    log_to_run("llm_run")
    log_info("启动LLM智能体", character=character)
    
    client = None
    llm_client = None
    
    try:
        log_info("开始初始化LLM智能体组件")

        # Initialize the client and LLM client
        log_debug("初始化Communication Mod客户端")
        client = Client()
        
        log_debug("初始化LLM客户端", model="qwen3:8b", base_url="http://localhost:11434")
        llm_client = LLMClient(
            model_name="qwen3:8b",
            base_url="http://localhost:11434",
            enable_debug_output=True
        )

        # Initialize the game controller
        log_debug("初始化游戏控制器", character=character)
        llm_game = LLMGame(client, llm_client, character=character)
        
        # Start game
        log_info("开始游戏会话")
        llm_game.start_game()

        # Game loop
        log_info("进入主游戏循环")
        llm_game.run()
        
        log_info("游戏会话正常结束")

    except KeyboardInterrupt:
        log_info("收到用户中断信号，正常退出")
    except Exception as e:
        log_error("主循环中发生严重异常", 
                 exception=e,
                 character=character,
                 client_status="已初始化" if client else "未初始化",
                 llm_client_status="已初始化" if llm_client else "未初始化")
        
        # 记录详细的异常上下文
        log_debug("异常上下文信息", 
                 exception_type=type(e).__name__,
                 exception_args=str(e.args) if hasattr(e, 'args') else "N/A",
                 current_working_dir=os.getcwd(),
                 python_path=os.environ.get('PYTHONPATH', 'N/A'))

    finally:
        log_info("程序清理完成，即将退出", exit_reason="正常结束或异常退出")

if __name__ == "__main__":
    log_info("=== LLM智能体启动 ===", 
             version="1.0",
             character=character,
             working_directory=os.getcwd())
    
    run_agent()
    
    log_info("=== 程序完全退出 ===")
