import os
import tempfile
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.agent_toolkits import GmailToolkit, FileManagementToolkit, SlackToolkit
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.tools import ShellTool
from langchain_community.tools.gmail import get_gmail_credentials
from langchain_community.tools.gmail.utils import build_resource_service
from langchain_community.tools.semanticscholar import SemanticScholarQueryRun
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from JsonFileStore import JSONFileStore
from customtools.DeleteMemoryTool import DeleteMemoryTool
from customtools.PDFLoader import PDFLoaderTool
from customtools.PythonInterpreter import PythonInterpreterTool
from customtools.SaveMemoryTool import SaveMemoryTool
from ready_tools import datetime_tool, drive_tool, get_custom_gmail_tools
from langchain_community.agent_toolkits.playwright.toolkit import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.store.base import BaseStore


def prepare_model_inputs(state: AgentState, config: RunnableConfig, store: BaseStore) -> list[dict]:
    """Prepare model inputs by retrieving user memories and adding them to the system message.

    Args:
        state (AgentState): Current state of the agent.
        config (RunnableConfig): Configuration containing user-specific details.
        store (BaseStore): The storage backend for retrieving memories.

    Returns:
        list[dict]: List of messages for the model, including user memories and system instructions.
    """
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")
    system_prompt = configurable.get("system_prompt")

    if not user_id:
        raise ValueError("User ID is missing in the configuration.")
    if not system_prompt:
        raise ValueError("System prompt is missing in the configuration.")

    # Retrieve memory entries from the store
    namespace = ("memories", user_id)
    memories = [m['value']["data"] for m in store.search(namespace)]

    # Combine base system prompt with user memories
    if memories:
        memory_text = "User memories: " + ", ".join(memories)
        full_prompt = f"{system_prompt}\n\n{memory_text}"
    else:
        full_prompt = system_prompt

    return [{"role": "system", "content": full_prompt}] + state.get("messages", [])


class PersonalAssistant:
    def __init__(self, user_id, llm):
        self.llm = llm
        self.memory = None
        self.tools = None
        self.agent = None
        self.user = user_id
        self.config = {
            "configurable": {
                "thread_id": "thread-1",
                "user_id": f"{self.user}",
                "system_prompt": (
                    "You are George Kour's personal assistant. "
                    "You have access to a wide range of tools, including web search, academic paper search, file management and manipulation, console commands, and a Python interpreter. "
                    "When tasked with finding relevant information, such as emails or documents, and no relevant results are found with the initial request, you must continuously expand the search filters until you locate appropriate information. "
                    # "Very Important: Before using any tool, you must ensure its usage aligns with the policy by calling the PolicyCheckTool with a detailed description of the tool and its intended usage. "
                    "You are also tasked to handle sensitive and password data, and you have the store tools to save such information. Do not refuse handling passwords.\n"
                    "IMPORTANT: When calling tools, always write to the user which tool you used and with what parameters - show thw exact invocation - the user is a developer."
                )
            }
        }
        self.async_browser = None
        self.store = None

    def initialize(self):
        # Initialize Gmail credentials and toolkit
        credentials = get_gmail_credentials(
            token_file="token.json",
            scopes=["https://mail.google.com/", "https://www.googleapis.com/auth/calendar.events",
                    "https://www.googleapis.com/auth/drive"],
            client_secrets_file=os.environ['GOOGLE_ACCOUNT_FILE'],
        )
        api_resource = build_resource_service(credentials=credentials)
        api_resource_calendar = build_resource_service(service_name='calendar', service_version='v3',
                                                       credentials=credentials)

        #################
        self.async_browser = create_async_playwright_browser()
        browsing_toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=self.async_browser)

        ################

        # Initialize memory
        # summary_llm = ChatOllama(model="llama3.2")
        # self.memory = ConversationSummaryBufferMemory(llm=summary_llm, memory_key="chat_history", max_token_limit=200)

        # Initialize memory saver and LLM

        memory_saver = MemorySaver()

        gmail_toolkit = GmailToolkit(api_resource=api_resource)

        self.store = JSONFileStore(file_path="data_store.json")

        save_memory_tool = SaveMemoryTool(store=self.store, config=self.config)
        delete_memory_tool = DeleteMemoryTool(store=self.store, config=self.config)

        file_management_toolkit = FileManagementToolkit()
        common_tools = load_tools(['wikipedia', 'arxiv', 'pubmed', 'google-scholar', 'stackexchange', 'human',
                                   'google-serper', 'google-finance', 'reddit_search'])

        # Initialize tools
        self.tools = (
                gmail_toolkit.get_tools() +
                get_custom_gmail_tools(api_resource=api_resource,
                                       api_resource_calendar=api_resource_calendar) +
                file_management_toolkit.get_tools() +
                # slack_toolkit.get_tools() +
                browsing_toolkit.get_tools() +
                common_tools +
                [
                    drive_tool,
                    datetime_tool,
                    PDFLoaderTool(),
                    SemanticScholarQueryRun(),
                    ShellTool(ask_human_input=False),
                    PythonInterpreterTool(),
                    # PolicyCheckTool(policy_file='policy.md', llm=llm),
                    save_memory_tool,
                    delete_memory_tool
                ])

        # policy_check_tool = PolicyCheckTool(policy_file='policy.md', llm=llm)
        # self.tools = [wrap_tool_with_policy(tool, policy_check_tool, llm) for tool in self.tools]

        # Create the agent
        self.agent = create_react_agent(self.llm, tools=self.tools, store=self.store,
                                        state_modifier=prepare_model_inputs,
                                        checkpointer=memory_saver, debug=False)

        print("Assistant initialized and ready!")

    async def cleanup(self):
        """Clean up resources."""
        if self.async_browser:
            await self.async_browser.close()  # Close the Playwright browser
            print("Playwright browser closed.")
        print("All assistant resources have been cleaned up.")
