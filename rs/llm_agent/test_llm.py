#!/usr/bin/env python3
"""
LLM Agent测试文件
测试Ollama连接和模拟游戏状态处理
"""

import json
from rs.llm_agent.llm_client import LLMClient
from rs.llm_agent.action_converter import ActionConverter


def test_ollama_connection():
    """测试Ollama连接"""
    print("=== 测试Ollama连接 ===")
    
    llm_client = LLMClient()
    
    if llm_client.test_connection():
        print("✓ Ollama连接成功")
        return True
    else:
        print("✗ Ollama连接失败")
        print("请确保:")
        print("1. Ollama已安装并运行在 http://localhost:11434")
        print("2. qwen3:4b 模型已下载 (运行: ollama pull qwen3:4b)")
        return False


def test_llm_with_mock_game_state():
    """使用模拟游戏状态测试LLM"""
    print("\n=== 测试LLM游戏状态处理 ===")
    
    # 模拟战斗状态JSON (基于README示例简化)
    mock_combat_state = {
        "available_commands": ["play", "end", "wait"],
        "ready_for_command": True,
        "in_game": True,
        "game_state": {
            "screen_type": "NONE",
            "screen_state": {},
            "combat_state": {
                "hand": [
                    {
                        "name": "Strike",
                        "id": "Strike_R",
                        "cost": 1,
                        "type": "ATTACK",
                        "has_target": True,
                        "is_playable": True
                    },
                    {
                        "name": "Defend", 
                        "id": "Defend_R",
                        "cost": 1,
                        "type": "SKILL",
                        "has_target": False,
                        "is_playable": True
                    },
                    {
                        "name": "Bash",
                        "id": "Bash",
                        "cost": 2,
                        "type": "ATTACK", 
                        "has_target": True,
                        "is_playable": True
                    }
                ],
                "monsters": [
                    {
                        "name": "Jaw Worm",
                        "current_hp": 1,
                        "max_hp": 46,
                        "intent": "DEBUG",
                        "is_gone": False
                    }
                ],
                "player": {
                    "current_hp": 68,
                    "max_hp": 75,
                    "energy": 3,
                    "block": 0
                },
                "turn": 1
            },
            "room_type": "MonsterRoom"
        }
    }
    
    # 模拟选择状态JSON
    mock_choice_state = {
        "available_commands": ["choose", "proceed"],
        "ready_for_command": True,
        "in_game": True,
        "game_state": {
            "screen_type": "CARD_REWARD",
            "choice_list": ["Strike+", "Defend+", "Iron Wave"],
            "room_type": "MonsterRoom"
        }
    }
    
    # 启用调试输出的LLM客户端
    llm_client = LLMClient(enable_debug_output=True)
    
    print("1. 测试战斗状态处理...")
    context1 = ActionConverter.determine_context(mock_combat_state)
    print(f"   检测到的情境: {context1}")
    
    action1 = llm_client.generate_action(mock_combat_state, context1)
    print(f"   LLM生成的动作: {action1}")
    
    # 传递调试文件路径到转换器
    debug_file = getattr(llm_client, 'debug_file', None)
    commands1 = ActionConverter.convert_to_game_commands(action1, mock_combat_state, debug_file)
    print(f"   转换后的游戏命令: {commands1}")
    
    print("\n2. 测试选择状态处理...")
    context2 = ActionConverter.determine_context(mock_choice_state)
    print(f"   检测到的情境: {context2}")
    
    action2 = llm_client.generate_action(mock_choice_state, context2)
    print(f"   LLM生成的动作: {action2}")
    
    commands2 = ActionConverter.convert_to_game_commands(action2, mock_choice_state, debug_file)
    print(f"   转换后的游戏命令: {commands2}")
    
    # 显示调试文件位置
    if hasattr(llm_client, 'debug_file'):
        print(f"\n📝 调试日志文件: {llm_client.debug_file}")
        print("   该文件包含详细的prompt、响应和转换过程")
    
    return True


def test_action_converter():
    """测试动作转换器的各种情况"""
    print("\n=== 测试动作转换器 ===")
    
    mock_state = {
        "game_state": {
            "combat_state": {
                "hand": [{"name": "Strike"}, {"name": "Defend"}],
                "monsters": [{"name": "Jaw Worm"}]
            },
            "choice_list": ["Option 1", "Option 2", "Option 3"],
            "potions": [{"name": "Health Potion"}, {"name": "Potion Slot"}]
        }
    }
    
    test_cases = [
        ('{"command": "PLAY", "card_index": 0, "target_index": 0}', "PLAY动作"),
        ('{"command": "END"}', "END动作"),
        ('{"command": "CHOOSE", "choice_index": 1}', "CHOOSE动作"),
        ('{"command": "PROCEED"}', "PROCEED动作"),
        ('{"command": "POTION", "potion_action": "use", "slot": 0}', "POTION动作"),
        ('{"invalid": "json"}', "无效JSON"),
        ('not json at all', "非JSON字符串")
    ]
    
    for action_json, description in test_cases:
        print(f"\n测试 {description}:")
        print(f"  输入: {action_json}")
        commands = ActionConverter.convert_to_game_commands(action_json, mock_state)
        print(f"  输出: {commands}")


def main():
    """主测试函数"""
    print("LLM Agent 测试程序")
    print("=" * 50)
    
    # 测试Ollama连接
    if not test_ollama_connection():
        print("\n⚠️  Ollama连接失败，无法进行完整测试")
        print("但是可以继续测试动作转换器...")
    
    # 测试动作转换器
    test_action_converter()
    
    # 如果Ollama可用，测试LLM处理
    llm_client = LLMClient(enable_debug_output=False)  # 临时测试时不创建调试文件
    if llm_client.test_connection():
        test_llm_with_mock_game_state()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n💡 提示:")
    print("- 运行游戏时会自动生成调试日志文件在 debug_logs/ 目录")
    print("- 调试文件包含每次LLM的prompt、响应和动作转换详情")
    print("- 可以通过设置 enable_debug_output=False 来关闭调试输出")


if __name__ == "__main__":
    main() 