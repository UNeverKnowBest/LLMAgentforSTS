import json

from typing import Dict, Any, Tuple

from .config.prompt import (
    BASE_TEMPLATE,
    COMBAT_PROMPT_TEMPLATE,
    MAP_PROMPT_TEMPLATE,
    CARD_REWARD_PROMPT_TEMPLATE,
    REST_SITE_PROMPT_TEMPLATE,
    SHOP_PROMPT_TEMPLATE,
    GENERIC_PROMPT_TEMPLATE,
    OUTPUT_FORMAT_TEMPLATE,
    EVENT_PROMPT_TEMPLATE,
    COMPLETE_PROMPT_TEMPLATE
)
from .logger import log


class PromptGenerator:
    """Generate the prompt based on the current game state info"""
    def __init__(self, game_state_json: Dict[Any, Any]):
        self.game_state_json = game_state_json

    def _format_base_context(self) -> str:
        """格式化通用的核心状态信息"""
        game_state = self.game_state_json.get('game_state',{})
        relics = ", ".join([r.get("name", "?") for r in game_state.get("relics", [])])
        return (
            f"### 核心状态\n"
            f"职业: {game_state.get('class', '?')} | 章节: {game_state.get('act', '?')} | 层数: {game_state.get('floor', '?')}\n"
            f"生命值: {game_state.get('current_hp', '?')}/{game_state.get('max_hp', '?')} | 金币: {game_state.get('gold', '?')}\n"
            f"遗物: {relics}\n"
        )

    def _format_combat_context(self) -> str:
        """格式化战斗场景的详细信息"""
        combat_state = self.game_state_json.get("combat_state", {})
        player = combat_state.get("player", {})
        hand = [f"{c.get('name', '?')} ({c.get('cost', '?')}费)" for c in combat_state.get("hand", [])]
        
        context = (
            f"能量: {player.get('energy', '?')}/3 | 格挡: {player.get('block', 0)}\n"
            f"手牌: {', '.join(hand)}\n"
            f"抽牌堆: {len(combat_state.get('draw_pile', []))}张 | 弃牌堆: {len(combat_state.get('discard_pile', []))}张\n"
            f"敌人状态:\n"
        )
        for m in combat_state.get("monsters", []):
            intent_desc = f"意图: {m.get('intent', '?')}"
            if m.get('intent', '').startswith("ATTACK"):
                intent_desc += f", 伤害: {m.get('move_adjusted_damage', '?')} x {m.get('move_hits', '?')}"
            context += f"- {m.get('name', '?')} (HP: {m.get('current_hp', '?')}, 格挡: {m.get('block', 0)}) -> {intent_desc}\n"
        return context

    def _format_card_reward_context(self) -> str:
        game_state = self.game_state_json.get('game_state', {})
        screen_state = game_state.get("screen_state", {})
        cards = [f"“{c.get('name', '?')}”" for c in screen_state.get("cards", [])]
        return f"可选卡牌: {', '.join(cards)}\n"
    
    def _format_map_context(self) -> str:
        game_state = self.game_state_json.get('game_state', {})
        map_data = game_state.get("map", [])
        player_node = game_state.get('current_node')
        next_nodes_info = game_state.get('screen_state', {}).get('next_nodes', [])

        context = "**地图分析:**\n"
        if player_node:
            context += f"你当前位于节点 (x={player_node['x']}, y={player_node['y']})。\n"
        
        if game_state.get('screen_state', {}).get('boss_available'):
            context += "你可以挑战本章节的Boss。\n"
        elif next_nodes_info:
            context += "你可以选择前往以下节点：\n"
            for node in next_nodes_info:
                full_node_info = next((item for item in map_data if item["x"] == node["x"] and item["y"] == node["y"]), None)
                symbol = full_node_info.get('symbol', '?') if full_node_info else '?'
                room_type_map = {"M": "怪物", "E": "精英", "$": "商店", "R": "休息处", "T": "宝箱", "?": "事件"}
                room_name = room_type_map.get(symbol, "未知")
                context += f"- 节点 (x={node['x']}, y={node['y']})，房间类型: **{room_name}**\n"
                
        return context

    def generate_prompt_from_state(self) -> str:
        game_state = self.game_state_json["game_state"]
        screen_type = game_state.get("screen_type", "NONE")
        if game_state.get("room_phase") == "COMBAT" and screen_type == "NONE":
            screen_type = "COMBAT"
        base_context = self._format_base_context()
        if screen_type == "COMBAT":
            prompt = COMBAT_PROMPT_TEMPLATE
            context = base_context + self._format_combat_context()
        elif screen_type == "MAP":
            prompt = MAP_PROMPT_TEMPLATE
            context = base_context + self._format_map_context()
        elif screen_type == "CARD_REWARD":
            prompt = CARD_REWARD_PROMPT_TEMPLATE
            context = base_context + self._format_card_reward_context()
        elif screen_type == "REST":
            prompt = REST_SITE_PROMPT_TEMPLATE
            context = base_context
        elif screen_type == "SHOP_SCREEN":
            prompt = SHOP_PROMPT_TEMPLATE
            context = base_context # 商店信息在choice_list里很清晰
        elif screen_type == "EVENT":
            prompt = EVENT_PROMPT_TEMPLATE
            context = base_context
        elif screen_type == "COMPLETE":
            prompt = COMPLETE_PROMPT_TEMPLATE
            context = base_context
        else: # EVENT, BOSS_REWARD, GRID, etc.
            prompt = GENERIC_PROMPT_TEMPLATE
            context = base_context

        choices = self.game_state_json.get("available_commands", [])
        if "choice_list" in game_state:
            choices = game_state["choice_list"]

        available_commands_list = "\n".join([f"- {c}" for c in choices])
        final_prompt = prompt + OUTPUT_FORMAT_TEMPLATE.format(
            contextual_game_state=context,
            available_commands_list=available_commands_list
        )
        log(f"Generated prompt:\n{final_prompt}")
        return final_prompt
if __name__ == '__main__':
    # 模拟一个战斗场景的JSON
    combat_state_example = {
        "in_game": True,
        "ready_for_command": True,
        "available_commands": ["play 1 0", "play 2", "end"],
        "game_state": {
            "class": "IRONCLAD", "act": 1, "floor": 3, "current_hp": 60, "max_hp": 80, "gold": 120,
            "relics": [{"name": "燃烧之血"}], "room_phase": "COMBAT", "screen_type": "NONE",
            "combat_state": {
                "player": {"energy": 3, "block": 5},
                "hand": [{"name": "打击", "cost": 1}, {"name": "防御", "cost": 1}],
                "monsters": [
                    {"name": "邪教徒", "current_hp": 48, "block": 0, "intent": "ATTACK", "move_adjusted_damage": 18, "move_hits": 1}
                ]
            }
        }
    }
    prompt_generator = PromptGenerator(combat_state_example)
    strict_prompt = prompt_generator.generate_prompt_from_state()
    print(strict_prompt)