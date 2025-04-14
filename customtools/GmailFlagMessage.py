"""Flag Gmail messages."""

from typing import Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_community.tools.gmail.base import GmailBaseTool


def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label = next((label for label in labels if label['name'] == label_name), None)
    if label:
        return label['id']
    else:
        label_body = {
            'name': label_name,
            'labellistVisibility': 'labelShow',
            'messagelistVisibility': 'show',
            'type': 'user'
        }
        label = service.users().labels().create(userId='me', body=label_body).execute()
        return label['id']


def label_email(service, email_id, label_name):
    label_id = get_or_create_label(service, label_name)
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={
            'addLabelIds': [label_id],
            'removeLabelIds': []
        }
    ).execute()
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={
            'removeLabelIds': ['UNREAD']
        }
    ).execute()
    print(f"Email flagged: ID {email_id}, with the label {label_name}.")


class FlagMessageSchema(BaseModel):
    """Input for GmailSendMessageTool."""

    message_id: str = Field(
        ..., description="The ID of the message to flag."
    )
    label_name: str = Field(
        ..., description="The label name to apply to the message."
    )


class GmailFlagMessage(GmailBaseTool):  # type: ignore[override, override]
    """Tool that flags a message in Gmail."""

    name: str = "flag_gmail_message"
    description: str = "Use this tool to flag an email message with a specific label."
    args_schema: Type[FlagMessageSchema] = FlagMessageSchema

    def _run(
        self,
        message_id: str,
        label_name: str,
        run_manager: CallbackManagerForToolRun = None,
    ) -> str:
        """Run the tool."""
        try:
            label_email(self.api_resource, message_id, label_name)
            return f"Message with ID {message_id} has been flagged with label {label_name}."
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
