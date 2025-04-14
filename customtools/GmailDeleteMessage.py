"""Delete Gmail messages."""

from typing import Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_community.tools.gmail.base import GmailBaseTool


def delete_email(service, email_id):
    service.users().messages().delete(
        userId='me',
        id=email_id
    ).execute()
    print(f"Email deleted: ID {email_id}.")


class DeleteMessageSchema(BaseModel):
    """Input for GmailDeleteMessageTool."""

    message_id: str = Field(
        ..., description="The ID of the message to delete."
    )


class GmailDeleteMessage(GmailBaseTool):  # type: ignore[override, override]
    """Tool that deletes a message in Gmail."""

    name: str = "delete_gmail_message"
    description: str = "Use this tool to delete an email message."
    args_schema: Type[DeleteMessageSchema] = DeleteMessageSchema

    def _run(
        self,
        message_id: str,
        run_manager: CallbackManagerForToolRun = None,
    ) -> str:
        """Run the tool."""
        try:
            delete_email(self.api_resource, message_id)
            return f"Message with ID {message_id} has been deleted."
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
