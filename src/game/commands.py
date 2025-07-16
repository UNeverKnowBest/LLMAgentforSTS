from typing import Dict, Optional
from .game_constants import ScreenType

SIMPLE_COMMAND_MAP: Dict[ScreenType, str] = {
    ScreenType.CHEST: "choose open",
    ScreenType.SHOP_ROOM: "choose shop",
    ScreenType.COMPLETE: "proceed",
    ScreenType.GAME_OVER: "end",
}

def _get_simple_command(screen_type: ScreenType) -> Optional[str]:
    return SIMPLE_COMMAND_MAP.get(screen_type)


