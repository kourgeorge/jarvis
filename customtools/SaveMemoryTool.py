import asyncio
from typing import Type, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore


class SaveMemorySchema(BaseModel):
    """Input schema for SaveMemoryTool."""
    memory: str = Field(..., description="The memory string to be saved for the user.")


class SaveMemoryTool(BaseTool):
    """Tool to save user-provided memories into a persistent store."""

    name: str = "save_memory"
    description: str = (
        "Saves a given memory string to the user's memory store. "
        "This tool is used to remember important information shared by the user."
    )
    args_schema: Type[SaveMemorySchema] = SaveMemorySchema

    store: BaseStore
    config: RunnableConfig

    def _run(self, memory: str) -> dict:
        """
        Save the given memory string synchronously.

        Args:
            memory (str): The memory to be saved.

        Returns:
            dict: Result of the save operation.
        """
        try:
            # Retrieve user ID from config
            user_id = self.config.get("configurable", {}).get("user_id")
            if not user_id:
                raise ValueError("User ID is missing in the configuration.")

            # Namespace and key for saving the memory
            namespace = ("memories", user_id)
            memory_key = f"memory_{len(self.store.search(namespace))}"
            self.store.put(namespace, memory_key, {"data": memory})

            return {
                "status": "success",
                "message": f"Memory saved successfully: {memory}"
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while saving memory: {error}",
            }

    async def _arun(self, memory: str) -> dict:
        """
        Save the given memory string asynchronously.

        Args:
            memory (str): The memory to be saved.

        Returns:
            dict: Result of the save operation.
        """
        try:
            # Run _run method in an asynchronous thread
            return await asyncio.to_thread(self._run, memory)
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while saving memory asynchronously: {error}",
            }
