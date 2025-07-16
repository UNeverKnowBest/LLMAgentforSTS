#!/usr/bin/env python3

import sys
import logging
from src.graph.builder import sts_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sts_agent.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the STS Agent.
    
    This agent communicates with the CommunicationMod through stdin/stdout:
    - Receives JSON game state from stdin
    - Sends commands to stdout
    - Logs to stderr and sts_agent.log file
    """
    logger.info("Starting STS Agent...")
    
    try:
        # Create initial state
        initial_state = {
            "game_state_json": None,
            "thinking_process": None,
            "final_command": None,
            "command_success": None,
            "error_message": None,
            "is_game_over": None,
            "state_valid": None,
            "validation_result": None,
            "fallback_command": None
        }
        
        # Configuration for the agent run
        config = {
            "configurable": {
                "thread_id": "sts_session_1"
            }
        }
        
        logger.info("Agent initialized, starting game loop...")
        
        for state_dict in sts_agent.stream(initial_state, config=config):
            for node_name, state in state_dict.items():
                if hasattr(state, 'error_message') and state.error_message:
                    logger.error(f"Agent error: {state.error_message}")
                    return
                
                if hasattr(state, 'is_game_over') and state.is_game_over:
                    logger.info("Game over detected, agent stopping")
                    return
                
    except KeyboardInterrupt:
        logger.info("Agent stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("STS Agent terminated")

if __name__ == "__main__":
    main()
