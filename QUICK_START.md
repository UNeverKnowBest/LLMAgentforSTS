# LLM Agent 快速启动指南

## 预备条件

### 1. 安装依赖
确保你已安装：
- **Python 3.7+** 
- **Ollama** (从 https://ollama.ai 下载)
- **Slay the Spire** 
- **ModTheSpire** 和 **BaseMod**
- **Communication Mod**

### 2. 下载模型
```bash
ollama pull qwen3:4b
```

### 3. 启动Ollama服务
```bash
ollama serve
```

## 快速启动

### 方法一：使用批处理文件（推荐）
1. 双击 `start_llm_agent.bat`
2. 按提示检查所有条件
3. 按任意键开始

### 方法二：手动启动
```bash
python main.py
```

## 验证设置

### 测试Ollama连接
```python
python -c "from rs.llm_agent.test_llm import test_ollama_connection; test_ollama_connection()"
```

### 测试完整系统
```python
python -c "from rs.llm_agent.test_llm import main; main()"
```

## 配置Communication Mod

1. **找到SpireConfig文件**：
   - Windows: `%USERPROFILE%/.prefs/SpireConfig`
   - 或游戏安装目录

2. **设置命令**：
   ```
   command=python D:\\SteamLibrary\\steamapps\\common\\SlayTheSpire\\llm_agent\\main.py
   ```
   
   **注意**：路径中的反斜杠必须转义（使用双反斜杠）

3. **重启游戏**以激活设置

## 运行游戏

1. **启动Slay the Spire**
2. **确保Communication Mod已启用**（在Mods菜单中）
3. **等待主菜单完全加载**
4. **运行Python程序**（使用上述方法之一）

## 观察运行

### 程序日志
- **位置**：`logs/` 目录
- **内容**：程序运行状态、错误信息

### 调试日志
- **位置**：`debug_logs/` 目录  
- **内容**：LLM交互详情、动作转换过程
- **文件格式**：`llm_debug_YYYYMMDD_HHMMSS.txt`

### 实时观察
程序会在控制台输出：
- 连接状态
- 游戏状态变化
- LLM决策
- 动作执行结果

## 常见问题

### Q: 显示"JSON Decode Error"
**A**: Communication Mod未正确连接，检查：
- 游戏是否运行
- Communication Mod是否启用
- SpireConfig路径是否正确

### Q: 显示"LLM连接失败"  
**A**: Ollama服务问题，检查：
- `ollama serve` 是否运行
- 模型是否已下载
- 端口11434是否可用

### Q: 游戏动作无效
**A**: 查看调试日志，通常是：
- 动作格式错误
- 游戏状态不匹配
- 卡牌索引问题

## 停止程序

- 按 `Ctrl+C` 停止Python程序
- 程序会自动保存日志并优雅退出
- 调试日志会保留供分析

## 下一步

- 查看 `DEBUG_GUIDE.md` 了解调试功能
- 查看 `TROUBLESHOOTING.md` 解决问题
- 修改 `main.py` 调整运行参数
- 查看 `rs/llm_agent/` 了解代码结构

## 提示

- **首次运行**可能需要几分钟来建立连接
- **游戏状态变化**时程序会暂停等待
- **LLM响应**可能需要数秒时间
- **调试日志**包含完整的决策过程 