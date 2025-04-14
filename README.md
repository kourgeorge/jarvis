# Personal Assistant LLM-based AI Agent

## Overview
This project implements a personal assistant AI agent using Langchain, designed to assist users with various tasks by leveraging a wide range of capabilities. The assistant is built to interact with different tools and services, making it a versatile solution for personal and professional needs.

## Features
- **Email Management**: Integrates with Gmail to manage emails, including sending, deleting, and flagging messages.
- **Calendar Integration**: Allows users to create and fetch calendar events seamlessly.
- **Web Browsing**: Utilizes Playwright for web browsing capabilities, enabling the assistant to gather information from the web.
- **Academic Research**: Supports querying academic databases like PubMed, Semantic Scholar, and arXiv for research papers.
- **File Management**: Provides tools for managing and manipulating files.
- **Real-time Interaction**: Built with Streamlit for a user-friendly interface, allowing real-time chat interactions with the assistant.
- **Memory Management**: Maintains a conversation history and user memories to provide personalized responses.

## Project Structure
- **customtools/**: Contains custom tools and utilities that enhance the assistant's capabilities.
- **personal_assistant.py**: The main module that defines the `PersonalAssistant` class, which initializes the assistant and manages its operations.
- **app.py**: The Streamlit application that serves as the user interface for interacting with the assistant.
- **ready_tools.py**: Defines various tools that the assistant can use to perform specific tasks, such as searching for information or retrieving the current date and time.

## Getting Started
To get started with the project, clone the repository and install the required dependencies. You can then run the Streamlit app to interact with your personal assistant.

## Example Use cases

### Email Management
- **Forwarding Emails**: "Forward the last email you got from Joe Doe to jeries.fin@gmail.com."
- **Summarizing Emails**: "Summarize the last few emails I got from Joe Doe."

### File System Interaction
- **Organizing Files**: "Create a folder in the Downloads directory named PDFS and move all .pdf files from the desktop to it."
- **Content Summarization**: "Summarize all the file content in directory X, create a new file called summary.txt with the summary, and send it to gin.din@gmail.com."

### Internet Research Tasks
- **Information Gathering**: "Get everything you can learn about George Kour, write a poem about it, and create a file on the desktop with this information."
- **Academic Research**: "Find the latest research papers on quantum computing, summarize the key findings, and compile them into a report."

### Calendar and Scheduling
- **Event Creation**: "Schedule a meeting with the team for next Monday at 10 AM, including a video conference link."
- **Event Retrieval**: "List all my meetings for this week, highlighting any that overlap or conflict."

### Real-time Assistance
- **Task Automation**: "Set a reminder to call John at 3 PM tomorrow and send a follow-up email if the call is missed."
- **Information Retrieval**: "What's the weather forecast for today, and do I need an umbrella?"

### Academic and Professional Development
- **Research Assistance**: "Identify key trends in AI research over the past year and prepare a presentation."
- **Skill Enhancement**: "Find online courses to improve my Python programming skills and schedule study sessions."

### Personal Productivity
- **Daily Planning**: "Create a daily schedule that includes work tasks, breaks, and personal time."
- **Goal Tracking**: "Set weekly goals and track progress, providing motivational quotes to keep me inspired."
## Installation
```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd PersonalAssistant

# Install dependencies
pip install -r requirements.txt
```

## Usage
Run the Streamlit app:
```bash
streamlit run app.py
```

## Future Plans:
1. Use other vendors of LLMs.
2. Use local LLMs like deepseek.
3. adding proprietry knowledge and usign RAG.