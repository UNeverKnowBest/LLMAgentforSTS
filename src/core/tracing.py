"""
LangSmith 追踪配置模块
用于监控和调试 LLM 调用
"""

import os
import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime

from src.config import (
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    LANGSMITH_ENDPOINT,
    LANGSMITH_ENABLED
)

logger = logging.getLogger(__name__)

class TracingManager:
    """
    LangSmith 追踪管理器
    """
    
    def __init__(self):
        self.langsmith_enabled = False
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """
        设置 LangSmith 追踪
        """
        try:
            api_key = LANGSMITH_API_KEY or os.getenv("LANGSMITH_API_KEY")
            
            if api_key and LANGSMITH_ENABLED:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = api_key
                os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
                os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
                
                self.langsmith_enabled = True
                logger.info(f"✅ LangSmith 追踪已启用 - 项目: {LANGSMITH_PROJECT}")
                
                self._test_langsmith_connection()
                
            else:
                logger.info("ℹ️ LangSmith 追踪未启用 (需要 API Key)")
                
        except Exception as e:
            logger.error(f"❌ LangSmith 设置失败: {e}")
            self.langsmith_enabled = False
    
    def _test_langsmith_connection(self):
        """
        测试 LangSmith 连接
        """
        try:
            print("--- Testing LangSmith connection ---", file=sys.stderr, flush=True)
            from langsmith import Client
            client = Client(timeout=10)
            client.read_project(project_name=LANGSMITH_PROJECT)
            print("--- LangSmith connection test successful ---", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"--- LangSmith connection test failed: {e} ---", file=sys.stderr, flush=True)
    
    def create_run_metadata(self, screen_type: str, floor: int, act: int) -> Dict[str, Any]:
        """
        创建运行元数据，用于 LangSmith 追踪
        """
        return {
            "screen_type": screen_type,
            "floor": floor,
            "act": act,
            "game": "Slay the Spire",
            "agent_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }

tracing_manager = TracingManager()

def get_tracing_manager() -> TracingManager:
    """
    获取追踪管理器实例
    """
    return tracing_manager 