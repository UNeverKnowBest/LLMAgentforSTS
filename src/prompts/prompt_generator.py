from typing import Dict, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
import os
from src.game.game_constants import ScreenType

class PromptGenerator:
    def __init__(self, game_state_json: Dict) -> None:
        self.game_state_json = game_state_json
        self.game_state = game_state_json.get("game_state", {})
        
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        self.simple_command_map: Dict[ScreenType, str] = {
            ScreenType.CHEST: "choose open",        
            ScreenType.SHOP_ROOM: "choose shop",    
            ScreenType.COMPLETE: "proceed",         
            ScreenType.GAME_OVER: "end",           
        }
        
        self.template_screens = {
            ScreenType.COMBAT,          
            ScreenType.MAP,             
            ScreenType.CARD_REWARD,     
            ScreenType.REST,            
            ScreenType.SHOP_SCREEN,    
            ScreenType.EVENT,           
            ScreenType.BOSS_REWARD,     
            ScreenType.GRID,            
            ScreenType.HAND_SELECT,     
            ScreenType.COMBAT_REWARD,   
        }

    def get_command_or_prompt(self) -> Tuple[Optional[str], Optional[str]]:
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