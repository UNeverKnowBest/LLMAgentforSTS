#!/usr/bin/env python3

import json
import sys
from typing import Dict, Any, List
from src.graph.nodes import (
    advice_on_command,
    validate_command, 
    handle_validation_failure,
    generate_fallback_command
)
from src.graph.states import GameState
from src.prompts.prompt_generator import PromptGenerator

class GameStateTestSuite:
    """
    基于CommunicationMod的真实游戏状态的comprehensive测试套件
    游戏状态数据基于GameStateConverter.java的结构
    """
    
    def __init__(self):
        self.test_cases = self._create_realistic_game_states()
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def _create_realistic_game_states(self) -> Dict[str, Dict[str, Any]]:
        """
        基于原mod GameStateConverter.java 创建真实的游戏状态样本
        包含各种不同的游戏场景
        """
        return {
            "combat_early_game": {
                "available_commands": ["play", "end", "potion", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "NONE",
                    "is_screen_up": False,
                    "screen_type": "COMBAT",
                    "room_phase": "COMBAT",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 72,
                    "max_hp": 80,
                    "floor": 3,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 124,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [
                        {
                            "id": "Burning Blood",
                            "name": "Burning Blood",
                            "counter": -1
                        },
                        {
                            "id": "Vajra",
                            "name": "Vajra",
                            "counter": -1
                        }
                    ],
                    "deck": [
                        {
                            "id": "Strike_R",
                            "name": "Strike",
                            "cost": 1,
                            "rarity": "BASIC",
                            "type": "ATTACK",
                            "upgrades": 0,
                            "uuid": "uuid-strike-1",
                            "is_playable": True,
                            "has_target": True,
                            "exhausts": False,
                            "ethereal": False,
                            "misc": 0
                        },
                        {
                            "id": "Defend_R",
                            "name": "Defend",
                            "cost": 1,
                            "rarity": "BASIC",
                            "type": "SKILL",
                            "upgrades": 1,
                            "uuid": "uuid-defend-1",
                            "is_playable": True,
                            "has_target": False,
                            "exhausts": False,
                            "ethereal": False,
                            "misc": 0
                        },
                        {
                            "id": "Bash",
                            "name": "Bash",
                            "cost": 2,
                            "rarity": "BASIC",
                            "type": "ATTACK",
                            "upgrades": 0,
                            "uuid": "uuid-bash-1",
                            "is_playable": True,
                            "has_target": True,
                            "exhausts": False,
                            "ethereal": False,
                            "misc": 0
                        }
                    ],
                    "potions": [
                        {
                            "id": "Fire Potion",
                            "name": "Fire Potion",
                            "can_use": True,
                            "can_discard": True,
                            "requires_target": True
                        },
                        {
                            "id": "PotionSlot",
                            "name": "Potion Slot",
                            "can_use": False,
                            "can_discard": False,
                            "requires_target": False
                        },
                        {
                            "id": "PotionSlot",
                            "name": "Potion Slot",
                            "can_use": False,
                            "can_discard": False,
                            "requires_target": False
                        }
                    ],
                    "keys": {
                        "ruby": False,
                        "emerald": False,
                        "sapphire": False
                    },
                    "combat_state": {
                        "turn": 1,
                        "cards_discarded_this_turn": 0,
                        "times_damaged": 0,
                        "player": {
                            "current_hp": 72,
                            "max_hp": 80,
                            "block": 0,
                            "energy": 3,
                            "orbs": [],
                            "powers": [
                                {
                                    "id": "Strength",
                                    "name": "Strength",
                                    "amount": 1,
                                    "damage": 0,
                                    "misc": 0,
                                    "just_applied": False
                                }
                            ]
                        },
                        "monsters": [
                            {
                                "id": "Cultist",
                                "name": "Cultist",
                                "current_hp": 48,
                                "max_hp": 48,
                                "block": 0,
                                "intent": "ATTACK",
                                "is_gone": False,
                                "half_dead": False,
                                "move_id": 1,
                                "move_base_damage": 6,
                                "move_adjusted_damage": 6,
                                "move_hits": 1,
                                "last_move_id": -1,
                                "second_last_move_id": -1,
                                "powers": []
                            }
                        ],
                        "draw_pile": [
                            {
                                "id": "Strike_R",
                                "name": "Strike",
                                "cost": 1,
                                "is_playable": True
                            },
                            {
                                "id": "Strike_R",
                                "name": "Strike",
                                "cost": 1,
                                "is_playable": True
                            }
                        ],
                        "discard_pile": [],
                        "exhaust_pile": [],
                        "hand": [
                            {
                                "id": "Strike_R",
                                "name": "Strike",
                                "cost": 1,
                                "rarity": "BASIC",
                                "type": "ATTACK",
                                "upgrades": 0,
                                "uuid": "uuid-strike-hand-1",
                                "is_playable": True,
                                "has_target": True,
                                "exhausts": False,
                                "ethereal": False
                            },
                            {
                                "id": "Defend_R",
                                "name": "Defend+",
                                "cost": 1,
                                "rarity": "BASIC",
                                "type": "SKILL",
                                "upgrades": 1,
                                "uuid": "uuid-defend-hand-1",
                                "is_playable": True,
                                "has_target": False,
                                "exhausts": False,
                                "ethereal": False
                            },
                            {
                                "id": "Bash",
                                "name": "Bash",
                                "cost": 2,
                                "rarity": "BASIC",
                                "type": "ATTACK",
                                "upgrades": 0,
                                "uuid": "uuid-bash-hand-1",
                                "is_playable": True,
                                "has_target": True,
                                "exhausts": False,
                                "ethereal": False
                            }
                        ],
                        "limbo": []
                    },
                    "screen_state": {}
                }
            },
            
            "card_reward_screen": {
                "available_commands": ["choose", "skip", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "CARD_REWARD",
                    "is_screen_up": True,
                    "screen_type": "CARD_REWARD",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 65,
                    "max_hp": 80,
                    "floor": 3,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 134,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [
                        {
                            "id": "Burning Blood",
                            "name": "Burning Blood",
                            "counter": -1
                        }
                    ],
                    "deck": [
                        {
                            "id": "Strike_R",
                            "name": "Strike",
                            "cost": 1,
                            "rarity": "BASIC",
                            "type": "ATTACK",
                            "upgrades": 0,
                            "uuid": "uuid-strike-1",
                            "is_playable": True,
                            "has_target": True,
                            "exhausts": False,
                            "ethereal": False
                        }
                    ],
                    "potions": [
                        {
                            "id": "PotionSlot",
                            "name": "Potion Slot",
                            "can_use": False,
                            "can_discard": False,
                            "requires_target": False
                        }
                    ],
                    "keys": {
                        "ruby": False,
                        "emerald": False,
                        "sapphire": False
                    },
                    "choice_list": ["0", "1", "2", "skip"],
                    "screen_state": {
                        "bowl_available": False,
                        "skip_available": True,
                        "cards": [
                            {
                                "id": "Inflame",
                                "name": "Inflame",
                                "cost": 1,
                                "rarity": "COMMON",
                                "type": "POWER",
                                "upgrades": 0,
                                "uuid": "uuid-inflame-reward",
                                "is_playable": True,
                                "has_target": False,
                                "exhausts": False,
                                "ethereal": False
                            },
                            {
                                "id": "Iron Wave",
                                "name": "Iron Wave",
                                "cost": 1,
                                "rarity": "COMMON",
                                "type": "ATTACK",
                                "upgrades": 0,
                                "uuid": "uuid-ironwave-reward",
                                "is_playable": True,
                                "has_target": True,
                                "exhausts": False,
                                "ethereal": False
                            },
                            {
                                "id": "True Grit",
                                "name": "True Grit",
                                "cost": 1,
                                "rarity": "COMMON",
                                "type": "SKILL",
                                "upgrades": 0,
                                "uuid": "uuid-truegrit-reward",
                                "is_playable": True,
                                "has_target": False,
                                "exhausts": False,
                                "ethereal": False
                            }
                        ]
                    }
                }
            },
            
            "shop_screen": {
                "available_commands": ["choose", "leave", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "SHOP",
                    "is_screen_up": True,
                    "screen_type": "SHOP_SCREEN",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "ShopRoom",
                    "current_hp": 65,
                    "max_hp": 80,
                    "floor": 6,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 234,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [
                        {
                            "id": "Burning Blood",
                            "name": "Burning Blood",
                            "counter": -1
                        }
                    ],
                    "deck": [],
                    "potions": [],
                    "keys": {
                        "ruby": False,
                        "emerald": False,
                        "sapphire": False
                    },
                    "choice_list": ["card 0", "card 1", "relic 0", "potion 0", "purge", "leave"],
                    "screen_state": {
                        "cards": [
                            {
                                "id": "Headbutt",
                                "name": "Headbutt",
                                "cost": 1,
                                "price": 48,
                                "rarity": "COMMON",
                                "type": "ATTACK"
                            },
                            {
                                "id": "Shrug It Off",
                                "name": "Shrug It Off",
                                "cost": 1,
                                "price": 52,
                                "rarity": "COMMON", 
                                "type": "SKILL"
                            }
                        ],
                        "relics": [
                            {
                                "id": "Art of War",
                                "name": "Art of War",
                                "price": 300,
                                "counter": -1
                            }
                        ],
                        "potions": [
                            {
                                "id": "Strength Potion",
                                "name": "Strength Potion",
                                "price": 50,
                                "can_use": True,
                                "can_discard": True,
                                "requires_target": False
                            }
                        ],
                        "purge_available": True,
                        "purge_cost": 75
                    }
                }
            },
            
            "map_screen": {
                "available_commands": ["choose", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "MAP",
                    "is_screen_up": True,
                    "screen_type": "MAP",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 65,
                    "max_hp": 80,
                    "floor": 7,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 184,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [],
                    "deck": [],
                    "potions": [],
                    "keys": {
                        "ruby": False,
                        "emerald": False,
                        "sapphire": False
                    },
                    "choice_list": ["0", "1"],
                    "screen_state": {
                        "current_node": {
                            "x": 3,
                            "y": 6,
                            "symbol": "M"
                        },
                        "next_nodes": [
                            {
                                "x": 2,
                                "y": 7,
                                "symbol": "?"
                            },
                            {
                                "x": 4,
                                "y": 7,
                                "symbol": "$"
                            }
                        ],
                        "first_node_chosen": True,
                        "boss_available": False
                    }
                }
            },
            
            "event_screen": {
                "available_commands": ["choose", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "EVENT",
                    "is_screen_up": True,
                    "screen_type": "EVENT",
                    "room_phase": "EVENT",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "EventRoom",
                    "current_hp": 45,
                    "max_hp": 80,
                    "floor": 8,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 184,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [],
                    "deck": [],
                    "potions": [],
                    "keys": {
                        "ruby": False,
                        "emerald": False,
                        "sapphire": False
                    },
                    "choice_list": ["0", "1", "2"],
                    "screen_state": {
                        "body_text": "A strange shrine sits before you. Do you make an offering?",
                        "event_name": "Golden Shrine",
                        "event_id": "Golden Shrine",
                        "options": [
                            {
                                "text": "[Pray] Gain 1 Max HP.",
                                "disabled": False,
                                "label": "Pray",
                                "choice_index": 0
                            },
                            {
                                "text": "[Donate] Lose 25 Gold. Gain 2 Max HP.",
                                "disabled": False,
                                "label": "Donate", 
                                "choice_index": 1
                            },
                            {
                                "text": "[Leave] Nothing happens.",
                                "disabled": False,
                                "label": "Leave",
                                "choice_index": 2
                            }
                        ]
                    }
                }
            },
            
            "game_over_victory": {
                "available_commands": ["proceed", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "VICTORY",
                    "is_screen_up": True,
                    "screen_type": "GAME_OVER",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "VictoryRoom",
                    "current_hp": 1,
                    "max_hp": 80,
                    "floor": 55,
                    "act": 4,
                    "act_boss": "The Heart",
                    "gold": 999,
                    "seed": 1234567890123,
                    "class": "IRONCLAD",
                    "ascension_level": 20,
                    "relics": [
                        {
                            "id": "Ruby Key",
                            "name": "Ruby Key",
                            "counter": -1
                        },
                        {
                            "id": "Emerald Key",
                            "name": "Emerald Key", 
                            "counter": -1
                        },
                        {
                            "id": "Sapphire Key",
                            "name": "Sapphire Key",
                            "counter": -1
                        }
                    ],
                    "deck": [],
                    "potions": [],
                    "keys": {
                        "ruby": True,
                        "emerald": True,
                        "sapphire": True
                    },
                    "screen_state": {
                        "score": 1523,
                        "victory": True
                    }
                }
            },
            
            "rest_screen": {
                "available_commands": ["choose", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "REST",
                    "is_screen_up": True,
                    "screen_type": "REST",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "RestRoom",
                    "current_hp": 35,
                    "max_hp": 80,
                    "floor": 9,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 150,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [],
                    "deck": [],
                    "potions": [],
                    "keys": {"ruby": False, "emerald": False, "sapphire": False},
                    "choice_list": ["rest", "smith"],
                    "screen_state": {
                        "rest_available": True,
                        "smith_available": True,
                        "recall_available": False,
                        "lift_available": False,
                        "toke_available": False,
                        "dig_available": False
                    }
                }
            },

            "grid_select_screen": {
                "available_commands": ["choose", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "Grid Card Select",
                    "is_screen_up": True,
                    "screen_type": "GRID",
                    "room_phase": "COMBAT",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 50,
                    "max_hp": 80,
                    "floor": 10,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 150,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [],
                    "deck": [],
                    "potions": [],
                    "keys": {"ruby": False, "emerald": False, "sapphire": False},
                    "choice_list": ["0", "1", "2"],
                    "screen_state": {
                        "num_cards": 1,
                        "min_cards": 1,
                        "max_cards": 1,
                        "any_number": False,
                        "for_upgrade": False,
                        "for_transform": False,
                        "for_purge": False,
                        "confirm_up": False,
                        "bowl_available": False,
                        "is_discovery": True,
                        "cards": [
                            {"id": "Armaments", "name": "Armaments", "cost": 1, "rarity": "COMMON", "type": "SKILL"},
                            {"id": "Flex", "name": "Flex", "cost": 0, "rarity": "COMMON", "type": "SKILL"},
                            {"id": "Heavy Blade", "name": "Heavy Blade", "cost": 2, "rarity": "COMMON", "type": "ATTACK"}
                        ]
                    }
                }
            },
            
            "game_over_defeat": {
                "available_commands": ["proceed", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "DEFEAT",
                    "is_screen_up": True,
                    "screen_type": "GAME_OVER",
                    "room_phase": "COMPLETE",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 0,
                    "max_hp": 80,
                    "floor": 11,
                    "act": 1,
                    "act_boss": "Hexaghost",
                    "gold": 200,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [],
                    "deck": [],
                    "potions": [],
                    "keys": {"ruby": False, "emerald": False, "sapphire": False},
                    "screen_state": {
                        "score": 450,
                        "victory": False
                    }
                }
            },

            "combat_mid_game": {
                "available_commands": ["play", "end", "potion", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_name": "NONE",
                    "is_screen_up": False,
                    "screen_type": "COMBAT",
                    "room_phase": "COMBAT",
                    "action_phase": "WAITING_FOR_USER_INPUT",
                    "room_type": "MonsterRoom",
                    "current_hp": 45,
                    "max_hp": 85,
                    "floor": 25,
                    "act": 2,
                    "act_boss": "The Champ",
                    "gold": 300,
                    "class": "IRONCLAD",
                    "ascension_level": 15,
                    "relics": [
                        {"id": "Burning Blood", "name": "Burning Blood", "counter": -1},
                        {"id": "Orichalcum", "name": "Orichalcum", "counter": -1},
                        {"id": "Pen Nib", "name": "Pen Nib", "counter": 8}
                    ],
                    "deck": [],
                    "potions": [{"id": "FearPotion", "name": "Fear Potion", "can_use": True, "can_discard": True, "requires_target": True}],
                    "keys": {"ruby": False, "emerald": False, "sapphire": False},
                    "combat_state": {
                        "turn": 3,
                        "player": {
                            "current_hp": 45, "max_hp": 85, "block": 6, "energy": 3, "orbs": [],
                            "powers": [{"id": "Metallicize", "name": "Metallicize", "amount": 4}]
                        },
                        "monsters": [
                            {
                                "id": "SlaverBlue", "name": "Slaver (Blue)", "current_hp": 25, "max_hp": 46, "block": 0,
                                "intent": "ATTACK_DEBUFF", "move_id": 2, "move_base_damage": 8
                            },
                            {
                                "id": "SlaverRed", "name": "Slaver (Red)", "current_hp": 30, "max_hp": 46, "block": 5,
                                "intent": "ATTACK", "move_id": 3, "move_base_damage": 13
                            }
                        ],
                        "hand": [
                            {"id": "Strike_R", "name": "Strike", "cost": 1, "is_playable": True, "has_target": True},
                            {"id": "Defend_R", "name": "Defend", "cost": 1, "is_playable": True, "has_target": False},
                            {"id": "Body Slam", "name": "Body Slam+", "cost": 0, "upgrades": 1, "is_playable": True, "has_target": True}
                        ],
                        "draw_pile": [],
                        "discard_pile": [],
                        "exhaust_pile": []
                    },
                    "screen_state": {}
                }
            }
        }
    
    def run_test_case(self, name: str, game_state_data: Dict[str, Any]) -> bool:
        """
        运行单个测试用例，验证项目的各个组件
        """
        print(f"\n🔍 测试场景: {name}")
        print(f"   屏幕类型: {game_state_data['game_state']['screen_type']}")
        print(f"   楼层: {game_state_data['game_state']['floor']}")
        print(f"   生命值: {game_state_data['game_state']['current_hp']}/{game_state_data['game_state']['max_hp']}")
        
        try:
            # 1. 测试提示生成器 (供后续步骤使用)
            prompt_generator = PromptGenerator(game_state_data)

            # 2. 通过 advice_on_command 节点测试提示生成和LLM集成
            state = GameState(game_state_json=game_state_data)
            advice_result = advice_on_command(state)
            final_command = advice_result.get("final_command", "state")

            if "thinking_process" in advice_result and advice_result["thinking_process"]:
                print(f"   ✅ LLM 已响应，获得命令: {final_command}")
            else:
                print(f"   ✅ 获得简单命令: {final_command}")

            # 3. 测试命令验证
            state.final_command = final_command
            
            validation_result = validate_command(state)
            is_valid = validation_result["validation_result"]["is_valid"]
            
            if is_valid:
                print(f"   ✅ 命令验证通过: {final_command}")
            else:
                errors = validation_result["validation_result"]["errors"]
                print(f"   ❌ 命令验证失败: {final_command}")
                print(f"       错误: {errors}")
                
                # 4. 测试失败处理
                state.validation_result = validation_result["validation_result"]
                fallback_result = handle_validation_failure(state)
                fallback_command = fallback_result["fallback_command"]
                print(f"   🔄 使用后备命令: {fallback_command}")
            
            # 5. 测试屏幕类型识别
            screen_type = prompt_generator.get_screen_type()
            print(f"   ✅ 屏幕类型识别: {screen_type.value}")
            
            # 6. 测试可用命令
            available_commands = prompt_generator.get_available_commands()
            print(f"   ✅ 可用命令: {available_commands}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["errors"].append(f"{name}: {e}")
            return False
    
    def run_all_tests(self):
        """
        运行所有测试用例
        """
        print("🚀 开始CommunicationMod游戏状态Comprehensive测试")
        print("=" * 80)
        
        for name, game_state_data in self.test_cases.items():
            if self.run_test_case(name, game_state_data):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        
        # 输出测试结果
        print("\n" + "=" * 80)
        print("📊 测试结果汇总")
        print(f"   ✅ 通过: {self.results['passed']}")
        print(f"   ❌ 失败: {self.results['failed']}")
        print(f"   📈 成功率: {self.results['passed']/(self.results['passed']+self.results['failed'])*100:.1f}%")
        
        if self.results["errors"]:
            print("\n🐛 错误详情:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        print("\n🎯 测试完成!")
        
        # 额外的数据验证测试
        self._validate_json_structures()
    
    def _validate_json_structures(self):
        """
        验证JSON结构是否符合原mod规范
        """
        print("\n🔍 验证JSON结构符合CommunicationMod规范...")
        
        required_top_level = ["available_commands", "ready_for_command", "in_game", "game_state"]
        required_game_state = ["screen_type", "current_hp", "max_hp", "floor", "act", "gold", "class"]
        
        for name, data in self.test_cases.items():
            # 验证顶级结构
            for field in required_top_level:
                if field not in data:
                    print(f"   ❌ {name}: 缺少顶级字段 {field}")
                    continue
            
            # 验证游戏状态结构
            game_state = data.get("game_state", {})
            for field in required_game_state:
                if field not in game_state:
                    print(f"   ❌ {name}: 缺少游戏状态字段 {field}")
                    continue
        
        print("   ✅ JSON结构验证完成")

def main():
    """
    主函数：运行comprehensive测试套件
    """
    test_suite = GameStateTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main() 