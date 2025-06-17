from .llm_client import LLMClient
from .logger import log_to_run




class LLMHandler:
    """LLM驱动的游戏处理器"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    def handle(self, game_state) -> str:
        """use LLM to generate game commands based on the current game state"""
        
        log_to_run("Calling LLM to generate action for complex scenario...")
        command = self.llm_client.generate_action(game_state.json)
        log_to_run(f"LLM generated action JSON: {command}")   
        log_to_run(f"LLM Handler executing commands: {command}")

        return command





