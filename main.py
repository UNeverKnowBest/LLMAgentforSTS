#!/usr/bin/env python3

import sys
import logging
from src.graph.builder import agent

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
    logger.info("Starting Fixed STS Agent...")
    
    try:
        current_state = {
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
        
        logger.info("Agent initialized, starting communication loop...")
        result = agent.invoke(current_state)
        logger.info("STS Agent workflow completed normally")
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user (Ctrl+C)")
    except BrokenPipeError:
        logger.info("Broken pipe - mod likely disconnected")
    except EOFError:
        logger.info("EOF received - mod terminated")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("STS Agent terminated")

if __name__ == "__main__":
    main() 