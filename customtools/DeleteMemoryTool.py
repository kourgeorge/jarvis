import asyncio
from typing import Type, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore, SearchItem


class DeleteMemorySchema(BaseModel):
    """Input schema for DeleteMemoryTool."""
    memory_key: str = Field(..., description="The key of the memory to be deleted.")


def find_most_relevant_memory(store: BaseStore, namespace: tuple[str, ...], query: str) -> Optional[SearchItem]:
    """Find the most relevant memory matching the query string."""
    results = store.search(
        namespace,
        query=query,
        limit=1  # Just get the top match
    )
    return results[0] if results else None


class DeleteMemoryTool(BaseTool):
    """Tool to delete a specific user memory from the persistent store."""

    name: str = "delete_memory"
    description: str = (
        "Deletes a specific memory from the user's memory store using the provided key. "
        "This is useful for forgetting outdated or incorrect information."
    )
    args_schema: Type[DeleteMemorySchema] = DeleteMemorySchema

    store: BaseStore
    config: RunnableConfig

    def _run(self, memory: str) -> dict:
        """
        Delete the specified memory string synchronously.

        Args:
            memory (str): The str of the memory to be deleted.

        Returns:
            dict: Result of the delete operation.
        """
        try:
            # Retrieve user ID from config
            user_id = self.config.get("configurable", {}).get("user_id")
            if not user_id:
                raise ValueError("User ID is missing in the configuration.")

            namespace = ("memories", user_id)

            most_relevant = find_most_relevant_memory(self.store, namespace, memory)

            if not most_relevant:
                return {"status": "not_found", "message": f"No matching memory for: '{memory}'"}

            self.store.delete(namespace, most_relevant.key)

            return {
                "status": "success",
                "message": f"Memory '{most_relevant.key}' deleted successfully."
            }

        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while deleting memory: {error}",
            }

    async def _arun(self, memory_key: str) -> dict:
        """
        Delete the specified memory string asynchronously.

        Args:
            memory_key (str): The key of the memory to be deleted.

        Returns:
            dict: Result of the delete operation.
        """
        try:
            return await asyncio.to_thread(self._run, memory_key)
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while deleting memory asynchronously: {error}",
            }

