import streamlit as st
import asyncio

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import ToolMessage
from langchain.schema import HumanMessage, AIMessage
from dotenv import load_dotenv
import yaml
import streamlit_authenticator as stauth

from conversation_manager import ConversationManager
from conversation_history_manager import ConversationHistoryManager
from personal_assistant import PersonalAssistant
from sentinel import LLMSecretDetector
from sentinel.wrappers import instrument_model_class

# Load environment variables
load_dotenv()

# Load authentication config
with open('config.yaml') as file:
    config = yaml.safe_load(file)

# Authenticate user
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)
authenticator.login(location='main', key='Login')

authentication_status = st.session_state.get("authentication_status")

if authentication_status is not True:
    if authentication_status is False:
        st.error("Username/password is incorrect")
    else:
        st.warning("Please enter your username and password")
    st.stop()

# Authenticated session
name = st.session_state.get("name")
username = st.session_state.get("username")

# st.title(f"{name}'s Personal Assistant")

llm = AzureChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)

# Initialize assistant and conversation
if "assistant" not in st.session_state:
    st.session_state.assistant = PersonalAssistant(user_id=username, llm=llm)
    st.session_state.assistant.initialize()

if "conversation" not in st.session_state:
    st.session_state.conversation = ConversationManager(st.session_state.assistant)

conversation_history_manager = ConversationHistoryManager(llm=llm)
conversation = st.session_state.conversation

selected_thread_id = None  # define this at top of sidebar block

assistant = st.session_state.assistant
thread_ids = conversation_history_manager.list_threads(username)

with st.sidebar:

    col1, col2 = st.columns([0.8,0.2])
    col1.success(f"{name} ({username})")

    with col2:
        if st.button("Logout", use_container_width=True):
            authenticator.logout(location='main', key='Logout')
            st.session_state.set("authentication_status", False)
            st.rerun()

    col1, col2, col3 = st.columns([0.6, 0.1, 0.1])
    with col1:
        st.header("Saved Conversations")

    with col2:
        if st.button("💬"):
            if len(conversation.conversation_messages) > 0:
                conversation_history_manager.save_conversation(conversation)
            st.session_state.conversation = ConversationManager(assistant)
            st.rerun()

    with col3:
        if st.button("💾", key="save_conversation"):
            conversation_history_manager.save_conversation(st.session_state.conversation)
            st.rerun()

    if thread_ids:
        thread_map = {tid: conversation_history_manager.get_summary(user_id=username, thread_id=tid) for tid in
                      thread_ids}
        friendly_names = list(thread_map.values())

        for thread_id in thread_ids:
            cols = st.columns([0.6, 0.1, 0.1])
            with cols[0]:
                st.markdown(f"🧵 {thread_map[thread_id]}")
            with cols[1]:
                if st.button("📂", key=f"load_{thread_id}"):
                    selected_thread_id = thread_id
                    loaded_convo = conversation_history_manager.load(assistant, username, selected_thread_id)
                    st.session_state.conversation = loaded_convo
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"delete_{thread_id}"):
                    conversation_history_manager.delete_conversation(username, thread_id)
                    st.rerun()


# Main content area for chat panel
chat_container = st.container(border=False, key='chat')


def handle_chat_widget_content(turn, uploaded_files=None):
    """
    Render a full turn (list of BaseMessage) in the Streamlit chat widget.
    """
    for message in turn:
        if isinstance(message, HumanMessage):
            with chat_container.chat_message("user"):
                st.markdown(message.content)
                if uploaded_files:
                    for file in uploaded_files:
                        if file.type.startswith("image/"):
                            st.image(file)
                        else:
                            st.write(f"📄 Uploaded file: `{file.name}`")

        elif isinstance(message, ToolMessage):
            with chat_container.chat_message("tool"):
                st.expander("**Tool Response:**", expanded=False).markdown(message.content)

        elif isinstance(message, AIMessage):
            with chat_container.chat_message("assistant"):
                if message.content:
                    st.markdown(message.content)
                else:
                    tool_calls = message.tool_calls or []
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name", "unknown_tool")
                        tool_args = tool_call.get("args", {})
                        tool_call_message = f"**Tool:** {tool_name} | **Arguments:** {tool_args}"
                        st.markdown(tool_call_message)


# Use the chat container to render the chat widget content
with chat_container:
    for turn in conversation.conversation_messages:
        handle_chat_widget_content(turn)


prompt = st.chat_input(
        "What can I help you with?",
        accept_file=True,
        file_type=["jpg", "jpeg", "png", "txt", "pdf"]
    )

if prompt:
    user_text = prompt["text"]
    uploaded_files = prompt["files"]
    user_message = HumanMessage(content=user_text)
    handle_chat_widget_content(user_message)


    # Run assistant
    async def process_input(prompt_text, uploaded_files, handle_chat_content):
        response_turn = await st.session_state.conversation.process_input(
            prompt_text, uploaded_files, lambda msg: None  # we handle all output below
        )
        if response_turn is None:
            conversation_history_manager.save_conversation(st.session_state.conversation)
        else:
            handle_chat_content(response_turn, uploaded_files)


    asyncio.run(process_input(user_text, uploaded_files, handle_chat_widget_content))
