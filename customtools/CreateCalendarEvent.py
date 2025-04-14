from typing import Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_community.tools.gmail.base import GmailBaseTool  # You may need to adapt this import to Google Calendar tools.


def create_calendar_event(service, event_data):
    """Create an event in Google Calendar."""
    event = service.events().insert(calendarId='primary', body=event_data).execute()
    print(f"Event created: {event['htmlLink']}")
    return event['htmlLink']


class CreateCalendarEventSchema(BaseModel):
    """Input schema for GmailCreateCalendarEventTool."""

    summary: str = Field(..., description="The title of the event.")
    location: str = Field(None, description="The location of the event.")
    description: str = Field(None, description="A description of the event.")
    start_time: str = Field(
        ..., description="The start time of the event in ISO 8601 format (e.g., '2024-12-15T09:00:00-07:00')."
    )
    end_time: str = Field(
        ..., description="The end time of the event in ISO 8601 format (e.g., '2024-12-15T10:00:00-07:00')."
    )
    attendees: list[str] = Field(
        default_factory=list, description="A list of email addresses of attendees."
    )
    time_zone: str = Field(
        default="America/Los_Angeles", description="The time zone of the event."
    )


class GmailCreateCalendarEvent(GmailBaseTool):  # type: ignore[override, override]
    """Tool for creating a Google Calendar event."""

    name: str = "create_calendar_event"
    description: str = "Use this tool to create a new Google Calendar event."
    args_schema: Type[CreateCalendarEventSchema] = CreateCalendarEventSchema

    def _run(
            self,
            summary: str,
            location: str,
            description: str,
            start_time: str,
            end_time: str,
            attendees: list[str],
            time_zone: str,
            run_manager: CallbackManagerForToolRun = None,
    ) -> str:
        """Run the tool."""
        try:
            event_data = {
                "summary": summary,
                "location": location,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": time_zone},
                "end": {"dateTime": end_time, "timeZone": time_zone},
                "attendees": [{"email": email} for email in attendees],
            }
            event_link = create_calendar_event(self.api_resource, event_data)
            return f"Event created successfully: {event_link}"
        except Exception as error:
            raise Exception(f"An error occurred: {error}")

