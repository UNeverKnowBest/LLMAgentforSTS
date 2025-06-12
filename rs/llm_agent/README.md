# Slay the Spire LLM Agent

这是一个基于大语言模型的Slay the Spire AI agent，使用本地Ollama服务与qwen3:4b模型。

## 特性

- 🤖 使用本地LLM（qwen3:4b）进行游戏决策
- 📊 直接处理原始游戏状态JSON，无需转换
- 🎯 上下文感知的决策制定
- 🛡️ 强健的错误处理和动作验证
- 📝 详细的日志记录

## 快速开始

### 1. 安装Ollama和模型

```bash
# 安装Ollama (访问 https://ollama.ai)
# Windows/Mac: 下载安装包
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 启动Ollama服务
ollama serve

# 下载qwen3:4b模型
ollama pull qwen3:4b
```

### 2. 安装Python依赖

```bash
pip install requests
```

### 3. 运行测试

```bash
# 测试LLM连接和基本功能
python -m rs.llm_agent.test_llm
```

### 4. 运行游戏

```bash
# 在游戏中启动Communication Mod后运行
python main.py
```

## 架构说明

### 核心组件

1. **LLMClient** (`llm_client.py`)
   - 与Ollama API通信
   - 构建游戏状态提示词
   - 解析LLM输出

2. **ActionConverter** (`action_converter.py`) 
   - 将LLM的JSON输出转换为游戏命令
   - 验证动作的合法性
   - 提供上下文感知

3. **LLMGame** (`llm_strategy.py`)
   - 简化的游戏控制器
   - 集成LLM决策与游戏循环
   - 错误恢复机制

### 决策流程

1. 接收游戏状态JSON
2. 分析当前情境（战斗/选择/地图等）
3. 构建上下文相关的提示词
4. 调用LLM生成决策
5. 验证并转换为游戏命令
6. 执行命令并等待下一状态

## 配置选项

在 `main.py` 中可以配置:

```python
# LLM模型配置
llm_client = LLMClient(
    model_name="qwen3:4b",           # 模型名称
    base_url="http://localhost:11434"   # Ollama服务地址
)

# 游戏配置
character = "IRONCLAD"  # 角色选择
run_amount = 1          # 运行次数
run_seeds = []          # 指定种子
```

## 支持的游戏动作

- `PLAY` - 打出手牌
- `END` - 结束回合
- `CHOOSE` - 做出选择
- `PROCEED` - 确认/继续
- `RETURN` - 返回/跳过
- `POTION` - 使用/丢弃药水

## 故障排除

### Ollama连接失败
```
✗ Ollama连接失败
```
**解决方案:**
1. 确保Ollama服务运行: `ollama serve`
2. 检查端口11434是否可用
3. 确认模型已下载: `ollama list`

### 模型响应慢
**解决方案:**
1. 使用更小的模型: `ollama pull qwen2:1.5b`
2. 调整提示词长度
3. 增加超时时间

### 游戏命令错误
**解决方案:**
1. 检查日志中的LLM输出
2. 验证JSON格式正确性
3. 确认游戏状态数据完整

## 扩展和定制

### 添加新的决策策略
1. 修改 `_build_prompt()` 方法
2. 添加特定情境的处理逻辑
3. 调整LLM参数 (temperature, top_p等)

### 支持其他LLM
1. 继承 `LLMClient` 类
2. 实现对应的API调用
3. 适配不同的响应格式

## 注意事项

- 确保Communication Mod正确配置并运行
- LLM决策可能需要几秒钟时间
- 建议在测试模式下先验证功能
- 大模型的决策质量取决于提示词设计

## 贡献

欢迎提交Issue和Pull Request来改进LLM agent！ 