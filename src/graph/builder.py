from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .states import GameState
from .nodes import (
    initial_game,
    read_state,
    advice_on_command,
    validate_command,
    handle_validation_failure,
    execute_command,
    execute_fallback_command,
    request_state_update
)

def create_sts_agent():
    workflow = StateGraph(GameState)
    
    # Add nodes
    workflow.add_node("initial_game", initial_game)
    workflow.add_node("read_state", read_state)
    workflow.add_node("advice_on_command", advice_on_command)
    workflow.add_node("validate_command", validate_command)
    workflow.add_node("handle_validation_failure", handle_validation_failure)
    workflow.add_node("execute_command", execute_command)
    workflow.add_node("execute_fallback_command", execute_fallback_command)
    
    # Define the workflow
    workflow.add_edge(START, "initial_game")
    workflow.add_edge("initial_game", "read_state")
    
    # Main game loop
    def should_continue_reading(state: GameState):
        game_state_json = state.game_state_json
        if not game_state_json:
            return "read_state"
        
        game_state = game_state_json.get("game_state", {})
        if game_state.get("screen_type") == "GAME_OVER":
            return END
            
        return "advice_on_command"
    
    workflow.add_conditional_edges(
        "read_state",
        should_continue_reading,
        {
            "read_state": "read_state",
            "advice_on_command": "advice_on_command",
            END: END
        }
    )
    
    workflow.add_edge("advice_on_command", "validate_command")
    
    # Conditional routing based on validation result
    def route_after_validation(state: GameState):
        validation_result = state.validation_result or {}
        if validation_result.get("is_valid", False):
            return "execute_command"
        else:
            return "handle_validation_failure"
    
    workflow.add_conditional_edges(
        "validate_command",
        route_after_validation,
        {
            "execute_command": "execute_command",
            "handle_validation_failure": "handle_validation_failure"
        }
    )
    
    # After command execution, return to reading state
    workflow.add_edge("execute_command", "read_state")
    
    # After handling validation failure, execute fallback command
    workflow.add_edge("handle_validation_failure", "execute_fallback_command")
    workflow.add_edge("execute_fallback_command", "read_state")
    
    # Add memory saver for state persistence
    memory = MemorySaver()
    agent = workflow.compile(checkpointer=memory)
    
    return agent

# Create the agent instance
sts_agent = create_sts_agent()