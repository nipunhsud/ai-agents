from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from typing import Optional, Dict
from .agent_slack import SlackAgent

# First, let's create a tool wrapper for our SlackAgent
class SlackAgentTool(BaseTool):
    name = "slack_communication"
    description = """Use this tool to send messages or announcements through Slack.
    For messages, provide: 'message' content
    For announcements, provide: 'type' (feature/company/milestone/event), 'title', and 'description'
    The tool will automatically determine appropriate recipients."""
    
    def __init__(self, slack_token: str, openai_api_key: str):
        super().__init__()
        self.slack_agent = SlackAgent(slack_token, openai_api_key)
    
    def _run(self, query: str) -> str:
        """Execute the Slack agent with the given query"""
        return self.slack_agent.process_request(query)
    
    async def _arun(self, query: str) -> str:
        """Async version of the tool"""
        return self._run(query)
    


'''
#example use of slack as tool of another agent.
self.slack_tool = SlackAgentTool(
    slack_token=slack_token,
    openai_api_key=openai_api_key
)
self.tools = [
    self.slack_tool,
    Tool(
        name="calendar",
        func=self._check_calendar,
        description="Check calendar for available times and meetings"
    ),
    Tool(
        name="task_manager",
        func=self._manage_tasks,
        description="Manage and track team tasks"
    )
]
'''