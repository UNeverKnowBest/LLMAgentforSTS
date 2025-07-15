from typing import Dict, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
import os
from src.game.game_constants import ScreenType

class PromptGenerator:
    """
    Prompt生成器类，负责根据游戏状态生成LLM上下文
    使用Jinja2模板系统为不同的游戏场景生成专业化的prompt
    """
    
    def __init__(self, game_state_json: Dict) -> None:
        """
        初始化PromptGenerator
        
        Args:
            game_state_json: 完整的游戏状态JSON数据，包含game_state和available_commands
        """
        self.game_state_json = game_state_json
        self.game_state = game_state_json.get("game_state", {})
        
        # 初始化Jinja2模板环境
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # 简单命令映射 - 不需要复杂prompt的场景
        self.simple_command_map: Dict[ScreenType, str] = {
            ScreenType.CHEST: "choose open",        # 宝箱 - 直接打开
            ScreenType.SHOP_ROOM: "choose shop",    # 商店房间 - 进入商店
            ScreenType.COMPLETE: "proceed",         # 完成状态 - 继续
            ScreenType.GAME_OVER: "end",           # 游戏结束 - 结束
        }
        
        # 需要使用模板生成prompt的复杂场景
        self.template_screens = {
            ScreenType.COMBAT,          # 战斗
            ScreenType.MAP,             # 地图选择
            ScreenType.CARD_REWARD,     # 卡牌奖励
            ScreenType.REST,            # 休息点
            ScreenType.SHOP_SCREEN,     # 商店界面
            ScreenType.EVENT,           # 事件
            ScreenType.BOSS_REWARD,     # Boss奖励
            ScreenType.GRID,            # 网格选择
            ScreenType.HAND_SELECT,     # 手牌选择
            ScreenType.COMBAT_REWARD,   # 战斗奖励
        }

    def get_command_or_prompt(self) -> Tuple[Optional[str], Optional[str]]:
        """
        根据当前游戏状态返回简单命令或生成的prompt
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (command, prompt) - 只有一个会有值
            - 如果是简单场景，返回(command, None)
            - 如果是复杂场景，返回(None, prompt)
            - 如果无法识别场景，返回("state", None)
        """
        screen_type = self._get_effective_screen_type()
        
        # 检查是否有简单命令
        if command := self.simple_command_map.get(screen_type):
            return command, None
        
        # 检查是否需要生成复杂prompt
        if screen_type in self.template_screens:
            prompt = self._generate_prompt_from_template()
            return None, prompt
        
        # 默认返回状态查询命令
        return "state", None

    def _get_effective_screen_type(self) -> ScreenType:
        """
        确定有效的屏幕类型，处理特殊情况
        
        Returns:
            ScreenType: 当前有效的屏幕类型
        """
        screen_type = self.game_state.get("screen_type", "NONE")
        room_phase = self.game_state.get("room_phase")

        # 特殊情况处理：当screen_type为NONE但处于战斗阶段时
        if screen_type == "NONE" and room_phase == "COMBAT":
            return ScreenType.COMBAT
        
        try:
            return ScreenType(screen_type)
        except ValueError:
            return ScreenType.NONE

    def _generate_prompt_from_template(self) -> str:
        """
        使用Jinja2模板生成LLM prompt
        
        Returns:
            str: 渲染后的prompt文本
        """
        try:
            # 加载基础模板
            template = self.env.get_template('base.jinja')
            
            # 渲染模板，传入完整的游戏状态数据
            prompt = template.render(
                game_state_json=self.game_state_json,
                game_state=self.game_state,
                screen_state=self.game_state.get("screen_state", {}),
                screen_type=self.game_state.get("screen_type", "NONE"),
                player_deck=self.game_state.get("deck", [])
            )
            
            return prompt.strip()
            
        except Exception as e:
            # 如果模板渲染失败，返回简化的错误信息
            error_msg = (
                f"模板渲染错误: {str(e)}\n"
                f"当前屏幕类型: {self.game_state.get('screen_type', 'UNKNOWN')}\n"
                f"请使用 'state' 命令获取更多信息。"
            )
            return error_msg

    def get_screen_type(self) -> ScreenType:
        """
        获取当前屏幕类型
        
        Returns:
            ScreenType: 当前屏幕类型
        """
        return self._get_effective_screen_type()
    
    def has_simple_command(self) -> bool:
        """
        检查当前场景是否有简单命令
        
        Returns:
            bool: 如果当前场景有预定义的简单命令则返回True
        """
        screen_type = self._get_effective_screen_type()
        return screen_type in self.simple_command_map
    
    def needs_prompt(self) -> bool:
        """
        检查当前场景是否需要生成详细prompt
        
        Returns:
            bool: 如果当前场景需要复杂的模板prompt则返回True
        """
        screen_type = self._get_effective_screen_type()
        return screen_type in self.template_screens
    
    def get_available_commands(self) -> list:
        """
        获取可用命令列表
        
        Returns:
            list: 当前可用的命令列表
        """
        return self.game_state_json.get("available_commands", [])
    
    def debug_info(self) -> Dict:
        """
        获取调试信息
        
        Returns:
            Dict: 包含当前状态的调试信息
        """
        return {
            "screen_type": self.get_screen_type().value,
            "has_simple_command": self.has_simple_command(),
            "needs_prompt": self.needs_prompt(),
            "available_commands": self.get_available_commands(),
            "room_phase": self.game_state.get("room_phase"),
            "act": self.game_state.get("act"),
            "floor": self.game_state.get("floor")
        }
    
    