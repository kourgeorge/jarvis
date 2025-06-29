# python
import os
import asyncio

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from sentinel import LLMSecretDetector, instrument_model_class
from personal_assistant import PersonalAssistant
from langchain_openai import AzureChatOpenAI
from conversation_manager import ConversationManager
from conversation_history_manager import ConversationHistoryManager


async def start(update, context):
    await update.message.reply_text("Hello! I am your personal assistant.")


async def handle_message(update, context):
    conv_manager = context.application.bot_data['conversation_manager']
    history_manager = context.application.bot_data['conversation_history_manager']
    message = update.message

    # Check if the message contains a document
    if message.document:
        # Download the file to a local 'downloads' directory
        file = await message.document.get_file()
        os.makedirs("downloads", exist_ok=True)
        file_path = os.path.join("downloads", message.document.file_name)
        await file.download_to_drive(custom_path=file_path)
        try:
            if file.file_path.lower().endswith('.pdf'):
                # If the file is a PDF, we will read its content
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    file_content = "\n".join(doc.page_content for doc in docs)
                except Exception as e:
                    await update.message.reply_text(f"Could not read the PDF file: {e}")
                    return
            # Read file content (assuming it's a text file)
            elif file.mime_type.startswith("text/") or file.type.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

            conversation_response = await conv_manager.process_input(file_content)
        except Exception as e:
            await update.message.reply_text(f"Could not read the file: {e}")
            return
    else:
        # Process text input
        user_text = message.text
        conversation_response = await conv_manager.process_input(user_text)

    if conversation_response is None:
        history_manager.save_conversation(conv_manager)
        await update.message.reply_text("Conversation ended. History saved.")
    else:
        await update.message.reply_text(conversation_response[-1].content)


async def main():
    load_dotenv()

    # Initialize LLM with secret detector instrumentation
    # detector = LLMSecretDetector((AzureChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)))
    # WrappedClass = instrument_model_class(AzureChatOpenAI, detector=detector)
    llm = AzureChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)

    # Initialize PersonalAssistant
    assistant = PersonalAssistant(user_id='gkour', llm=llm)
    await assistant.initialize()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # Create conversation managers and save them in bot_data
    conv_manager = ConversationManager(assistant)
    history_manager = ConversationHistoryManager()
    app.bot_data['assistant'] = assistant
    app.bot_data['conversation_manager'] = conv_manager
    app.bot_data['conversation_history_manager'] = history_manager

    # Add handlers for commands and messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL & ~filters.COMMAND, handle_message))

    print("Bot is polling...")
    await app.run_polling()
    await assistant.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
