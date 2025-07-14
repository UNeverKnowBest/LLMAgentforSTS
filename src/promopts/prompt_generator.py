from typing import Dict, Optional, Callable, Tuple
from game.game_constants import ScreenType

class PromptGenerator:
    def __init__(self, game_state: str) -> None:
        self.game_infos = game_state
        self.game_state = self.game_infos.get("game_state", {})

        self.simple_command_map: Dict[ScreenType, str] = {
            ScreenType.CHEST: "choose open",
            ScreenType.SHOP_ROOM: "choose shop",
            ScreenType.COMPLETE: "proceed",
            ScreenType.GAME_OVER: "end",
        }       

        self._context_formatter_map: Dict[ScreenType, Callable[[], str]] = {
            ScreenType.COMBAT: self._format_combat_context,
            ScreenType.MAP: self._format_map_context,
            ScreenType.CARD_REWARD: self._format_card_reward_context,
            ScreenType.REST: self._format_rest_site_context,
            ScreenType.SHOP_SCREEN: self._format_shop_context,
            ScreenType.EVENT: self._format_event_context,
            ScreenType.BOSS_REWARD: self._format_boss_reward_context,
            ScreenType.GRID: self._format_grid_context,
            ScreenType.HAND_SELECT: self._format_hand_select_context,
            ScreenType.COMBAT_REWARD: self._format_combat_reward_context,
        }

    def get_command_or_promopt(self) -> Tuple[Optional[str], Optional[str]]:
        if command := self._simple_command_map.get(self.screen_type):
            return command, None

        if handler := self._prompt_handler_map.get(self.screen_type):
            prompt = handler()
            return None, prompt
        
        return "state", None

    def _get_effective_screen_type(self) -> ScreenType:
        screen_type = self.game_state.get("screen_type", "NONE")
        room_phase = self.game_state.get("room_phase")

        if screen_type == "NONE" and room_phase == "COMBAT":
            return ScreenType.COMBAT
        
        try:
            return ScreenType(screen_type)
        except ValueError:
            return ScreenType.NONE
        
    def _generate_combat_promopt(self):
        pass
    
    def _get_simple_command(self) -> str:
        return self.SIMPLE_COMMAND_MAP.get(self.screen_type)
    
    def _format_combat_reward_context(self) -> str:
        context = f"\n### CURRENT CONTEXT\n{self._format_core_status()}\n"
        screen_state = self.game_state.get("screen_state", {})
        context += "**Combat Rewards:**\n"
        for reward in screen_state.get("rewards", []):
            reward_type = reward.get('reward_type')
            if reward_type == "GOLD":
                context += f"- Gold: {reward.get('gold')} gold\n"
            elif reward_type == "RELIC":
                 context += f"- Relic: {reward.get('relic', {}).get('name')}\n"
            elif reward_type == "POTION":
                 context += f"- Potion: {reward.get('potion', {}).get('name')}\n"
            elif reward_type == "CARD":
                 context += f"- Card Reward\n"
        context += "**Available Commands**: `choose <reward_type>`, `proceed`\n"
        return context
    
    def _format_combat_context(self) -> str:
        context = f"\n### CURRENT CONTEXT\n{self._format_core_status()}\n"
        combat_state = self.game_state.get("combat_state", {})
        player = combat_state.get("player", {})
        
        hand_str = ", ".join([f"'{c.get('name')}'({c.get('cost')}E)" for c in combat_state.get("hand", [])])
        powers_str = ", ".join([f"{p.get('name')}({p.get('amount')})" for p in player.get("powers", [])])
        context += (
            f"**Player Combat**: Energy: {player.get('energy', 0)}, Block: {player.get('block', 0)}\n"
            f"**Hand ({len(combat_state.get('hand',[]))} cards)**: {hand_str}\n"
            f"**Draw Pile**: {len(combat_state.get('draw_pile',[]))} cards | **Discard Pile**: {len(combat_state.get('discard_pile',[]))} cards\n"
            f"**Active Powers**: {powers_str if powers_str else 'None'}\n\n"
        )

        context += "**Enemies:**\n"
        total_incoming_damage = 0
        for i, m in enumerate(combat_state.get("monsters", [])):
            if not m.get('is_gone'):
                intent_damage = m.get('move_adjusted_damage', 0) if "ATTACK" in m.get('intent', '') else 0
                intent_hits = m.get('move_hits', 1)
                total_damage = intent_damage * intent_hits
                total_incoming_damage += total_damage
                
                intent_str = f"Intent: {m.get('intent', '?')}"
                if total_damage > 0:
                    intent_str += f" for {total_damage} damage ({intent_damage}x{intent_hits})"
                
                monster_powers = ", ".join([f"{p.get('name')}({p.get('amount')})" for p in m.get("powers", [])])
                context += (
                    f"- **Enemy {i}**: '{m.get('name')}' | HP: {m.get('current_hp')}/{m.get('max_hp')} | Block: {m.get('block', 0)}\n"
                    f"  - {intent_str}\n"
                    f"  - Powers: {monster_powers if monster_powers else 'None'}\n"
                )
        context += f"\n**Total Incoming Damage This Turn: {total_incoming_damage}**\n"
        return context
    
    def _format_core_status(self) -> str:
        relics = ", ".join([r.get("name", "?") for r in self.game_state.get("relics", [])])
        return (
            f"**Run Status**: Act {self.game_state.get('act', '?')}, Floor {self.game_state.get('floor', '?')}\n"
            f"**Health**: {self.game_state.get('current_hp', '?')} / {self.game_state.get('max_hp', '?')}\n"
            f"**Gold**: {self.game_state.get('gold', '?')}\n"
            f"**Relics**: {relics}\n"
        )
    
    