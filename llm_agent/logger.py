import logging
import os
import sys
import traceback
import functools
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

# 确定日志目录 - 使用绝对路径
def get_log_directory():
    """获取日志目录的绝对路径"""
    try:
        # 尝试使用脚本所在目录
        script_dir = Path(__file__).parent.parent.absolute()
        log_dir = script_dir / "logs"
    except:
        # 如果失败，使用当前工作目录
        log_dir = Path.cwd() / "logs"
    
    # 创建日志目录
    try:
        log_dir.mkdir(exist_ok=True)
        return str(log_dir)
    except Exception as e:
        # 如果无法创建，使用临时目录
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "llm_agent_logs"
        temp_dir.mkdir(exist_ok=True)
        return str(temp_dir)

LOGS_DIR = get_log_directory()

# 生成带时间戳的日志文件名
log_filename = datetime.now().strftime("run_%Y%m%d_%H%M%S.log")
log_filepath = os.path.join(LOGS_DIR, log_filename)

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"

# 创建日志处理器列表
handlers = []

# 文件处理器 - 必须有的
try:
    file_handler = logging.FileHandler(log_filepath, "w", "utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
except Exception as e:
    # 如果文件处理器失败，尝试stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.DEBUG)
    stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(stderr_handler)

# 设置主logger
try:
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
        handlers=handlers,
        force=True  # 强制重新配置
    )
except Exception as e:
    # 如果basicConfig失败，至少设置一个基本配置
    logging.basicConfig(level=logging.INFO)

# 获取logger实例
logger = logging.getLogger("LLMAgent")
logger.setLevel(logging.DEBUG)

# 确保有处理器
if not logger.handlers:
    try:
        handler = logging.FileHandler(log_filepath, "w", "utf-8")
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    except:
        # 最后的备选方案 - stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

# 禁用传播到根logger（避免干扰游戏通信）
logger.propagate = False

def log(message: str, level=logging.INFO, extra_data: Optional[Dict[str, Any]] = None):
    """
    增强版的日志记录函数
    
    Args:
        message: 日志消息
        level: 日志级别
        extra_data: 额外的调试数据
    """
    try:
        # 获取调用者信息
        frame = sys._getframe(1)
        caller_info = f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"
        
        # 构建完整的日志消息
        full_message = f"[{caller_info}] {message}"
        
        # 如果有额外数据，添加到日志中
        if extra_data:
            extra_str = ", ".join([f"{k}={v}" for k, v in extra_data.items()])
            full_message += f" | {extra_str}"
        
        logger.log(level, full_message)
        
        # 强制刷新缓冲区
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
                
    except Exception as e:
        # 如果日志记录失败，至少输出到stderr
        try:
            print(f"LOG ERROR: {message} (Error: {e})", file=sys.stderr)
            sys.stderr.flush()
        except:
            pass

def log_debug(message: str, **kwargs):
    """记录debug级别的日志"""
    log(message, logging.DEBUG, kwargs if kwargs else None)

def log_info(message: str, **kwargs):
    """记录info级别的日志"""
    log(message, logging.INFO, kwargs if kwargs else None)

def log_warning(message: str, **kwargs):
    """记录warning级别的日志"""
    log(message, logging.WARNING, kwargs if kwargs else None)

def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    """记录error级别的日志，包含异常信息"""
    error_message = message
    if exception:
        error_message += f" | Exception: {type(exception).__name__}: {str(exception)}"
        error_message += f" | Traceback: {traceback.format_exc()}"
    
    log(error_message, logging.ERROR, kwargs if kwargs else None)

def log_game_state(game_state: Dict[str, Any], action: str = ""):
    """专门用于记录游戏状态的函数"""
    try:
        # 提取关键信息
        gs = game_state.get('game_state', {})
        screen_type = gs.get('screen_type', 'UNKNOWN')
        room_phase = gs.get('room_phase', 'UNKNOWN')
        floor = gs.get('floor', '?')
        hp = f"{gs.get('current_hp', '?')}/{gs.get('max_hp', '?')}"
        gold = gs.get('gold', '?')
        
        # 构建状态摘要
        state_summary = f"Floor:{floor}, HP:{hp}, Gold:{gold}, Screen:{screen_type}, Phase:{room_phase}"
        
        # 仅在有动作时记录为INFO，否则为DEBUG
        level = logging.INFO if action else logging.DEBUG
        
        if action:
            message = f"游戏状态: {state_summary} | 待执行动作: {action}"
        else:
            message = f"游戏状态更新: {state_summary}"
        
        log(message, level=level, 
            game_state_keys=list(game_state.keys()), 
            available_commands=len(game_state.get('available_commands', [])))
        
    except Exception as e:
        log_error(f"记录游戏状态时发生错误", exception=e)

def log_llm_interaction(prompt: str, response: str, model_name: str = "", duration: float = 0):
    """记录LLM交互信息"""
    prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
    response_preview = response[:200] + "..." if len(response) > 200 else response
    
    log_info(f"LLM交互完成", 
             model=model_name,
             duration=f"{duration:.2f}s",
             prompt_length=len(prompt),
             response_length=len(response),
             prompt_preview=prompt_preview,
             response_preview=response_preview)

def log_action_execution(action: str, success: bool, result: Any = None, error: Optional[Exception] = None):
    """记录动作执行结果"""
    if success:
        log_info(f"动作执行成功: {action}", result=str(result) if result else None)
    else:
        log_error(f"动作执行失败: {action}", exception=error, attempted_action=action)

def log_to_run(message: str):
    """简单的运行日志记录（保持向后兼容）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 尝试多个位置写入run.log
    run_log_paths = [
        "run.log",  # 当前目录
        os.path.join(LOGS_DIR, "run.log"),  # 日志目录
        os.path.join(os.path.dirname(__file__), "..", "run.log")  # 项目根目录
    ]
    
    log_content = f"[{timestamp}] {message}\n"
    
    for path in run_log_paths:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(log_content)
                f.flush()
            # 成功写入后即退出循环
            return
        except Exception:
            continue
    
    # 如果所有路径都失败，则记录一个错误
    log_warning(f"无法写入run.log: {message}")

def log_function_call(func):
    """装饰器：自动记录函数调用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        log_debug(f"调用函数: {func_name}", args_count=len(args), kwargs_keys=list(kwargs.keys()))
        
        try:
            start_time = datetime.now()
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            log_debug(f"函数执行完成: {func_name}", duration=f"{duration:.3f}s", success=True)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            log_error(f"函数执行失败: {func_name}", exception=e, duration=f"{duration:.3f}s")
            raise
    
    return wrapper

# 初始化日志系统
def init_logging():
    """初始化日志系统，确保在任何环境下都能工作"""
    try:
        log_info("=== 日志系统初始化 ===", 
                 log_dir=LOGS_DIR,
                 log_file=log_filename,
                 working_dir=os.getcwd(),
                 script_dir=os.path.dirname(os.path.abspath(__file__)))
        return True
    except Exception as e:
        try:
            print(f"日志系统初始化失败: {e}", file=sys.stderr)
            return False
        except:
            return False

# 自动初始化
init_logging() 