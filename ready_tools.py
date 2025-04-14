import os
from typing import List

from langchain.agents import Tool
from datetime import datetime

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.gmail import get_gmail_credentials
from langchain_community.tools.gmail.utils import build_resource_service
from langchain_community.utilities.semanticscholar import SemanticScholarAPIWrapper
from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_googledrive.tools import GoogleDriveSearchTool
from langchain_googledrive.utilities import GoogleDriveAPIWrapper

from customtools.CreateCalendarEvent import GmailCreateCalendarEvent
from customtools.FetchEventTool import GmailFetchCalendarEvents
from customtools.GmailDeleteMessage import GmailDeleteMessage
from customtools.GmailFlagImportantMessage import GmailFlagImportantMessage
from customtools.GmailFlagMessage import GmailFlagMessage

load_dotenv()

# Define Wrappers
semantic_scholar_wrapper = SemanticScholarAPIWrapper()

# Define Tools

datetime_tool = Tool(
    name="CurrentDateTime",
    func=lambda _: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    description="Retrieve the current date and time."
)

api_wrapper = GoogleDriveAPIWrapper(
    gdrive_api_file=os.environ['GOOGLE_ACCOUNT_FILE'],
    folder_id='root',
    num_results=20,
    template="gdrive-query",
    mode='documents',
    recursive=True
)

drive_tool = GoogleDriveSearchTool(api_wrapper=api_wrapper)

#     drive_tools = load_tools(
#     ["google_drive_search"],
#     folder_id='root',
#     template="gdrive-query",
# )


def get_custom_gmail_tools(api_resource, api_resource_calendar) -> List[BaseTool]:
    """Get the tools in the toolkit."""
    return [
        GmailFlagMessage(api_resource=api_resource),
        GmailDeleteMessage(api_resource=api_resource),
        GmailFlagImportantMessage(api_resource=api_resource),
        GmailCreateCalendarEvent(api_resource=api_resource_calendar),
        GmailFetchCalendarEvents(api_resource=api_resource_calendar),
    ]

