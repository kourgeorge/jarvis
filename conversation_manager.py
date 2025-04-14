import tempfile
import uuid
from typing import List

from langchain_community.document_loaders import PyPDFLoader

from personal_assistant import PersonalAssistant
from langsmith import traceable
from utils import process_stream
from langchain_core.messages import BaseMessage


class ConversationManager:
    """
    Manages a single conversation session: processing input, maintaining message history.
    """

    def __init__(self, personal_assistant: PersonalAssistant, thread_id: str = None,
                 messages: List[List[BaseMessage]] = None):
        self.thread_id = thread_id or str(uuid.uuid4())
        self.personal_assistant = personal_assistant
        self.conversation_messages = messages or []

    @traceable
    async def process_input(self, user_input, uploaded_files=None, add_message_hook=None):
        """
        Handles user input and optional uploaded files, then streams assistant response.
        """
        # ... [existing uploaded files handling logic remains the same]
        # Process uploaded files and append them as messages

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            return None

        messages = [("user", user_input)]

        if uploaded_files:
            for file in uploaded_files:
                try:
                    if file.type.startswith("text/") or file.type.endswith(".txt"):
                        file_content = file.read().decode("utf-8")
                        messages.append(("user", f"Uploaded file `{file.name}`:\n\n{file_content}"))
                    elif file.type == "application/pdf":
                        # Save the uploaded PDF to a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(file.read())
                            tmp_file_path = tmp_file.name

                        # Load the PDF content using PyPDFLoader
                        loader = PyPDFLoader(tmp_file_path)
                        pages = loader.load()

                        # Concatenate page content into one string
                        pdf_content = "\n\n".join(page.page_content for page in pages)

                        messages.append(("user", f"Uploaded PDF `{file.name}`:\n\n{pdf_content.strip()}"))

                    else:
                        messages.append(("user", f"[{file.name}] uploaded, but preview not supported."))
                except Exception as e:
                    messages.append(("user", f"Failed to read `{file.name}`: {str(e)}"))

        inputs = {"messages": messages}
        message = await process_stream(
            self.personal_assistant.agent.astream(inputs, stream_mode="values", config=self.personal_assistant.config),
            add_message_hook
        )

        self.conversation_messages.append(message)
        return message
