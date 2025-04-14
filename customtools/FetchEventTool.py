from typing import Type, Optional, List
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from langchain_community.tools.gmail.base import GmailBaseTool


def fetch_calendar_events(service, time_min: str, time_max: str, calendar_id='primary'):
    """Fetch events from Google Calendar within a specified time range."""
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return events


class FetchCalendarEventsSchema(BaseModel):
    """Input schema for GmailFetchCalendarEventsTool."""
    
    time_min: str = Field(..., description="The start time of the range in ISO 8601 format.")
    time_max: str = Field(..., description="The end time of the range in ISO 8601 format.")
    calendar_id: Optional[str] = Field(None, description="The ID of the calendar to fetch events from.")


class GmailFetchCalendarEvents(GmailBaseTool):  # type: ignore[override, override]
    """Tool for fetching events from Google Calendar."""

    name: str = "fetch_calendar_events"
    description: str = "Use this tool to fetch events from Google Calendar."
    args_schema: Type[FetchCalendarEventsSchema] = FetchCalendarEventsSchema

    def _run(
            self,
            time_min: str,
            time_max: str,
            calendar_id: Optional[str] = None,
            run_manager: CallbackManagerForToolRun = None,
    ) -> List[dict]:
        """Run the tool."""
        try:
            events = fetch_calendar_events(self.api_resource, time_min, time_max, calendar_id)
            return events if events else "No events found."
        except Exception as error:
            raise Exception(f"An error occurred: {error}")
