from langgraph.graph import StateGraph, START, END

from .states import GameState
from .nodes import (
    initial_game,
    read_state,
    advice_on_command,
    execute_command,
    validate_command,
    handle_validation_failure,
    execute_fallback_command
)

def create_agent():

    def should_process_state(state: GameState):
        game_state_json = state.game_state_json
        if game_state_json is None:
            return END
        
        game_state = game_state_json.get("game_state", {})
        # 确保game_state不为None
        if game_state is None:
            game_state = {}
            
        if game_state.get("screen_type") == "GAME_OVER":
            return "advice_on_command"
            
        return "advice_on_command"
    
    def route_after_validation(state: GameState):
        validation_result = state.validation_result or {}
        if validation_result.get("is_valid", False):
            return "execute_command"
        else:
            return "handle_validation_failure"
    
    def after_command_execution(state: GameState):
        game_state_json = state.game_state_json or {}
        game_state = game_state_json.get("game_state", {})
        # 确保game_state不为None
        if game_state is None:
            game_state = {}
        
        if game_state.get("screen_type") == "GAME_OVER":
            return END
        else:
            return "read_state"
        
    workflow = StateGraph(GameState)
    workflow.add_node("initial_game", initial_game)
    workflow.add_node("read_state", read_state)
    workflow.add_node("advice_on_command", advice_on_command)
    workflow.add_node("validate_command", validate_command)
    workflow.add_node("handle_validation_failure", handle_validation_failure)
    workflow.add_node("execute_command", execute_command)
    workflow.add_node("execute_fallback_command", execute_fallback_command)

    workflow.add_edge(START, "initial_game")
    workflow.add_edge("initial_game", "read_state")
    workflow.add_conditional_edges(
        "read_state",
        should_process_state,
        {
            "advice_on_command": "advice_on_command",
            END: END
        }
    )

    workflow.add_edge("advice_on_command", "validate_command")
    workflow.add_conditional_edges(
        "validate_command",
        route_after_validation,
        {
            "execute_command": "execute_command",
            "handle_validation_failure": "handle_validation_failure"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_command",
        after_command_execution,
        {
            "read_state": "read_state",
            END: END
        }
    )

    workflow.add_edge("handle_validation_failure", "execute_fallback_command")
    
    workflow.add_conditional_edges(
        "execute_fallback_command",
        after_command_execution,
        {
            "read_state": "read_state",
            END: END
        }
    )
    
    agent = workflow.compile()
    
    return agent

agent = create_agent() 