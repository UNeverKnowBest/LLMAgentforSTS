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
    def __init__(self, model_name: str = "qwen3:4b", base_url: str = "http://localhost:11434", enable_debug_output: bool = True, timeout: int = 120):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api/generate"
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
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.3,
            }
            
            generated_text = ""
            action_json = {}
            max_retries = 10
            
            for attempt in range(max_retries):
                try:
                    log(f"LLM请求尝试 {attempt + 1}/{max_retries}")
                    log(f"等待LLM响应中...（最长{self.timeout}秒超时）")
                    response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                
                    if response.status_code == 200:
                        result = response.json()
                        action_command = result.get("response", "").strip()
                        log(f"LLM prompt为：{prompt}")
                        log(f"LLM输出为：{action_command}")
                        
                        if not generated_text:
                            log(f"LLM返回空响应，尝试重试...")
                            continue

                        if self._extract_and_validate_action(action_command, game_state_json):
                            log(f"LLM成功生成动作: {action_command}")
                            break
                        else:
                            log(f"LLM生成的动作格式无效，尝试重试...")
                    else:
                        log(f"API请求失败，状态码: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    log(f"网络请求异常: {e}")
            
            log_to_run(f"LLM generated action: {action_command}")
            return action_command
        
        except Exception as e:
            error_msg = f"在LLM生成过程中发生严重错误: {e}"
            log(error_msg)
            return "wait"
        
    def _extract_and_validate_action(self, llm_output: str, state_json: dict) -> str | None:
        game_state = state_json.get("game_state", {})
        valid_commands = game_state.get("choice_list", state_json.get("available_commands", []))
        if not valid_commands:
            return None
        sorted_commands = sorted(valid_commands, key=len, reverse=True)
        for command in sorted_commands:
            if command in llm_output:
                return command
        return None