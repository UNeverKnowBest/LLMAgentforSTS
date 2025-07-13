import sys

try:
    from IPython.display import Image, display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

from agent.agent_graph import create_graph, AgentState

def run_agent():
    """
    Initializes and runs the Slay the Spire agent.
    """
    # 1. Signal readiness to CommunicationMod
    # This handshake is critical for the mod to start sending game states.
    # It should be the VERY FIRST thing the agent does.
    print("ready", flush=True)
    print("start THE_SILENT", flush=True)

    # 2. Create the compiled LangGraph agent from the graph definition
    app = create_graph()

    # 3. (Optional) Visualize the graph if running in a compatible environment
    if IPYTHON_AVAILABLE:
        try:
            # This will generate and display a diagram of the agent's workflow
            print("Visualizing agent graph...", file=sys.stderr)
        except Exception as e:
            # Mermaid/graphviz might not be installed or configured
            print(f"Graph visualization failed: {e}", file=sys.stderr)

    # 4. Define the initial state for the graph
    initial_state = AgentState(game_state_json_str="", final_command="")

    # 5. Run the agent in a continuous loop
    # The stream will block and wait for input from stdin (the game)
    # and process each state change as it comes in.
    print("Agent is running. Waiting for game states...", file=sys.stderr)
    try:
        app.invoke()
    except KeyboardInterrupt:
        print("\nAgent stopped by user.", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
    finally:
        print("\nAgent shutting down.", file=sys.stderr)


if __name__ == "__main__":
    run_agent()
