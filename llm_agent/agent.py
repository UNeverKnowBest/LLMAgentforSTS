from typing import Annotated
from typing_extensions import TypedDict, List
from prompt_generator import PromptGenerator
from 

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate

class AgentState(TypedDict):
    game_state_json: str
    final_command: str
    history: List[BaseMessage]

llm = ChatOllama(model="qwen3:8b", temperature=0)

def make_decision(state: AgentState):
    game_state_json = state['game_state_json']
    prompt_generator = PromptGenerator(game_state_json)
    prompt = prompt_generator.generate_prompt_from_state()
    response = llm.invoke(prompt)
    llm_output = response.content
    lines = llm_output.strip().split('\n')
    final_command = lines[0].strip() if lines else "state"
    state['final_command'] = final_command
    return state

def 
        
workflow = StateGraph(AgentState)
