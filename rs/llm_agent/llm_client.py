import json
import requests
import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple
from rs.helper.logger import log, log_to_run
from rs.llm_agent.action_converter import ActionConverter

class ScreenType:
    BATTLE = "COMBAT"
    MAP = "MAP"
    CARD_REWARD = "CARD_REWARD"
    BOSS_RELIC = "BOSS_REWARD"
    SHOP_ROOM = "SHOP_ROOM"
    REST = "REST"
    CHEST = "TREASURE"
    EVENT = "EVENT"
    COMBAT_REWARD = "COMBAT_REWARD"
    GRID = "GRID"
    HAND_SELECT = "HAND_SELECT"
    NONE = "NONE"

DEFAULT_SYSTEM_PROMPT = """你是《杀戮尖塔》的顶级AI，拥有数千小时的游戏经验。你的目标是冲击最高层，决策必须兼具长远规划和当前最优。

# 1. 核心游戏哲学
- **卡组质量 > 数量**: 牌库不是越大越好。每张牌都应服务于你的核心战略。无用的牌会稀释你的抽牌堆，卡住关键张。
- **生命值是资源**: 不要为了节省几点生命值而放弃战略优势（例如，避免精英战斗、不拿关键卡）。有时，承受伤害是为了获得更强的遗物或卡牌，从而在长期获得更大利益。
- **规划而非反应**: 始终提前2-3个房间思考。你的篝火用来升级还是休息？你的金币要在商店买什么？这些都应提前规划。

# 2. 卡组构建与选牌策略
- **寻找制胜组合 (Combo)**: 你的卡组需要一个明确的获胜方式。是无限循环、巨量力量、海量毒素还是护甲制胜？你拿的每一张牌都应加强这个组合。
- **优先解决核心问题**: 
  - **前期 (第一幕)**: 优先拿高质量的攻击牌来快速解决战斗，安全度过前期。AOE（群体攻击）能力非常重要。
  - **中期 (第二幕)**: 开始寻找并构建你的核心卡组组件和防御/规模化解决方案（如：力量、专注、毒、壁垒等）。
  - **后期 (第三幕及以后)**: 完善你的制胜组合，寻找能打破游戏规则的稀有卡和遗物。
- **跳过是常态**: 如果奖励卡牌都不符合你的卡组规划，果断选择"跳过"。拿一张平庸的牌比不拿更糟糕。

# 3. 地图路径选择策略
- **精英(E)是关键**: 精英是遗物的主要来源，是卡组强度的飞跃点。路径规划应尽可能多地包含精英战斗。
- **精英前的准备**: 挑战精英前，务必做好准备。路径上最好有篝火(R)用于升级，或商店($)用于购买强力卡牌/遗物或移除弱卡。状态不佳时（血量低、卡组弱），应优先选择有篝火的路径。
- **篝火(R)的使用**: 
    - **升级 > 休息**: 绝大多数情况，升级核心卡牌的收益远大于休息回血。只有在血量极度危险（低于30%）且无其他恢复手段时才考虑休息。
    - **升级优先级**: Combo核心组件 > 降费关键牌 > 提升伤害/格挡数值的牌。
- **商店($)的价值**:
    - **移除 > 购买**: 游戏中最强的能力之一就是"移除卡牌"。优先花费金币移除初始的"打击"和"防御"，这能极大地提升卡组流畅度。
    - **购买优先级**: 改变游戏规则的核心遗物(SSS级) > 关键卡牌 > 普通强力遗物 > 药水。

# 4. 输出规则 - 严格遵守
你可以先思考，但最终必须输出一个有效的JSON对象作为结果。

格式要求：
1. 可以使用<think>标签进行思考分析，分析过程需要详尽。
2. 思考后必须输出最终决策JSON。
3. JSON必须是有效格式，包含command字段。

## 战斗指令
- **正确格式**: `{"command": "PLAY", "card_index": 0, "target_index": 0}` 或 `{"command": "END"}`
- **错误格式**: `{"command": "PLAY", "target": "Miracle"}`  <-- 绝对禁止！必须使用 card_index，而不是卡牌名称。

## 非战斗指令
- **正确格式**: `{"command": "CHOOSE", "choice_index": 0}`

思考后必须给出JSON决策，否则游戏无法继续。
"""

