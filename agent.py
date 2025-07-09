import sys
import json

from typing import Annotated
from typing_extensions import TypedDict, List
from llm_agent.prompt_generator import PromptGenerator

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from IPython.display import Image, display

class AgentState(TypedDict):
    game_state_json: str
    final_command: str

llm = ChatOllama(model="qwen3:8b", temperature=0)

def initial_game(state: AgentState):
    return {"final_command": f"start THE_SILENT"}

def read_game_state(state: AgentState):
    try:
        line = sys.stdin.readline()
        if not line:
            return {"final_command": "exit"}
        
        game_state_json= line.strip()
        return {"game_state_json": game_state_json}
    
    except Exception as e:
        return {"final_command": "exit"}

def make_decision(state: AgentState):
    game_state_json = state['game_state_json']
    game_state = json.loads(game_state_json)
    if game_state.get("ready_for_command"):
        prompt_generator = PromptGenerator(game_state_json)
        prompt = prompt_generator.generate_prompt_from_state()
        response = llm.invoke(prompt)
        llm_output = response.content
        lines = llm_output.strip().split('\n')
        final_command = lines[0].strip() if lines else "state"
        return {"final_command": final_command}
    
    else:
        return {"final_command": "wait 10"}

def excute_command(state: AgentState):
    command = state['final_command']
    print(command)
    sys.stdout.flush()
    return {}

def check_running(state: AgentState):
    if state["game_state_json"].get("in_game", False):
        return "Continue"
    else:
        return "Stop"

workflow = StateGraph(AgentState)
workflow.add_node("read_state", read_game_state)
workflow.add_node("make_decision", make_decision)
workflow.add_node("execute_command", excute_command)

workflow.add_edge(START, "read_state")
workflow.add_conditional_edges(
    "read_state", check_running, {"Continue": "make_decision", "Stop": END}
)

workflow.add_edge("make_decision", "execute_command")
workflow.add_edge("execute_command", "read_state")

chain = workflow.compile()
display(Image(chain.get_graph().draw_mermaid_png()))
state = chain.invoke()
