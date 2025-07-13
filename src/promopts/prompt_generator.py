class PromptGenerator:
    def __init__(self, game_state: str) -> None:
        self.game_state = game_state
    
    def generate_prompt_based_on_state(self) -> str:
        screen_type = self.game_state.get("screen_type", "NONE")
        if screen_type == "MAP":
            prompt = MAP_PROMPT_TEMPLATE
            

        elif screen_type == "CARD_REWARD":
            prompt = CARD_REWARD_PROMPT_TEMPLATE
            
        
        elif screen_type == "REST":
            prompt = REST_SITE_PROMPT_TEMPLATE
            
        
        elif screen_type == "SHOP_SCREEN":
            prompt = SHOP_PROMPT_TEMPLATE
            
        
        elif screen_type == "EVENT":
            prompt = EVENT_PROMPT_TEMPLATE
                     
        else: 
            if 
            prompt = GENERIC_PROMPT_TEMPLATE
        
            