class LLMClient:
    """与Ollama本地大模型通信的客户端"""
    
    def __init__(self, model_name: str = "qwen3:8b", base_url: str = "http://localhost:11434", enable_debug_output: bool = True, system_prompt: str = DEFAULT_SYSTEM_PROMPT, timeout: int = 120):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api/generate"
        self.enable_debug_output = enable_debug_output
        self.system_prompt = system_prompt
        self.turn_counter = 0
        self.timeout = timeout
        
        # 初始化调试输出文件
        if self.enable_debug_output:
            self._init_debug_file()
        
    def _init_debug_file(self):
        """初始化调试输出文件"""
        try:
            # 创建debug目录 - 修复竞态条件
            debug_dir = "debug_logs"
            os.makedirs(debug_dir, exist_ok=True)
            log(f"创建调试目录: {debug_dir}")
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.debug_file = os.path.join(debug_dir, f"llm_debug_{timestamp}.txt")
            log(f"尝试创建调试文件: {self.debug_file}")
            
            # 测试写入权限
            test_content = "test write"
            with open(self.debug_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 验证文件创建成功
            if os.path.exists(self.debug_file):
                log(f"调试文件创建成功: {self.debug_file}")
            else:
                raise Exception("文件创建后无法找到")
                
            # 写入真正的文件头
            with open(self.debug_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"LLM Agent 调试日志\n")
                f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"模型: {self.model_name}\n")
                f.write(f"API地址: {self.api_url}\n")
                f.write("=" * 80 + "\n\n")
                f.write("--- Base System Prompt ---\n")
                f.write(self.system_prompt)
                f.write("\n" + "=" * 80 + "\n")
                f.flush()  # 确保立即写入
            
            log(f"LLM调试日志文件: {self.debug_file}")
            
        except Exception as e:
            log(f"初始化调试文件失败: {e}")
            log(f"错误详情: {type(e).__name__}: {str(e)}")
            self.enable_debug_output = False
            self.debug_file = None
        
    def test_connection(self) -> bool:
        """测试与Ollama的连接"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                log(f"Successfully connected to Ollama at {self.base_url}")
                return True
            else:
                log(f"Failed to connect to Ollama: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            log(f"Failed to connect to Ollama: {e}")
            return False
    
    def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """直接调用LLM获取响应（用于测试）"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9,
                "num_predict": 2048
            }
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(self.api_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"
    
    def generate_action(self, game_state_json: Dict[Any, Any]) -> Tuple[Dict[str, Any], str]:
        """
        根据游戏状态生成动作
        
        Args:
            game_state_json: 游戏状态的JSON数据
            
        Returns:
            生成的动作JSON对象和所使用的上下文
        """
        context = "unknown"
        try:
            # 确定上下文并过滤游戏状态
            context = self._get_context(game_state_json)
            filtered_state = self._filter_game_state(game_state_json, context)

            # 构建系统提示，包含基础提示和上下文战术
            final_system_prompt_with_tactics, prompt = self._build_prompt(filtered_state, context)

            # 记录到调试文件
            if self.enable_debug_output:
                self.turn_counter += 1
                # 从final_system_prompt中提取附加的战术部分
                system_prompt_additions = final_system_prompt_with_tactics.replace(self.system_prompt, '').strip()
                self._log_turn_to_debug({
                    "context": context, 
                    "system_prompt_additions": system_prompt_additions, 
                    "user_prompt": prompt
                })
            
            # 发送请求到Ollama
            payload = {
                "model": self.model_name,
                "system": final_system_prompt_with_tactics,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.3,
                "num_predict": 2048,
                "stop": ["```", "==="]
            }
            
            generated_text = ""
            action_json = {}
            max_retries = 5
            
            for attempt in range(max_retries):
                try:
                    log(f"LLM请求尝试 {attempt + 1}/{max_retries}")
                    log(f"等待LLM响应中...（最长{self.timeout}秒超时）")
                    response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result.get("response", "").strip()
                        
                        if not generated_text:
                            log(f"LLM返回空响应，尝试重试...")
                            continue
                        
                        action_str = self._extract_action_json(generated_text, context)
                        action_json = json.loads(action_str)
                        
                        if self._is_valid_action_format(action_json):
                            log(f"LLM成功生成动作: {action_json}")
                            break
                        else:
                            log(f"LLM生成的动作格式无效，尝试重试...")
                    else:
                        log(f"API请求失败，状态码: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    log(f"网络请求异常: {e}")
                
                if attempt == max_retries - 1:
                    log("所有重试失败，使用回退动作")
                    action_json = self._get_fallback_action(context)
                    generated_text = f"ERROR: 重试失败. 使用回退动作: {json.dumps(action_json)}"
                    break

            # 记录成功的回合信息
            if self.enable_debug_output:
                self._log_turn_to_debug({
                    "context": context,
                    "raw_response": generated_text,
                    "final_action": json.dumps(action_json)
                })
            
            log_to_run(f"LLM generated action: {action_json}")
            return action_json, context
                
        except Exception as e:
            error_msg = f"在LLM生成过程中发生严重错误: {e}"
            log(error_msg)
            if self.enable_debug_output:
                self._log_turn_to_debug({"context": context, "error": error_msg})
            return self._get_fallback_action(context), context
    
    def _log_turn_to_debug(self, data: Dict[str, str]):
        """以结构化格式记录单回合的详细信息到调试文件"""
        if not self.enable_debug_output or not self.debug_file:
            return
            
        try:
            with open(self.debug_file, 'a', encoding='utf-8') as f:
                context_str = data.get('context', 'N/A')
                f.write(f"\n\n{'='*30} TURN {self.turn_counter} ({context_str}) {'='*30}\n")
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}]\n")

                if "error" in data:
                    f.write(f"\n--- ERROR ---\n{data['error']}\n")
                else:
                    if "system_prompt_additions" in data:
                        f.write("\n--- System Prompt Additions ---\n")
                        f.write(data['system_prompt_additions'])

                    if "user_prompt" in data:
                        f.write("\n\n--- User Prompt (Filtered State) ---\n")
                        f.write(data['user_prompt'])

                    if "raw_response" in data:
                        f.write("\n\n--- LLM Raw Response ---\n")
                        f.write(data.get('raw_response', ''))

                    if "final_action" in data:
                        f.write("\n\n--- Final Action JSON ---\n")
                        f.write(data.get('final_action', ''))
            
                f.write(f"\n{'='*80}\n")
                f.flush()

        except Exception as e:
            log(f"写入调试文件失败: {e}")
    
    def _filter_game_state(self, game_state: Dict[Any, Any], context: str) -> Dict[Any, Any]:
        """根据上下文过滤游戏状态，只保留关键信息"""
        
        gs = game_state.get("game_state", {})
        if not gs:
            return game_state

        player_state = gs.get("player", {})
        filtered_gs = {
            "game_state": {
                "screen_type": gs.get("screen_type"),
                "room_type": gs.get("room_type"),
                "floor": gs.get("floor"),
                "player": {"current_hp": player_state.get("current_hp"), "max_hp": player_state.get("max_hp")},
                "gold": player_state.get("gold"),
                "relics": [{"name": r.get("name")} for r in gs.get("relics", [])] # 始终包含遗物名称
            }
        }

        if "战斗中" in context:
            if "combat_state" in gs:
                # 过滤手牌，只保留关键信息
                hand = gs["combat_state"].get("hand", [])
                filtered_hand = [
                    {
                        "name": card.get("name"),
                        "cost": card.get("cost"),
                        "type": card.get("type"),
                        "is_playable": card.get("is_playable")
                    } for card in hand
                ]

                filtered_gs["game_state"]["combat_state"] = {
                    "monsters": gs["combat_state"].get("monsters"),
                    "hand": filtered_hand,
                    "discard_pile": len(gs["combat_state"].get("discard_pile", [])),
                    "draw_pile": len(gs["combat_state"].get("draw_pile", [])),
                    "player": gs["combat_state"].get("player")
                }
            if "potions" in gs:
                filtered_gs["game_state"]["potions"] = gs.get("potions")
        
        elif "地图" in context:
            if "map" in gs:
                summary = self._summarize_map(gs)
                filtered_gs["game_state"]["map_summary"] = summary
            if "choice_list" in gs:
                filtered_gs["game_state"]["choice_list"] = gs.get("choice_list")

        elif "选择卡牌奖励" in context:
            if "choice_list" in gs:
                filtered_gs["game_state"]["choice_list"] = gs.get("choice_list")

        elif "事件" in context or "篝火" in context or "战斗奖励" in context:
             if "choice_list" in gs:
                filtered_gs["game_state"]["choice_list"] = gs.get("choice_list")
        
        # 商店的特殊处理
        elif "商店" in context:
            if "choice_list" in gs:
                filtered_gs["game_state"]["choice_list"] = gs.get("choice_list")
            if "shop" in gs:
                shop = gs["shop"]
                filtered_gs["game_state"]["shop_prices"] = {
                    "card_removal": shop.get("card_removal_cost"),
                    "cards": [c.get("price") for c in shop.get("cards", [])],
                    "relics": [r.get("price") for r in shop.get("relics", [])],
                    "potions": [p.get("price") for p in shop.get("potions", [])]
                }
                # 卡牌、遗物、药水的名称也需要保留
                filtered_gs["game_state"]["shop_items"] = {
                    "cards": [c.get("name") for c in shop.get("cards", [])],
                    "relics": [r.get("name") for r in shop.get("relics", [])],
                    "potions": [p.get("name") for p in shop.get("potions", [])]
                }
            # 如果是移除卡牌的子情境，还需要展示玩家的牌库
            if "移除卡牌" in context and "deck" in gs:
                filtered_gs["game_state"]["deck"] = [
                    {"name": card.get("name"), "id": card.get("id"), "upgrades": card.get("upgrades")} 
                    for card in gs.get("deck", [])
                ]

        return filtered_gs

    def _build_prompt(self, filtered_state: Dict[Any, Any], context: str) -> Tuple[str, str]:
        """构建完整的系统提示和用户提示。"""
        
        # 基础战术提示
        base_tactic = f"\n\n# 当前情境: {context}\n"
        final_system_prompt = self.system_prompt
        
        # 检查特殊遗物和事件的动态提示
        relic_names = [r.get("name") for r in filtered_state.get("game_state", {}).get("relics", [])]
        
        # 遗物动态提示
        if "Neow's Lament" in relic_names and "地图" in context:
            base_tactic += "### !! 战略警报: 尼利的馈赠 !! ###\n你拥有【尼利的馈赠】，可以无伤击败3个敌人。这是巨大优势！请不惜一切代价规划一条能连续挑战最多精英的路径！\n"
        if "Peace Pipe" in relic_names and "篝火" in context:
            base_tactic += "### !! 遗物提示: 和平烟斗 !! ###\n你拥有【和平烟斗】，可以在篝火处移除一张牌。这通常是比升级更好的选择！\n"

        # 事件动态提示
        if "Mind Bloom" in context:
            base_tactic += """### !! 关键事件: 心灵奇花 !! ###
你遇到了游戏中最关键的事件之一，你的选择将决定成败：
- **选项1: 打一场精英战斗**: 高风险高回报，能获得强力遗物。
- **选项2: 获得999金币，但无法回血**: 巨大财富，但风险极高，通常不选。
- **选项3: 升级所有牌，但获得2个诅咒**: 牌库质量飞跃，但诅咒会污染牌库。
请根据你的核心哲学（精英优先）和当前状态（血量、卡组强度）做出最明智的判断。
"""

        # 分支逻辑
        if "地图" in context:
            base_tactic += "战术提示: 路径选择是游戏中最关键的决策之一。请严格遵循你在'核心游戏哲学'第3条中学到的地图路径选择策略（精英优先、篝火准备、移除优先），进行长远规划后，再给出决策。\n最终指令: 你的决策必须是 'CHOOSE' 命令。"
        
        elif "选择卡牌奖励" in context:
            base_tactic += "# 选牌专家策略...\n最终指令: 你的决策必须是 'CHOOSE' 命令，如果跳过，请选择-1。\n" # 省略详细策略

        elif "战斗中" in context:
            # 战斗药水提示
            potions = filtered_state.get("game_state", {}).get("potions", [])
            usable_potions = [p for p in potions if p.get("can_use")]
            if usable_potions:
                base_tactic += "### !! 药水警报 !! ###\n你拥有可用的药水！在出牌前，优先考虑使用`POTION`命令是否能带来巨大优势（例如：斩杀敌人、紧急格挡、获得费用）。\n"

            monsters = filtered_state.get("game_state", {}).get("combat_state", {}).get("monsters", [])
            low_hp_enemies = [m for m in monsters if m.get('current_hp', 99) <= 6 and not m.get('is_gone', False)]
            
            if low_hp_enemies:
                base_tactic += f"战术提示: 存在{len(low_hp_enemies)}个低血量敌人（≤6血）。立即使用PLAY命令攻击击杀！\n"
                base_tactic += "攻击优先级: 0费攻击牌 > combo组合技 > Strike类攻击牌 > 单体高伤害牌。\n"
            else:
                base_tactic += "战术提示: 优先处理威胁最大的敌人（高攻击意图、给群体上debuff的敌人）。评估是否需要格挡，有时承受少量伤害来打出关键进攻牌是值得的。\n"
            
            hand = filtered_state.get("game_state", {}).get("combat_state", {}).get("hand", [])
            attack_cards = [i for i, card in enumerate(hand) if card.get('type') == 'ATTACK' and card.get('is_playable', False)]
            
            if attack_cards:
                # 推荐第一张可用的攻击牌
                base_tactic += f"推荐动作: 立即使用PLAY命令，选择手牌中索引为 {attack_cards[0]} 的攻击牌，目标选敌人0。\n"
            
            base_tactic += "严格要求: 战斗中只能使用`PLAY`, `POTION`, 或 `END`命令。\n"

        elif context == "战斗奖励 - 拾取奖励":
            base_tactic += "战术提示: 你正处于战斗胜利后的奖励界面。请选择一个你最需要的奖励。通常情况下，我们优先选择第一个（索引0）。\n最终指令: 你的决策必须是 'CHOOSE' 命令。"
        
        elif context == "战斗奖励 - 完成并继续" or context == "即将进入战斗":
            base_tactic += "战术提示: 这是一个过渡阶段。你唯一要做的就是'继续'。\n最终指令: 你的决策必须是 'PROCEED' 命令，格式为 {\"command\": \"PROCEED\"}。"

        elif "商店 - 主界面" in context:
            base_tactic += "战术提示: 你在商店。核心策略是**优先移除卡牌**。检查你的金币和移除费用。如果钱够，就选择移除。如果不够，或者已经移除了关键的弱牌，再考虑购买。\n最终指令: 你的决策必须是'CHOOSE'，以进入相应的子菜单（如购买、移除）。"
        
        elif "商店 - 移除卡牌" in context:
            base_tactic += "战术提示: 你正在选择要移除的卡牌。请从你的牌库中选择最优先移除的牌。移除优先级：**诅咒 > 打击/防御 > 其他对卡组帮助不大的牌**。\n最终指令: 你的决策必须是'CHOOSE'，选择牌库中对应卡牌的索引。"

        elif "事件" in context and "心灵奇花" not in context: # 通用事件
            base_tactic += "战术提示: 仔细阅读事件描述，权衡利弊。\n最终指令: 你的决策必须是 'CHOOSE' 命令。"
        
        elif "篝火" in context:
            base_tactic += "战术提示: 你正在篝火处，请严格遵循核心游戏哲学中的篝火使用策略进行思考（升级优先）。记住，只有在濒死（<30% HP）且前方有精英时才考虑休息。\n最终指令: 你的决策必须是 'CHOOSE' 命令。"
        
        elif "通用选择" in context:
            base_tactic += "战术提示: 评估每个选项的短期和长期价值。\n最终指令: 你的决策必须是 'CHOOSE' 命令。"

        final_system_prompt += base_tactic

        # 构建用户Prompt
        prompt_json = filtered_state
        if "map_summary" in prompt_json.get("game_state", {}):
            map_summary_text = prompt_json["game_state"].pop("map_summary")
            prompt = f"""你正在选择地图路径。请分析以下几条路径的战略价值。

--- 路径摘要 ---
{map_summary_text}
---

--- 其余状态 ---
```json
{json.dumps(prompt_json, ensure_ascii=False, indent=2)}
```
---

请基于路径摘要和你的核心策略，选择最优路径。分析完成后，请严格按照格式要求，在下面直接提供最终的JSON决策。"""
        else:
            prompt = f"""```json
{json.dumps(filtered_state, ensure_ascii=False, indent=2)}
```
分析完成后，请严格按照格式要求，在下面直接提供最终的JSON决策。"""

        return final_system_prompt, prompt
    
    def _extract_action_json(self, generated_text: str, context: str) -> str:
        """从生成的文本中提取动作JSON，并进行严格验证"""
        try:
            if not generated_text.strip():
                log("LLM返回空响应，使用回退逻辑")
                return json.dumps(self._get_fallback_action(context))
            
            # 使用正则表达式从文本中寻找所有可能的JSON对象
            # 这个正则表达式会寻找被大括号包围，且内部含有 "command" 键的字符串
            json_pattern = r'(\{.*?"command".*?\})'
            potential_jsons = re.findall(json_pattern, generated_text, re.DOTALL)
            
            # 验证并返回第一个完全有效的JSON
            for candidate_str in potential_jsons:
                try:
                    # 尝试解析，看它是不是一个合法的JSON
                    parsed_json = json.loads(candidate_str)
                    
                    # 使用统一的、严格的格式验证函数
                    if self._is_valid_action_format(parsed_json):
                        log(f"成功提取并验证了JSON: {candidate_str}")
                        return candidate_str # 返回验证通过的JSON字符串
                
                except json.JSONDecodeError:
                    # 如果不是一个有效的JSON字符串，就跳过
                    continue
            
            log(f"无法从LLM输出中提取有效JSON。原始输出: {generated_text[:200]}...")
            return json.dumps(self._get_fallback_action(context))
                
        except Exception as e:
            log(f"提取动作JSON时发生错误: {e}")
            return json.dumps(self._get_fallback_action(context))
    
    def _is_valid_action_format(self, action_json: Any) -> bool:
        """验证动作JSON格式是否有效（现在是唯一的验证标准）"""
        try:
            # 必须是字典
            if not isinstance(action_json, dict):
                return False
            
            # 必须包含 'command' 键
            if "command" not in action_json:
                return False
            
            # 验证command值是否有效
            valid_commands = ["CHOOSE", "PLAY", "END", "PROCEED", "POTION"]
            command = action_json.get("command")
            if command not in valid_commands:
                return False
                
            # 根据command类型验证必需参数
            if command == "CHOOSE":
                if "choice_index" not in action_json:
                    return False
                # 检查类型
                if not isinstance(action_json["choice_index"], int):
                    return False
                    
            elif command == "PLAY":
                if "card_index" not in action_json:
                    return False
                # 检查类型
                if not isinstance(action_json["card_index"], int):
                    return False
                # target_index是可选的，但如果存在必须是整数
                if "target_index" in action_json and not isinstance(action_json["target_index"], int):
                    return False
            
            elif command == "POTION":
                if "potion_index" not in action_json:
                    return False
                if not isinstance(action_json["potion_index"], int):
                    return False
                if "target_index" in action_json and not isinstance(action_json["target_index"], int):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _get_fallback_action(self, context: str) -> dict:
        """根据上下文返回默认动作的字典"""
        if "选择" in context or "事件" in context or "地图" in context or "篝火" in context or "商店" in context or "拾取奖励" in context:
            log(f"情境 '{context}' 需要 CHOOSE。默认执行 CHOOSE 0。")
            return {"command": "CHOOSE", "choice_index": 0}
        elif context in ["战斗奖励 - 完成并继续", "即将进入战斗"]:
            log(f"情境 '{context}' 需要 PROCEED。默认执行 PROCEED。")
            return {"command": "PROCEED"}
        elif "战斗中" in context:
            log(f"情境 '{context}' 需要 PLAY/END/POTION。默认执行 PLAY card 0 on enemy 0。")
            return {"command": "PLAY", "card_index": 0, "target_index": 0}
        else:
            log(f"未知情境的回退。默认执行 END。")
            return {"command": "END"}

    def _summarize_map(self, gs: Dict[Any, Any]) -> str:
        """
        将复杂的地图JSON转换为简单的、人类可读的可用路径摘要。
        """
        map_nodes = gs.get("map")
        choice_list = gs.get("choice_list")
        current_floor = gs.get("floor", 0)

        if not map_nodes or not choice_list:
            return "地图信息不可用。"

        node_lookup = {(node['x'], node['y']): node for node in map_nodes}
        path_summaries = []

        try:
            choice_x_coords = [int(re.search(r'\d+', choice).group()) for choice in choice_list]

            for i, x_coord in enumerate(choice_x_coords):
                # 寻找该路径的起始节点。
                # 要选择的节点在当前楼层。
                start_node = node_lookup.get((x_coord, current_floor))

                if not start_node:
                    continue

                path_str = f"路径 {i+1} (选择 {choice_list[i]}): "
                path = []
                
                current_node = start_node
                # 追踪路径5步
                for _ in range(5):
                    if not current_node:
                        break
                    path.append(current_node['symbol'])
                    
                    children = current_node.get('children', [])
                    if not children:
                        break
                    
                    # 为简化规划，如果存在多个子节点，则只跟随第一个。
                    next_node_coords = (children[0]['x'], children[0]['y'])
                    current_node = node_lookup.get(next_node_coords)
                
                path_summaries.append(path_str + " -> ".join(path))

        except (ValueError, AttributeError) as e:
            log(f"解析地图摘要时出错: {e}")
            return "无法生成地图路径摘要。"

        legend = """
地图符号图例:
- M: 普通怪物 (Monster)
- E: 精英 (Elite)
- R: 篝火 (Rest)
- ?: 事件 (Unknown)
- $: 商店 (Merchant)
- T: 宝箱 (Treasure)
"""
        
        return legend + "\n" + "\n".join(path_summaries) if path_summaries else "无法生成地图路径摘要。" 
    
    def _get_context(self, gs: Dict[Any, Any]) -> str:
        """
        根据详细的游戏状态生成精确的上下文，模仿传统AI的逻辑。
        """
        game_state = gs.get("game_state", {})
        screen_type = game_state.get("screen_type")
        room_type = game_state.get("room_type")
        
        # 1. 优先处理最明确的屏幕类型
        if screen_type == ScreenType.BATTLE:
            return "战斗中 - 选择打出手牌或结束回合"
            
        if screen_type == ScreenType.MAP:
            return "地图 - 选择下一个房间"
            
        if screen_type == ScreenType.CARD_REWARD:
            return "选择卡牌奖励"
            
        if screen_type == ScreenType.BOSS_RELIC:
            return "选择Boss遗物"

        if screen_type == ScreenType.SHOP_ROOM:
            # 商店的逻辑比较复杂，可以根据选项细分
            choices = game_state.get("choice_list", [])
            if not choices or "leave" in choices: # 假设 "leave" 在主界面
                 return "商店 - 主界面"
            elif any("remove" in c.lower() for c in choices):
                 return "商店 - 选择移除卡牌"
            else:
                 return "商店 - 购买" # 其他情况默认为购买

        if screen_type == ScreenType.REST:
            return "篝火 - 休息或升级"
            
        if screen_type == ScreenType.CHEST:
            return "宝箱 - 打开或离开"

        if screen_type == ScreenType.COMBAT_REWARD:
            return "战斗奖励 - 拾取奖励并继续"
        
        # 2. 处理事件，这是最复杂的
        if screen_type == ScreenType.EVENT:
            event_name = game_state.get("event_name", "未知事件")
            # 可以根据事件名称返回更具体的上下文
            return f"事件 - {event_name}"

        # 3. 处理特殊的过渡/非标准状态
        if screen_type == ScreenType.NONE:
            if room_type == "NeowRoom":
                return "事件 - Neow初始事件" # Neow事件的特殊处理
            if room_type == "MonsterRoom":
                return "游戏加载中" # 我们之前修复的逻辑

        if screen_type == ScreenType.GRID:
            return "网格选择 - 选择卡牌"
            
        if screen_type == ScreenType.HAND_SELECT:
            return "手牌选择 - 从手牌中选择一张牌"

        # 4. 回退到通用上下文
        if game_state.get("choice_list"):
            return f"通用选择 - {screen_type}"
        
        return screen_type or "未知状态" 