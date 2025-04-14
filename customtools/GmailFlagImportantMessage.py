"""Flag Gmail messages as important."""

from typing import Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_community.tools.gmail.base import GmailBaseTool


def flag_as_important(service, email_id):
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={
            'addLabelIds': ['IMPORTANT'],
            'removeLabelIds': []
        }
    ).execute()
    print(f"Email flagged as important: ID {email_id}.")


class FlagImportantMessageSchema(BaseModel):
    """Input for GmailFlagImportantMessageTool."""

    message_id: str = Field(
        ..., description="The ID of the message to flag as important."
    )


class GmailFlagImportantMessage(GmailBaseTool):  # type: ignore[override, override]
    """Tool that flags a message in Gmail as important."""

    name: str = "flag_gmail_important_message"
    description: str = "Use this tool to flag an email message as important."
    args_schema: Type[FlagImportantMessageSchema] = FlagImportantMessageSchema

    def _run(
        self,
        message_id: str,
        run_manager: CallbackManagerForToolRun = None,
    ) -> str:
        """Run the tool."""
        try:
            flag_as_important(self.api_resource, message_id)
            return f"Message with ID {message_id} has been flagged as important."
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
