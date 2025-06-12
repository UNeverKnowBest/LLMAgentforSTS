import traceback

from rs.api.client import Client
from rs.helper.logger import log, init_log, log_new_run_sequence, init_run_logging
from rs.llm_agent.llm_client import  LLMClient
from rs.llm_agent.llm_strategy import LLMGame

character = "THE_SILENT"  # 可选: IRONCLAD, THE_SILENT, DEFECT, WATCHER

def run_simple_agent():
    init_log()
    log_new_run_sequence()
    # 为详细的逐回合日志初始化
    # 注意: 我们假设游戏种子(seed)在这里是未知的，所以使用一个占位符
    init_run_logging("llm_run")
    
    client = None
    llm_client = None
    
    try:
        log("Initializing LLM Agent")
        
        # 初始化客户端（这会发送ready信号）
        client = Client()
        
        # 初始化LLM客户端
        llm_client = LLMClient(
            model_name="qwen3:4b",
            base_url="http://localhost:11434",
            enable_debug_output=True
        )
        
        # Create a game controller
        llm_game = LLMGame(client, llm_client, character=character)
        
        # Start game
        log("Starting game...")
        llm_game.start_game()
        
        # Game loop
        log("Running game loop...")
        llm_game.run()
        
        log("Game completed successfully")
        
    except KeyboardInterrupt:
        log("用户中断了程序")
    except Exception as e:
        log(f"FATAL: 主循环中发生异常")
        log(f"异常类型: {type(e).__name__}")
        log(f"异常信息: {str(e)}")
        
        # 记录详细的traceback
        tb_str = traceback.format_exc()
        log(f"详细错误信息:\n{tb_str}")
        
        # 尝试优雅关闭
        try:
            if client:
                log("尝试发送退出命令...")
                client.send_message("quit", silent=True)
        except:
            pass
            
        # 重新抛出异常以便调试
        raise
    finally:
        log("程序结束")
        if llm_client and hasattr(llm_client, 'debug_file'):
            log(f"调试日志保存在: {llm_client.debug_file}")

if __name__ == "__main__":
    run_simple_agent()
