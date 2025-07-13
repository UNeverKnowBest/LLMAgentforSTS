# agent_graph.py
import sys
import json
from typing import TypedDict, Dict, Any

from langgraph.graph import StateGraph
from langchain_core.messages import SystemMessage
from langchain_community.chat_models import ChatOllama
from .prompt_generator import PromptGenerator

class AgentState(TypedDict):
    game_state_json_str: str
    final_command: str

def read_game_state(state: AgentState) -> AgentState:
    line = sys.stdin.readline()
    if not line:
        return {**state, "final_command": "exit"}
    state['game_state_json_str'] = line.strip()
    return state

def make_decision(state: AgentState) -> AgentState:
    game_state_data = json.loads(state['game_state_json_str'])

    # Handle special case: Character selection screen
    if game_state_data.get("screen_type") == "CHARACTER_SELECT":
        # If we are at the character selection screen, we must choose a character to start.
        # Let's pick "THE_SILENT" for now.
        print("Detected character selection screen. Choosing THE_SILENT.", file=sys.stderr)
        return {**state, "final_command": "start THE_SILENT"}

    if not game_state_data.get("ready_for_command"):
        return {**state, "final_command": "wait 10"}

    prompt_generator = PromptGenerator(game_state_data)
    prompt = prompt_generator.get_prompt()

    try:
        llm = ChatOllama(model="qwen3:8b", temperature=0)
        response = llm.invoke([SystemMessage(content=prompt)])
        llm_output = response.content
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        llm_output = "state"

    lines = llm_output.strip().split('\n')
    final_command = lines[-1].strip() if lines else "state"
    
    state['final_command'] = final_command
    return state

def execute_command(state: AgentState) -> AgentState:
    command = state['final_command']
    if command != "exit":
        print(command, flush=True)
    return state

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("read_state", read_game_state)
    workflow.add_node("make_decision", make_decision)
    workflow.add_node("execute_command", execute_command)

    workflow.set_entry_point("read_state")
    workflow.add_edge("read_state", "make_decision")
    workflow.add_edge("make_decision", "execute_command")
    workflow.add_edge("execute_command", "read_state")

    return workflow.compile()
