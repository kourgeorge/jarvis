import asyncio
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from langchain_experimental.utilities import PythonREPL


class PythonInterpreterSchema(BaseModel):
    """Input schema for PythonInterpreter."""
    code: str = Field(..., description="Python code to execute. Use print() to display results.")


class PythonInterpreterTool(BaseTool):
    """Tool to execute Python code in a REPL."""

    name: str = "python_interpreter"
    description: str = (
        "A Python REPL to execute arbitrary Python code. Input should be valid Python code. "
        "If you want to see the output of an expression, you must use print(). Use with caution."
    )
    args_schema: Type[PythonInterpreterSchema] = PythonInterpreterSchema

    # Define a private attribute for the Python REPL
    _python_repl: PythonREPL = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._python_repl = PythonREPL()

    def _run(self, code: str) -> dict:
        """
        Synchronously execute Python code in a REPL.

        Args:
            code (str): The Python code to execute.

        Returns:
            dict: The result or error message.
        """
        try:
            # Execute the Python code
            result = self._python_repl.run(code)
            return {
                "status": "success",
                "message": "Code executed successfully.",
                "result": result.strip(),
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while executing the code: {error}",
            }

    async def _arun(self, code: str) -> dict:
        """
        Asynchronously execute Python code in a REPL.

        Args:
            code (str): The Python code to execute.

        Returns:
            dict: The result or error message.
        """
        try:
            # Use asyncio to run the blocking code execution in a separate thread
            result = await asyncio.to_thread(self._python_repl.run, code)
            return {
                "status": "success",
                "message": "Code executed successfully.",
                "result": result.strip(),
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"An error occurred while executing the code: {error}",
            }


# Example Usage
if __name__ == "__main__":
    # Initialize the PythonInterpreterTool
    python_tool = PythonInterpreterTool()

    # Define the Python code
    code = "print(1 + 1)"

    # Run the tool
    result = python_tool._run(code=code)

    # Print the result
    if result["status"] == "success":
        print("Execution Result:")
        print(result["result"])
    else:
        print("Error:", result["message"])
