from typing import Type, Tuple

from langchain_community.llms.ollama import Ollama
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


class PolicyCheckSchema(BaseModel):
    """Input schema for PolicyCheck."""
    request: str = Field(..., description="The user request to validate against the policy.")
    tool_description: str = Field(..., description="Description of the tool the user intends to invoke.")


class PolicyCheckTool(BaseTool):
    """Tool to check if a request adheres to a predefined policy using an LLM."""

    name: str = "policy_check"
    description: str = "Validates if a tool invocation complies with the policy defined in policy.md. If it doesn't, it provides instructions or prohibits the invocation. This tool shoudld be invoked before every Tool invocation to validate compliance."
    args_schema: Type[PolicyCheckSchema] = PolicyCheckSchema

    # Add the necessary fields
    policy_file: str = Field(..., description="Path to the policy file.")
    llm: BaseChatModel = Field(..., description="The LLM instance used for evaluating the policy.")

    def _load_policy(self) -> str:
        """Loads the policy content from the file."""
        try:
            with open(self.policy_file, "r") as file:
                return file.read()
        except FileNotFoundError:
            raise Exception(f"Policy file '{self.policy_file}' not found.")
        except Exception as error:
            raise Exception(f"An error occurred while loading the policy: {error}")

    def _evaluate_policy_with_llm(self, request: str, tool_description: str) -> str:
        """
        Uses an LLM to evaluate the policy and determine if the invocation is compliant.

        Args:
            request (str): The user request.
            tool_description (str): Description of the tool to invoke.

        Returns:
            str: The LLM's response indicating compliance, prohibition, or required actions.
        """
        # Construct the prompt for the LLM
        prompt = f"""
Policy:
{self._load_policy()}

User Request:
{request}

Tool Description:
{tool_description}

Question:
Is invoking this tool in the described way compliant with the policy? If it is prohibited or requires additional actions, please explain in detail what the agent should do before invoking the tool.
"""
        # Get the LLM response
        response = self.llm.invoke(prompt)
        return response

    def _run(self, request: str, tool_description: str) -> str:
        """Run the policy check."""
        try:
            # Use LLM to evaluate the policy
            evaluation = self._evaluate_policy_with_llm(request, tool_description)

            # Parse and return the LLM's response
            return f"Policy evaluation result:\n{evaluation}"
        except Exception as error:
            raise Exception(f"An error occurred: {error}")



from langchain.tools import Tool


from langchain_core.runnables import Runnable


class PolicyAwareToolWrapper(Runnable):
    def __init__(self, tool, policy_check_tool, llm):
        self.tool = tool
        self.policy_check_tool = policy_check_tool
        self.llm = llm

    async def invoke(self, inputs):
        """
        Perform the policy check and invoke the tool if approved.

        Args:
            inputs (dict): Inputs to the tool.

        Returns:
            The result of the tool invocation or a policy check failure message.
        """
        # Prepare the policy check description
        tool_name = self.tool.name
        tool_description = self.tool.description or "No description available"
        intended_usage = f"Using tool: {tool_name}. Description: {tool_description}. Intended inputs: {inputs}"

        # Check the policy
        policy_inputs = {"description": intended_usage}
        policy_result = await self.policy_check_tool.invoke(policy_inputs)

        if not policy_result.get("approved", False):
            return f"Policy check failed: {policy_result.get('reason', 'No reason provided')}"

        # If approved, proceed with the actual tool invocation
        return await self.tool.invoke(inputs)

    async def __call__(self, inputs):
        """Alias for `invoke`."""
        return await self.invoke(inputs)


# Wrap with LangChain's Tool


def wrap_tool_with_policy(tool, policy_check_tool, llm):
    async def policy_aware_tool_func(inputs):
        """
        Async wrapper to perform policy checks before invoking the tool.
        """
        # Prepare the policy check description
        tool_name = tool.name
        tool_description = tool.description or "No description available"
        intended_usage = f"Using tool: {tool_name}. Description: {tool_description}. Intended inputs: {inputs}"

        # Check the policy
        policy_inputs = {"description": intended_usage}
        policy_result = await policy_check_tool.invoke(policy_inputs)

        if not policy_result.get("approved", False):
            return f"Policy check failed: {policy_result.get('reason', 'No reason provided')}"

        # If approved, proceed with the actual tool invocation
        return await tool.invoke(inputs)

    # Wrap the async function as a tool
    return Tool(
        name=tool.name,
        func=policy_aware_tool_func,  # Pass the async function here
        description=f"Policy-aware wrapper for {tool.name}",
    )

# Example Usage
if __name__ == "__main__":
    # Initialize an LLM (using OpenAI's API as an example)
    # llm_instance = OpenAI(model="gpt-4", openai_api_key=keys.OPENAI_KEY)

    llm_instance = ChatOllama(model="llama3.2")

    # Initialize the PolicyCheckTool
    tool = PolicyCheckTool(policy_file="policy.md", llm=llm_instance)

    # Define a user request and tool description
    user_request = "Delete all user data."
    tool_description = "A tool that deletes user data from the database."

    # Run the policy check
    result = tool._run(request=user_request, tool_description=tool_description)
    print(result)
