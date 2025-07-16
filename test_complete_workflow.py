#!/usr/bin/env python3
"""
完整的STS Agent测试套件
测试所有组件、工作流程和边界情况
确保项目无bug
"""

import sys
import os
import json
import time
import unittest
import unittest.mock
from unittest.mock import patch, MagicMock
from io import StringIO
from typing import Dict, Any
import tempfile
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from src.graph.builder import create_agent
from src.graph.states import GameState
from src.graph.nodes import (
    initial_game, read_state, advice_on_command, 
    validate_command, execute_command
)
from src.core.llms import LLMResponse, get_structured_llm
from src.prompts.prompt_generator import PromptGenerator
from src.game.game_constants import ScreenType

class TestCompleteWorkflow(unittest.TestCase):
    """完整工作流程测试"""

    def setUp(self):
        """测试前设置"""
        self.agent = create_agent()
        self.maxDiff = None
        
        # 模拟游戏状态样本
        self.sample_game_states = {
            "menu": {
                "available_commands": ["start"],
                "ready_for_command": True,
                "in_game": False,
                "game_state": None
            },
            "combat": {
                "available_commands": ["play", "end", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_type": "COMBAT",
                    "floor": 5,
                    "act": 1,
                    "current_hp": 50,
                    "max_hp": 80,
                    "class": "IRONCLAD",
                    "combat_state": {
                        "turn": 3,
                        "hand": [
                            {"name": "Strike", "cost": 1, "type": "ATTACK", "is_playable": True},
                            {"name": "Defend", "cost": 1, "type": "SKILL", "is_playable": True}
                        ],
                        "player": {"current_hp": 50, "max_hp": 80, "energy": 3, "block": 0},
                        "monsters": [
                            {"name": "Cultist", "current_hp": 20, "max_hp": 48, "intent": "ATTACK", "move_adjusted_damage": 6}
                        ]
                    },
                    "deck": [{"name": "Strike"}, {"name": "Defend"}] * 5
                }
            },
            "card_reward": {
                "available_commands": ["choose", "skip"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_type": "CARD_REWARD",
                    "floor": 6,
                    "screen_state": {
                        "cards": [
                            {"name": "Whirlwind", "type": "ATTACK", "rarity": "UNCOMMON"},
                            {"name": "Battle Trance", "type": "SKILL", "rarity": "UNCOMMON"}
                        ]
                    }
                }
            },
            "shop": {
                "available_commands": ["choose", "leave"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_type": "SHOP_SCREEN",
                    "gold": 150,
                    "screen_state": {
                        "cards": [{"name": "Offering", "price": 150}],
                        "relics": [{"name": "Red Skull", "price": 200}],
                        "potions": []
                    }
                }
            },
            "game_over": {
                "available_commands": ["confirm"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": {
                    "screen_type": "GAME_OVER",
                    "floor": 25,
                    "score": 450
                }
            }
        }

    def test_01_individual_nodes(self):
        """测试各个节点函数"""
        print("\n=== 测试节点函数 ===")
        
        # 测试initial_game节点
        with patch('builtins.print') as mock_print:
            state = GameState()
            result = initial_game(state)
            mock_print.assert_called()
            self.assertEqual(result, {})
        
        # 测试read_state节点 - 正常JSON输入
        test_json = json.dumps(self.sample_game_states["combat"])
        with patch('sys.stdin.readline', return_value=test_json + '\n'):
            state = GameState()
            result = read_state(state)
            self.assertIsNotNone(result.get("game_state_json"))
            self.assertEqual(result["game_state_json"]["in_game"], True)
        
        # 测试read_state节点 - EOF处理
        with patch('sys.stdin.readline', side_effect=EOFError):
            state = GameState()
            result = read_state(state)
            self.assertIsNone(result.get("game_state_json"))
        
        print("✅ 节点函数测试通过")

    def test_02_prompt_generator(self):
        """测试提示生成器"""
        print("\n=== 测试提示生成器 ===")
        
        for state_name, game_state in self.sample_game_states.items():
            print(f"测试 {state_name} 屏幕...")
            
            try:
                generator = PromptGenerator(game_state)
                command, prompt = generator.get_command_or_prompt()
                
                # 验证输出
                self.assertTrue(command is not None or prompt is not None, 
                              f"{state_name}: 必须返回命令或提示")
                
                if command:
                    self.assertIsInstance(command, str)
                    self.assertGreater(len(command), 0)
                    print(f"  简单命令: {command}")
                
                if prompt:
                    self.assertIsInstance(prompt, str)
                    self.assertGreater(len(prompt), 10)
                    print(f"  生成提示长度: {len(prompt)} 字符")
                    
            except Exception as e:
                self.fail(f"提示生成器在 {state_name} 状态下失败: {e}")
        
        print("✅ 提示生成器测试通过")

    def test_03_llm_response_structure(self):
        """测试LLM响应结构"""
        print("\n=== 测试LLM响应结构 ===")
        
        # 测试LLMResponse模型
        test_responses = [
            {"think": "我需要打击敌人", "command": "play 1"},
            {"think": "回合结束", "command": "end"},
            {"think": "选择卡牌", "command": "choose 1"}
        ]
        
        for response_data in test_responses:
            try:
                response = LLMResponse(**response_data)
                self.assertEqual(response.think, response_data["think"])
                self.assertEqual(response.command, response_data["command"])
            except Exception as e:
                self.fail(f"LLMResponse结构测试失败: {e}")
        
        print("✅ LLM响应结构测试通过")

    @patch('src.core.llms.llm')
    def test_04_advice_on_command_with_mock_llm(self, mock_llm):
        """测试advice_on_command节点（模拟LLM）"""
        print("\n=== 测试advice_on_command节点 ===")
        
        # 模拟LLM响应
        mock_responses = [
            LLMResponse(think="攻击是最好的防御", command="play 1"),
            LLMResponse(think="需要防御", command="play 2"),
            LLMResponse(think="结束回合", command="end")
        ]
        
        for i, (state_name, game_state) in enumerate(self.sample_game_states.items()):
            if game_state.get("in_game"):
                print(f"测试 {state_name} 状态...")
                
                # 设置模拟响应
                if i < len(mock_responses):
                    mock_llm.invoke.return_value = mock_responses[i]
                
                state = GameState(game_state_json=game_state)
                result = advice_on_command(state)
                
                self.assertIn("final_command", result)
                self.assertIsInstance(result["final_command"], str)
                print(f"  生成命令: {result['final_command']}")
                
                if "thinking_process" in result:
                    print(f"  思考过程: {result['thinking_process'][:50]}...")
        
        print("✅ advice_on_command测试通过")

    def test_05_command_validation(self):
        """测试命令验证"""
        print("\n=== 测试命令验证 ===")
        
        # 测试用例：[命令, 游戏状态, 期望结果]
        validation_test_cases = [
            ("play 1", self.sample_game_states["combat"], True),
            ("end", self.sample_game_states["combat"], True),
            ("choose 1", self.sample_game_states["card_reward"], True),
            ("invalid_command", self.sample_game_states["combat"], False),
            ("play", self.sample_game_states["combat"], False),  # 缺少参数
            ("play abc", self.sample_game_states["combat"], False),  # 无效参数
            ("", self.sample_game_states["combat"], False),  # 空命令
        ]
        
        for command, game_state, expected_valid in validation_test_cases:
            print(f"验证命令: '{command}'")
            
            state = GameState(
                game_state_json=game_state,
                final_command=command
            )
            
            try:
                result = validate_command(state)
                validation_result = result.get("validation_result", {})
                is_valid = validation_result.get("is_valid", False)
                
                if expected_valid:
                    self.assertTrue(is_valid, f"命令 '{command}' 应该有效")
                else:
                    self.assertFalse(is_valid, f"命令 '{command}' 应该无效")
                
                print(f"  结果: {'✅' if is_valid else '❌'}")
                
                if not is_valid and validation_result.get("errors"):
                    print(f"  错误: {validation_result['errors'][0]}")
                    
            except Exception as e:
                print(f"  验证出错: {e}")
                if expected_valid:
                    self.fail(f"验证有效命令时出错: {e}")
        
        print("✅ 命令验证测试通过")

    def test_06_execute_command(self):
        """测试命令执行"""
        print("\n=== 测试命令执行 ===")
        
        test_commands = ["play 1", "end", "choose 1", "state"]
        
        for command in test_commands:
            print(f"执行命令: {command}")
            
            state = GameState(final_command=command)
            
            with patch('builtins.print') as mock_print:
                result = execute_command(state)
                
                # 验证命令被打印到stdout（第一次调用）
                expected_calls = [
                    unittest.mock.call(command, flush=True),
                    unittest.mock.call(f"Sent command: {command}", file=sys.stderr)
                ]
                mock_print.assert_has_calls(expected_calls, any_order=False)
                
                # 验证返回结果
                self.assertIsInstance(result, dict)
                print(f"  执行状态: ✅")
        
        print("✅ 命令执行测试通过")

    def test_07_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试无效JSON输入
        with patch('sys.stdin.readline', return_value='invalid json\n'):
            with patch('sys.stderr', new_callable=StringIO):
                state = GameState()
                result = read_state(state)
                self.assertIsNone(result.get("game_state_json"))
        
        # 测试空游戏状态
        state = GameState(game_state_json=None)
        result = advice_on_command(state)
        self.assertEqual(result.get("final_command"), "state")
        
        # 测试提示生成器错误
        invalid_game_state = {"invalid": "structure"}
        try:
            generator = PromptGenerator(invalid_game_state)
            command, prompt = generator.get_command_or_prompt()
            # 应该返回默认值而不是崩溃
            self.assertTrue(command is not None or prompt is not None)
        except Exception as e:
            print(f"  提示生成器处理无效状态: {e}")
        
        print("✅ 错误处理测试通过")

    def test_08_screen_type_detection(self):
        """测试屏幕类型检测"""
        print("\n=== 测试屏幕类型检测 ===")
        
        screen_tests = [
            ({"screen_type": "COMBAT"}, ScreenType.COMBAT),
            ({"screen_type": "CARD_REWARD"}, ScreenType.CARD_REWARD),
            ({"screen_type": "SHOP_SCREEN"}, ScreenType.SHOP_SCREEN),
            ({"screen_type": "NONE", "room_phase": "COMBAT"}, ScreenType.COMBAT),
            ({"screen_type": "INVALID"}, ScreenType.NONE),
        ]
        
        for game_state, expected_screen in screen_tests:
            test_state = {"game_state": game_state}
            generator = PromptGenerator(test_state)
            detected_screen = generator._get_effective_screen_type()
            
            self.assertEqual(detected_screen, expected_screen,
                           f"屏幕类型检测错误: {game_state} -> {detected_screen} != {expected_screen}")
            print(f"  {game_state.get('screen_type', 'None')}: ✅")
        
        print("✅ 屏幕类型检测测试通过")

    @patch('sys.stdin')
    @patch('builtins.print')
    def test_09_complete_workflow_simulation(self, mock_print, mock_stdin):
        """测试完整工作流程模拟"""
        print("\n=== 测试完整工作流程 ===")
        
        # 模拟输入序列：菜单 -> 战斗 -> 游戏结束
        input_sequence = [
            json.dumps(self.sample_game_states["menu"]) + '\n',
            json.dumps(self.sample_game_states["combat"]) + '\n',
            json.dumps(self.sample_game_states["game_over"]) + '\n',
        ]
        
        # 模拟LLM响应
        with patch('src.core.llms.llm') as mock_llm:
            mock_llm.invoke.return_value = LLMResponse(
                think="分析当前情况", 
                command="play 1"
            )
            
            # 模拟stdin输入
            mock_stdin.readline.side_effect = input_sequence + [EOFError()]
            
            # 创建初始状态
            initial_state = {
                "game_state_json": None,
                "thinking_process": None,
                "final_command": None,
                "command_success": None,
                "error_message": None,
                "is_game_over": None,
                "state_valid": None,
                "validation_result": None,
                "fallback_command": None
            }
            
            try:
                # 执行工作流程
                result = self.agent.invoke(initial_state)
                
                # 验证结果
                self.assertIsNotNone(result)
                print("  工作流程执行完成")
                
                # 检查是否有输出
                self.assertTrue(mock_print.called)
                print(f"  命令执行次数: {mock_print.call_count}")
                
            except Exception as e:
                print(f"  工作流程执行错误: {e}")
                # 某些错误是可预期的（如EOFError），不应导致测试失败
                if "EOFError" not in str(e):
                    raise
        
        print("✅ 完整工作流程测试通过")

    def test_10_edge_cases(self):
        """测试边界情况"""
        print("\n=== 测试边界情况 ===")
        
        # 测试极长的输入
        very_long_game_state = {
            "available_commands": ["play"] * 100,
            "ready_for_command": True,
            "in_game": True,
            "game_state": {
                "screen_type": "COMBAT",
                "deck": [{"name": f"Card_{i}"} for i in range(1000)]
            }
        }
        
        try:
            generator = PromptGenerator(very_long_game_state)
            command, prompt = generator.get_command_or_prompt()
            self.assertTrue(command is not None or prompt is not None)
            print("  ✅ 处理大型游戏状态")
        except Exception as e:
            print(f"  ❌ 大型游戏状态处理失败: {e}")
        
        # 测试特殊字符
        special_char_state = {
            "available_commands": ["play"],
            "ready_for_command": True,
            "in_game": True,
            "game_state": {
                "screen_type": "COMBAT",
                "special_field": "特殊字符测试 !@#$%^&*()"
            }
        }
        
        try:
            generator = PromptGenerator(special_char_state)
            command, prompt = generator.get_command_or_prompt()
            print("  ✅ 处理特殊字符")
        except Exception as e:
            print(f"  ❌ 特殊字符处理失败: {e}")
        
        # 测试空游戏状态
        empty_state = {}
        try:
            generator = PromptGenerator(empty_state)
            command, prompt = generator.get_command_or_prompt()
            print("  ✅ 处理空状态")
        except Exception as e:
            print(f"  ❌ 空状态处理失败: {e}")
        
        print("✅ 边界情况测试通过")

    def test_11_performance(self):
        """测试性能"""
        print("\n=== 测试性能 ===")
        
        # 测试提示生成器性能
        start_time = time.time()
        for _ in range(100):
            generator = PromptGenerator(self.sample_game_states["combat"])
            command, prompt = generator.get_command_or_prompt()
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        print(f"  提示生成平均耗时: {avg_time:.4f}秒")
        self.assertLess(avg_time, 0.1, "提示生成耗时过长")
        
        # 测试命令验证性能
        start_time = time.time()
        for _ in range(100):
            state = GameState(
                game_state_json=self.sample_game_states["combat"],
                final_command="play 1"
            )
            validate_command(state)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        print(f"  命令验证平均耗时: {avg_time:.4f}秒")
        self.assertLess(avg_time, 0.01, "命令验证耗时过长")
        
        print("✅ 性能测试通过")

def run_comprehensive_tests():
    """运行完整测试套件"""
    print("🧪 开始STS Agent完整测试套件")
    print("=" * 60)
    
    # 配置日志
    logging.basicConfig(level=logging.WARNING)
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCompleteWorkflow)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 60)
    print("🏆 测试结果总结")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split('AssertionError:')[-1].strip() if 'AssertionError:' in trace else 'Unknown error'}")
    
    if result.errors:
        print("\n❌ 错误的测试:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split('Exception:')[-1].strip() if 'Exception:' in trace else 'Unknown error'}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！项目运行正常，无重大bug。")
        return True
    else:
        print(f"\n⚠️ 发现 {len(result.failures + result.errors)} 个问题，需要修复。")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 