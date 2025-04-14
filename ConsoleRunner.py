import asyncio

from langchain_openai import AzureChatOpenAI
from sentinel import LLMSecretDetector, instrument_model_class

from conversation_history_manager import ConversationHistoryManager
from conversation_manager import ConversationManager
from personal_assistant import PersonalAssistant
from dotenv import load_dotenv


class ChatbotRunner:
    def __init__(self, assistant):
        self.assistant = assistant
        self.conversation_manager = ConversationManager(self.assistant)
        self.conversation_history_manager = ConversationHistoryManager()

    async def run(self):
        if not self.assistant.agent:
            print("Please initialize the assistant first.")
            return

        print("Type 'exit' or 'quit' to end the chat.")
        while True:
            # Use asynchronous input
            user_input = await self.async_input("")
            if await self.conversation_manager.process_input(user_input) is None:
                self.conversation_history_manager.save_conversation(self.conversation_manager)
                break

    @staticmethod
    async def async_input(prompt: str) -> str:
        """Asynchronous wrapper for input."""
        print(prompt, end='', flush=True)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input)


# Example usage
if __name__ == "__main__":
    load_dotenv()


    async def main():
        detector = LLMSecretDetector((AzureChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)))
        WrappedClass = instrument_model_class(AzureChatOpenAI, detector=detector)
        llm = WrappedClass(model="gpt-4o-2024-08-06", temperature=0)

        assistant = PersonalAssistant(user_id='gkour', llm=llm)
        assistant.initialize()  # Await initialization if it is async
        runner = ChatbotRunner(assistant)
        try:
            await runner.run()  # Await run since it is async
        finally:
            await assistant.cleanup()  # Clean up resources asynchronously


    asyncio.run(main())
