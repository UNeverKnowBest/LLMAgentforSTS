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
from .logger import log_debug, log_info, log_error, log_function_call


class PromptGenerator:
    """Generate the prompt based on the current game state info"""
    
    @log_function_call
    def __init__(self, game_state_json: Dict[Any, Any]):
        self.game_state_json = game_state_json
        log_debug("初始化提示生成器", 
                 state_keys=list(game_state_json.keys()),
                 game_state_present='game_state' in game_state_json)

    def _format_base_context(self) -> str:
        """格式化通用的核心状态信息"""
        try:
            game_state = self.game_state_json.get('game_state',{})
            relics = ", ".join([r.get("name", "?") for r in game_state.get("relics", [])])
            
            context = (
                f"### 核心状态\n"
                f"职业: {game_state.get('class', '?')} | 章节: {game_state.get('act', '?')} | 层数: {game_state.get('floor', '?')}\n"
                f"生命值: {game_state.get('current_hp', '?')}/{game_state.get('max_hp', '?')} | 金币: {game_state.get('gold', '?')}\n"
                f"遗物: {relics}\n"
            )
            
            log_debug("格式化基础上下文完成", 
                     class_name=game_state.get('class', '?'),
                     floor=game_state.get('floor', '?'),
                     relics_count=len(game_state.get("relics", [])))
            
            return context
        except Exception as e:
            log_error("格式化基础上下文时发生错误", exception=e)
            return "### 核心状态\n[状态信息获取失败]\n"

    def _format_combat_context(self) -> str:
        """格式化战斗场景的详细信息"""
        try:
            combat_state = self.game_state_json.get("combat_state", {})
            player = combat_state.get("player", {})
            hand = [f"{c.get('name', '?')} ({c.get('cost', '?')}费)" for c in combat_state.get("hand", [])]
            
            context = (
                f"能量: {player.get('energy', '?')}/3 | 格挡: {player.get('block', 0)}\n"
                f"手牌: {', '.join(hand)}\n"
                f"抽牌堆: {len(combat_state.get('draw_pile', []))}张 | 弃牌堆: {len(combat_state.get('discard_pile', []))}张\n"
                f"敌人状态:\n"
            )
            
            monsters = combat_state.get("monsters", [])
            for m in monsters:
                intent_desc = f"意图: {m.get('intent', '?')}"
                if m.get('intent', '').startswith("ATTACK"):
                    intent_desc += f", 伤害: {m.get('move_adjusted_damage', '?')} x {m.get('move_hits', '?')}"
                context += f"- {m.get('name', '?')} (HP: {m.get('current_hp', '?')}, 格挡: {m.get('block', 0)}) -> {intent_desc}\n"
            
            log_debug("格式化战斗上下文完成",
                     hand_size=len(hand),
                     monsters_count=len(monsters),
                     player_energy=player.get('energy', '?'))
            
            return context
        except Exception as e:
            log_error("格式化战斗上下文时发生错误", exception=e)
            return "[战斗信息获取失败]\n"

    def _format_card_reward_context(self) -> str:
        try:
            game_state = self.game_state_json.get('game_state', {})
            screen_state = game_state.get("screen_state", {})
            cards = [f'"{c.get("name", "?")}"' for c in screen_state.get("cards", [])]
            
            context = f"可选卡牌: {', '.join(cards)}\n"
            log_debug("格式化卡牌奖励上下文完成", cards_count=len(cards))
            return context
        except Exception as e:
            log_error("格式化卡牌奖励上下文时发生错误", exception=e)
            return "[卡牌奖励信息获取失败]\n"
    
    def _format_map_context(self) -> str:
        try:
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
            
            log_debug("格式化地图上下文完成",
                     current_node=f"({player_node['x']}, {player_node['y']})" if player_node else "未知",
                     next_nodes_count=len(next_nodes_info),
                     boss_available=game_state.get('screen_state', {}).get('boss_available', False))
            
            return context
        except Exception as e:
            log_error("格式化地图上下文时发生错误", exception=e)
            return "[地图信息获取失败]\n"

    @log_function_call
    def generate_prompt_from_state(self) -> str:
        try:
            game_state = self.game_state_json["game_state"]
            screen_type = game_state.get("screen_type", "NONE")
            if game_state.get("room_phase") == "COMBAT" and screen_type == "NONE":
                screen_type = "COMBAT"
            
            log_debug("开始生成提示",
                     screen_type=screen_type,
                     room_phase=game_state.get("room_phase", "UNKNOWN"))
            
            base_context = self._format_base_context()
            
            # 根据屏幕类型选择合适的模板
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
            
            log_info("提示生成完成",
                    screen_type=screen_type,
                    prompt_length=len(final_prompt),
                    commands_count=len(choices),
                    context_length=len(context))
            
            log_debug("完整提示内容", prompt_preview=final_prompt[:300] + "..." if len(final_prompt) > 300 else final_prompt)
            
            return final_prompt
            
        except Exception as e:
            log_error("生成提示时发生严重错误", exception=e)
            # 返回一个基本的错误提示
            return "发生错误，无法生成完整提示。请检查游戏状态。"