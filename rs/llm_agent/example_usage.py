#!/usr/bin/env python3
"""
Slay the Spire LLM Agent 使用示例

这个脚本演示了如何使用LLM Agent来玩Slay the Spire
运行前确保：
1. Ollama服务已启动
2. qwen3:4b模型已下载
3. Communication Mod已正确配置
"""

from rs.api.client import Client
from rs.llm_agent.llm_client import LLMClient
from rs.llm_agent.llm_strategy import LLMGame
from rs.helper.logger import log, init_log, log_new_run_sequence


def main():
    """主函数演示LLM Agent的使用"""
    
    # 初始化日志
    init_log()
    log("LLM Agent 使用示例")
    log_new_run_sequence()
    
    try:
        # 1. 创建LLM客户端
        log("步骤 1: 创建LLM客户端")
        llm_client = LLMClient(
            model_name="qwen3:4b",                 # 使用的模型
            base_url="http://localhost:11434"      # Ollama服务地址
        )
        
        # 2. 测试连接
        log("步骤 2: 测试LLM连接")
        if not llm_client.test_connection():
            print("❌ LLM连接失败！")
            print("请检查:")
            print("  - Ollama服务是否运行: ollama serve")
            print("  - 模型是否已下载: ollama pull qwen3:4b")
            return
        print("✅ LLM连接成功")
        
        # 3. 创建游戏客户端
        log("步骤 3: 创建游戏客户端")
        client = Client()
        
        # 4. 创建LLM游戏控制器
        log("步骤 4: 创建LLM游戏控制器")
        llm_game = LLMGame(
            client=client,
            llm_client=llm_client,
            character="IRONCLAD"  # 可选: IRONCLAD, THE_SILENT, DEFECT, WATCHER
        )
        
        # 5. 开始游戏
        log("步骤 5: 开始游戏")
        print("🎮 启动游戏，请在Slay the Spire中确保Communication Mod已启用")
        print("💡 游戏将由AI自动进行，你可以观察其决策过程")
        
        # 可以指定种子以获得可重复的结果
        seed = ""  # 空字符串表示随机种子
        # seed = "TEST123ABC"  # 取消注释以使用固定种子
        
        llm_game.start(seed)
        llm_game.run()
        
        log("游戏结束")
        print("🏁 游戏完成！")
        
    except KeyboardInterrupt:
        log("用户中断游戏")
        print("\n⏸️  游戏被用户中断")
        
    except Exception as e:
        log(f"运行时错误: {e}")
        print(f"❌ 发生错误: {e}")
        print("请检查日志获取详细信息")


if __name__ == "__main__":
    print("Slay the Spire LLM Agent 示例")
    print("=" * 40)
    print()
    
    main()
    
    print()
    print("示例完成！")
    print("查看日志文件获取详细的游戏记录") 