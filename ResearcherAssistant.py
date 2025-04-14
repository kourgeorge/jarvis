from langchain.memory import ConversationSummaryBufferMemory
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain import hub

from ready_tools import datetime_tool, search_tool, arxiv_tool, wikipedia_tool, semantic_scholar_wrapper
from keys import OPENAI_KEY
from utils import process_stream


# Initialize the LangChain Agent

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_KEY
)

tools = [search_tool, arxiv_tool, wikipedia_tool, datetime_tool]

summaryllm = ChatOllama(model="llama3.2")
memory = ConversationSummaryBufferMemory(llm=summaryllm, memory_key="chat_history")

# Get the prompt to use - you can modify this!
prompt = hub.pull("ih/ih-react-agent-executor")
prompt.pretty_print()

memory = MemorySaver()
graph = create_react_agent(llm, tools, state_modifier=prompt, checkpointer=memory)

# Run Research Assistant Agent
print(" Assistant is ready!")
config = {"configurable": {"thread_id": "1"}}


while True:
    user_input = input("What Task task can I help you with? ")
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break
    inputs = {"messages": [("user", user_input)]}
    process_stream(graph.stream(inputs, stream_mode="values", config=config))


