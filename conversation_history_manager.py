import os
import json
from langchain_core.messages import messages_to_dict, messages_from_dict
from typing import List
from conversation_manager import ConversationManager
from personal_assistant import PersonalAssistant


class ConversationHistoryManager:
    def __init__(self, base_directory="conversations", llm=None):
        self.base_directory = base_directory
        self.llm = llm
        os.makedirs(self.base_directory, exist_ok=True)

    def _get_file_path(self, user_id: str, thread_id: str) -> str:
        user_dir = os.path.join(self.base_directory, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"{thread_id}.json")

    def save_conversation(self, conversation: ConversationManager):
        """
        Save the given ConversationManager's conversation history to disk.

        Args:
            conversation (ConversationManager): The conversation manager instance containing user, thread_id, and messages.
        """
        user_id = conversation.personal_assistant.user
        thread_id = conversation.thread_id
        messages = conversation.conversation_messages
        self.save(user_id, thread_id, messages)

    def save(self, user_id: str, thread_id: str, messages: List[List]):
        file_path = self._get_file_path(user_id, thread_id)
        serialized = [messages_to_dict(turn) for turn in messages]

        # Create a summary (e.g., from first user or assistant message)
        summary = self._generate_summary(messages)

        data = {
            "summary": summary,
            "messages": serialized
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _generate_summary(self, messages: List[List]) -> str:
        if not self.llm:
            # Fallback to basic content summary
            for turn in messages:
                for msg in turn:
                    content = getattr(msg, "content", None)
                    if content:
                        return content.strip()[:80] + "..." if len(content) > 80 else content.strip()
            return "No summary available."

        # Convert all turns to flat message list for summarization
        flat_messages = []
        for turn in messages:
            flat_messages.extend(turn)

        # Compose a prompt for summarizing the conversation
        chat_prompt = [{"role": "system", "content": "Summarize this conversation in one short title containing up to 3 words focusing on the User type request."}]
        for msg in flat_messages:
            role = "user" if msg.type == "human" else "assistant"
            chat_prompt.append({"role": role, "content": msg.content})

        try:
            response = self.llm(chat_prompt)
            # Check if response is a string or an object with a 'content' attribute
            if isinstance(response, str):
                summary = response
            else:
                summary = getattr(response, "content", "")
            return summary.strip()
        except Exception as e:
            print(f"[Warning] Failed to generate summary using LLM: {e}")
            return "Summary unavailable"

    def load(self, personal_assistant: PersonalAssistant, user_id: str, thread_id: str) -> ConversationManager:
        file_path = self._get_file_path(user_id, thread_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
                serialized = raw["messages"] if isinstance(raw, dict) and "messages" in raw else raw
                messages = [messages_from_dict(turn) for turn in serialized]
                return ConversationManager(personal_assistant, thread_id=thread_id, messages=messages)
        return ConversationManager(personal_assistant)

    def delete_conversation(self, user_id: str, thread_id: str) -> bool:
        """
        Delete the conversation file for the given user and thread ID.

        Args:
            user_id (str): The ID of the user.
            thread_id (str): The ID of the conversation thread.

        Returns:
            bool: True if the file was successfully deleted, False otherwise.
        """
        file_path = self._get_file_path(user_id, thread_id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(f"[Error] Failed to delete conversation file: {e}")
                return False
        else:
            print(f"[Warning] Conversation file does not exist: {file_path}")
            return False

    def list_threads(self, user_id: str) -> List[str]:
        user_dir = os.path.join(self.base_directory, user_id)
        if not os.path.exists(user_dir):
            return []
        return [f[:-5] for f in os.listdir(user_dir) if f.endswith(".json")]

    def get_summary(self, user_id: str, thread_id: str) -> str:
        file_path = self._get_file_path(user_id, thread_id)
        if not os.path.exists(file_path):
            return thread_id
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data.get("summary", "thread_id")
            except Exception:
                return thread_id
