import json
import os
from datetime import datetime
from typing import List, Dict, Any
from rs.helper.logger import log_to_run


class ActionConverter:
    """将LLM输出的动作JSON转换为游戏命令"""
    
    @staticmethod
    def convert_to_game_commands(action_json: str, game_state: Dict[Any, Any], debug_file: str = None) -> List[str]:
        """
        将LLM输出的动作JSON转换为游戏命令列表
        
        Args:
            action_json: LLM输出的动作JSON字符串
            game_state: 当前游戏状态，用于验证动作合法性
            debug_file: 调试文件路径，用于记录转换过程
            
        Returns:
            游戏命令字符串列表
        """
        try:
            action = json.loads(action_json)
            command = action.get("command", "").upper()
            result_commands = []
            
            if command == "PLAY":
                # 检查是否在战斗中
                gs = game_state.get("game_state", {})
                if "combat_state" in gs:
                    # 在战斗中，正常处理PLAY命令
                    result_commands = ActionConverter._convert_play_action(action, game_state)
                elif "choice_list" in gs:
                    log_to_run(f"PLAY command in non-combat context, converting to CHOOSE")
                    # 非战斗中，将PLAY命令转换为CHOOSE命令
                    choice_action = {"command": "CHOOSE", "choice_index": action.get("card_index", 0)}
                    result_commands = ActionConverter._convert_choose_action(choice_action, game_state)
                else:
                    log_to_run(f"PLAY command in invalid context, defaulting to END")
                    result_commands = ["end"]
            elif command == "END":
                result_commands = ["end"]
            elif command == "CHOOSE":
                # 非战斗中，正常处理CHOOSE命令
                result_commands = ActionConverter._convert_choose_action(action, game_state)
            elif command == "PROCEED":
                result_commands = ["proceed"]
            elif command == "RETURN":
                result_commands = ["return"]
            elif command == "POTION":
                result_commands = ActionConverter._convert_potion_action(action, game_state)
            else:
                # 智能回退: 尝试解析非标准但意图明确的格式
                if "choice" in action:
                    choice_str = action.get("choice")
                    log_to_run(f"检测到非标准'choice'键，值为'{choice_str}'。尝试匹配choice_list。")
                    
                    choice_list = game_state.get("game_state", {}).get("choice_list", [])
                    if choice_str in choice_list:
                        choice_index = choice_list.index(choice_str)
                        log_to_run(f"匹配成功！转换为 'choose {choice_index}'。")
                        result_commands = [f"choose {choice_index}"]
                    else:
                        log_to_run(f"'{choice_str}' 不在 choice_list 中，默认结束回合")
                        result_commands = ["end"]
                else:
                    log_to_run(f"未知或非法的命令格式: {action_json}, 默认结束回合")
                    result_commands = ["end"]
            
            if debug_file:
                ActionConverter._log_conversion_debug(debug_file, action_json, action, result_commands)
            
            return result_commands
                
        except json.JSONDecodeError as e:
            log_to_run(f"无效的JSON动作: {action_json}, 错误: {e}")
            # 修复上下文传递问题
            context_state = game_state if isinstance(game_state, dict) and "game_state" in game_state else {"game_state": game_state}
            context = ActionConverter.determine_context(context_state)
            log_to_run(f"使用上下文 '{context}' 进行智能回退。")
            if "选择" in context or "事件" in context or "地图" in context or "篝火" in context or "商店" in context:
                return ["choose 0"]
            return ["end"]
        except Exception as e:
            log_to_run(f"Error converting action: {e}")
            return ["end"]
    
    @staticmethod
    def _log_conversion_debug(debug_file: str, action_json: str, parsed_action: Dict[str, Any], result_commands: List[str]):
        """记录动作转换调试信息"""
        try:
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write("\n--- Action Conversion ---\n")
                f.write(f"  - Raw JSON: {action_json}\n")
                f.write(f"  - Parsed: {parsed_action}\n")
                f.write(f"  - => Commands: {result_commands}\n")
        except Exception as e:
            log_to_run(f"写入转换调试信息失败: {e}")
    
    @staticmethod 
    def _convert_play_action(action: Dict[str, Any], game_state: Dict[Any, Any]) -> List[str]:
        """转换PLAY动作"""
        try:
            # 修复数据类型不一致问题
            card_index = action.get("card_index", 0)
            target_index = action.get("target_index")
            
            # 确保索引是整数类型
            try:
                card_index = int(card_index)
                if target_index is not None:
                    target_index = int(target_index)
            except (ValueError, TypeError) as e:
                log_to_run(f"索引类型转换失败: {e}")
                return ["end"]
            
            # 验证卡牌索引有效性 (LLM使用0-indexed)
            if ActionConverter._is_valid_card_index(card_index, game_state):
                # Communication Mod需要1-indexed的卡牌索引
                game_card_index = card_index + 1
                
                if target_index is not None:
                    # 验证目标索引有效性 (目标索引保持0-indexed)
                    if ActionConverter._is_valid_target_index(target_index, game_state):
                        return [f"play {game_card_index} {target_index}"]
                    else:
                        log_to_run(f"Invalid target index: {target_index}")
                        return [f"play {game_card_index}"]
                else:
                    return [f"play {game_card_index}"]
            else:
                log_to_run(f"Invalid card index: {card_index}")
                return ["end"]
                
        except Exception as e:
            log_to_run(f"Error in play action conversion: {e}")
            return ["end"]
    
    @staticmethod
    def _convert_choose_action(action: Dict[str, Any], game_state: Dict[Any, Any]) -> List[str]:
        """
        转换CHOOSE动作，并对LLM可能混淆'值'和'索引'的错误进行智能修正。
        """
        try:
            choice_index = action.get("choice_index", 0)
            
            # 确保索引是整数类型
            try:
                choice_index = int(choice_index)
            except (ValueError, TypeError) as e:
                log_to_run(f"选择索引类型转换失败: {e}, 使用默认值0")
                choice_index = 0
            
            # 验证选择索引是否有效
            if ActionConverter._is_valid_choice_index(choice_index, game_state):
                return [f"choose {choice_index}"]
            
            # 如果索引无效，启动智能修正逻辑
            log_to_run(f"无效的选择索引: {choice_index}。启动智能修正...")
            choice_list = game_state.get("game_state", {}).get("choice_list", [])
            
            # 尝试将无效索引作为值，在选项文本中进行匹配
            # 例如, choice_index=5, choice_list=["x=0", "x=3", "x=5"] -> 匹配 "x=5"
            value_to_find = str(choice_index)
            for i, choice_text in enumerate(choice_list):
                # 使用正则表达式确保我们匹配的是完整的数字
                import re
                if re.search(r'\b' + re.escape(value_to_find) + r'\b', choice_text):
                    log_to_run(f"智能修正成功！发现 '{value_to_find}' 在选项 '{choice_text}' (索引 {i}) 中。")
                    return [f"choose {i}"]

            # 如果所有尝试都失败，才回退到默认值
            log_to_run(f"智能修正失败。回退到默认选择: choose 0")
            return ["choose 0"]
                
        except Exception as e:
            log_to_run(f"Error in choose action conversion: {e}")
            return ["choose 0"]
    
    @staticmethod
    def _convert_potion_action(action: Dict[str, Any], game_state: Dict[Any, Any]) -> List[str]:
        """转换POTION动作"""
        try:
            # AI 使用 0-indexed 的 potion_index
            potion_index = action.get("potion_index", 0)
            target_index = action.get("target_index")

            # 验证药水索引
            if not ActionConverter._is_valid_potion_index(potion_index, game_state):
                 log_to_run(f"Invalid or unusable potion index: {potion_index}")
                 return ["end"] # 如果药水不可用或索引无效，则结束回合
            
            # Communication Mod 需要基于槽位的命令: `potion use <slot>`
            potions = game_state.get("game_state", {}).get("potions", [])
            # 我们需要将 AI 的索引（在所有药水中的索引）映射到实际的槽位(slot)
            if potion_index < len(potions):
                potion_slot = potions[potion_index].get("slot")
                
                # 检查药水是否需要目标
                requires_target = potions[potion_index].get("requires_target", False)

                if requires_target:
                    if target_index is not None and ActionConverter._is_valid_target_index(target_index, game_state):
                        return [f"potion use {potion_slot} {target_index}"]
                    else:
                        # 如果需要目标但没有提供有效目标，则是一个无效动作
                        log_to_run(f"Potion at index {potion_index} requires a target, but a valid one was not provided.")
                        return ["end"] 
                else:
                    return [f"potion use {potion_slot}"]

            log_to_run(f"Could not find a valid slot for potion index: {potion_index}")
            return ["end"] # 找不到药水，结束回合
                
        except Exception as e:
            log_to_run(f"Error in potion action conversion: {e}")
            return ["end"]
    
    @staticmethod
    def _is_valid_card_index(card_index: int, game_state: Dict[Any, Any]) -> bool:
        """验证卡牌索引是否有效"""
        try:
            # 类型检查
            if not isinstance(card_index, int):
                return False
                
            if "combat_state" not in game_state.get("game_state", {}):
                return False
            
            hand = game_state["game_state"]["combat_state"].get("hand", [])
            return 0 <= card_index < len(hand)
        except (KeyError, TypeError, AttributeError):
            return False
    
    @staticmethod
    def _is_valid_target_index(target_index: int, game_state: Dict[Any, Any]) -> bool:
        """验证目标索引是否有效"""
        try:
            # 类型检查
            if not isinstance(target_index, int):
                return False
                
            if "combat_state" not in game_state.get("game_state", {}):
                return False
            
            monsters = game_state["game_state"]["combat_state"].get("monsters", [])
            return 0 <= target_index < len(monsters)
        except (KeyError, TypeError, AttributeError):
            return False
    
    @staticmethod
    def _is_valid_choice_index(choice_index: int, game_state: Dict[Any, Any]) -> bool:
        """验证选择索引是否有效"""
        try:
            # 类型检查
            if not isinstance(choice_index, int):
                return False
                
            choice_list = game_state.get("game_state", {}).get("choice_list", [])
            return 0 <= choice_index < len(choice_list)
        except (KeyError, TypeError, AttributeError):
            return False
    
    @staticmethod
    def _is_valid_potion_index(potion_index: int, game_state: Dict[Any, Any]) -> bool:
        """验证药水索引是否有效且可用"""
        try:
            if not isinstance(potion_index, int):
                return False
            
            potions = game_state.get("game_state", {}).get("potions", [])
            if 0 <= potion_index < len(potions):
                # 额外检查药水是否真的可以使用
                return potions[potion_index].get("can_use", False)
            return False
        except (KeyError, TypeError, AttributeError):
            return False
    
    @staticmethod
    def determine_context(game_state: Dict[Any, Any]) -> str:
        """根据游戏状态确定当前情境 - 增强版本"""
        try:
            gs = game_state.get("game_state", {})
            screen_type = gs.get("screen_type", "")
            room_type = gs.get("room_type", "")
            
            # 详细的状态匹配逻辑
            if "combat_state" in gs:
                return "战斗中 - 选择打出手牌或结束回合"
            elif screen_type == "CARD_REWARD":
                return "选择卡牌奖励"
            elif screen_type == "SHOP_ROOM" or screen_type == "SHOP":
                return "商店 - 购买物品"
            elif screen_type == "MAP":
                return "地图 - 选择下一个房间"
            elif screen_type == "EVENT" or screen_type == "EVENT_ROOM":
                return "事件 - 做出选择"
            elif room_type == "RestSite" or screen_type == "REST":
                return "篝火 - 选择休息或升级"
            elif room_type == "TreasureRoom" or screen_type == "TREASURE":
                return "宝箱房间"
            elif room_type == "EliteRoom":
                return "精英战斗房间"
            elif room_type == "MonsterRoom":
                return "普通战斗房间"
            elif room_type == "NeowRoom":
                return "事件 - 做出选择"
            elif screen_type == "HAND_SELECT":
                return "选择手牌"
            elif screen_type == "GRID":
                return "网格选择"
            elif screen_type == "BOSS_REWARD":
                return "Boss奖励选择"
            elif screen_type == "RELIC":
                return "遗物选择"
            elif "choice_list" in gs and gs["choice_list"]:
                choice_count = len(gs["choice_list"])
                return f"做出选择 ({choice_count}个选项)"
            elif "cards" in gs:
                return "卡牌相关选择"
            elif "relics" in gs:
                return "遗物相关选择"
            else:
                # 提供更多调试信息
                available_keys = list(gs.keys())
                return f"游戏进行中 (可用字段: {available_keys[:3]}...)"
                
        except Exception as e:
            log_to_run(f"Error determining context: {e}")
            return "游戏进行中 (上下文解析错误)" 