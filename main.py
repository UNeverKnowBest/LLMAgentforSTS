import traceback
import os
import logging

from llm_agent.client import Client
from llm_agent.llm_client import  LLMClient
from llm_agent.game_controller import LLMGame
from LLMAgentforSTS.llm_agent.logger import log, log_to_run

character = "THE_SILENT"

def run_agent():
    log_to_run("llm_run")
    
    client = None
    llm_client = None
    
    try:
        log("Initializing LLM Agent")

        # Initialize the client and LLM client
        client = Client()
        llm_client = LLMClient(
            model_name="qwen3:b",
            base_url="http://localhost:11434",
            enable_debug_output=True
        )

        # Initialize the game controller
        llm_game = LLMGame(client, llm_client, character=character)
        
        # Start game
        log("Starting game...")
        llm_game.start_game()

        # Game loop
        log("Running game loop...")
        llm_game.run()

    except Exception as e:
        log(f"FATAL: 主循环中发生异常", logging.ERROR)
        log(f"异常类型: {type(e).__name__}", logging.ERROR)
        log(f"异常信息: {str(e)}", logging.ERROR)
        tb_str = traceback.format_exc()
        log(f"详细错误信息:\n{tb_str}", logging.ERROR)

    finally:
        log("程序结束")

if __name__ == "__main__":
    run_agent()
