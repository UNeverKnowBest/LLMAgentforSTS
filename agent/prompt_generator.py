import json
from typing import Dict, Any
from agent import prompts

class PromptGenerator:
    def __init__(self, game_state_data: Dict[str, Any]):
        self.game_state_data = game_state_data

    def get_prompt(self) -> str:
        game_state = self.game_state_data.get("game_state", {})
        screen_type = game_state.get("screen_type", "NONE")

        if game_state.get("room_phase") == "COMBAT" and screen_type == "NONE":
            screen_type = "COMBAT"

        template = {
            "COMBAT": prompts.COMBAT_PROMPT,
            "MAP": prompts.MAP_PROMPT,
            "CARD_REWARD": prompts.CARD_REWARD_PROMPT,
            "REST": prompts.REST_SITE_PROMPT,
            "SHOP_SCREEN": prompts.SHOP_PROMPT,
            "EVENT": prompts.EVENT_PROMPT,
            "COMPLETE": prompts.COMPLETE_PROMPT,
        }.get(screen_type, prompts.GENERIC_PROMPT)

        return template + self._format_context()

    def _format_context(self) -> str:
        return f"\n### Game State Analysis ###\n```json\n{json.dumps(self.game_state_data, indent=2)}\n```"
