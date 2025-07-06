import json
import requests
import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple
from .prompt_generator import PromptGenerator
from enum import Enum
from .logger import log, log_to_run

class LLMClient:
    def __init__(self, model_name: str = "qwen3:8b", base_url: str = "http://localhost:11434", enable_debug_output: bool = True, timeout: int = 120):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api/chat"
        self.enable_debug_output = enable_debug_output
        self.turn_counter = 0
        self.timeout = timeout
        self.debug_file = None
        
    def generate_action(self, game_state_json: Dict[Any, Any]) -> str:
        try:
            prompt_generator = PromptGenerator(game_state_json)
            prompt = prompt_generator.generate_prompt_from_state()
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.3,
            }
            
            action_command = "wait"  # Default action
            max_retries = 10
            
            for attempt in range(max_retries):
                try:
                    log(f"LLM请求尝试 {attempt + 1}/{max_retries}")
                    log(f"等待LLM响应中...（最长{self.timeout}秒超时）")
                    response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result.get("message", {}).get("content", "").strip()
                        log(f"LLM prompt为：{prompt}")
                        log(f"LLM输出为：{generated_text}")
                        
                        if not generated_text:
                            log(f"LLM返回空响应，尝试重试...")
                            continue

                        validated_action = self._extract_and_validate_action(generated_text, game_state_json)
                        if validated_action:
                            log(f"LLM成功生成并验证动作: {validated_action}")
                            action_command = validated_action
                            break 
                        else:
                            log(f"LLM生成的动作无法验证或无效，尝试重试...")
                    else:
                        log(f"API请求失败，状态码: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    log(f"网络请求异常: {e}")
            
            log_to_run(f"LLM generated action JSON: {action_command}")
            return action_command
        
        except Exception as e:
            error_msg = f"在LLM生成过程中发生严重错误: {e}"
            log(error_msg)
            return "wait"
        
    def _extract_and_validate_action(self, llm_output: str, state_json: dict) -> str | None:
        # Step 1: Remove the thinking block to only parse the command
        cleaned_output = re.sub(r'<think>.*?</think>', '', llm_output, flags=re.DOTALL).strip()

        # Step 2: Get valid commands from the game state
        game_state = state_json.get("game_state", {})
        # For choices, the command is 'choose {choice}', but the choice_list only contains the choice itself.
        # We need to handle this. For now, let's combine both available_commands and choice_list
        available_commands = state_json.get("available_commands", [])
        choice_list = game_state.get("choice_list", [])
        
        # If choices are available, the command is likely 'choose <choice>'
        if choice_list:
            # Check if the LLM wants to choose something
            if cleaned_output.lower().startswith("choose "):
                chosen_option = cleaned_output.split(maxsplit=1)[1]
                # Find if the chosen option is in our choice list
                for choice in choice_list:
                    if chosen_option.lower() == choice.lower():
                        return f"choose {choice}" # Return the full command
            # Also check for raw choices like "talk"
            for choice in choice_list:
                if cleaned_output.lower() == choice.lower():
                    # The actual command is just the choice itself for some events
                    return choice

        # Check for other commands if no choice was made or choices aren't available
        valid_commands = available_commands + choice_list
        if not valid_commands:
            return None
            
        # Sort by length to match longer commands first (e.g., "choose Smith" before "choose")
        sorted_commands = sorted(valid_commands, key=len, reverse=True)
        for command in sorted_commands:
            if command.lower() in cleaned_output.lower():
                return command
                
        return None