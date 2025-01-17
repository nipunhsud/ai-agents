import re
import ast
import operator
import requests
import ssl
import certifi

from dotenv import load_dotenv
from langgraph.graph import END, START
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_community import GmailToolkit
from langchain_core.tools import tool
import os
from langchain_community.tools.google_finance import GoogleFinanceQueryRun
from langchain_community.utilities.google_finance import GoogleFinanceAPIWrapper
from langchain_community.tools.google_trends import GoogleTrendsQueryRun
from langchain_community.utilities.google_trends import GoogleTrendsAPIWrapper
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_core.tools import StructuredTool
from typing import List
from typing import Any, List
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage , ToolMessage, HumanMessage, AIMessage
from slack_sdk import WebClient

tavily_tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()

def handle_tool_error(state: dict) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\nPlease fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def slack_client():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    client = WebClient(
        token=os.getenv("SLACK_TOKEN"),
        ssl=ssl_context
    )
    return client


def send_slack_message(slack_token: str, channel: str, message: str) -> dict:
    """Get real-time stock quote data."""
    client = slack_client()
    response = client.chat_postMessage(channel=channel, text=message)
    return response

def get_slack_channels() -> dict:
    """Get list of public channels in the workspace."""
    client = slack_client()
    try:
        # Use conversations_list instead of channels_list
        response = client.conversations_list(
            types="public_channel",
            exclude_archived=True
        )
        return response
    except Exception as e:
        print(f"Error getting channels: {e}")
        return {"error": str(e)}
    
def get_slack_users() -> dict:
    """Get real-time stock quote data."""
    client = slack_client()
    response = client.users_list()
    return response

def create_slack_channel(slack_token: str, channel_name: str) -> dict:
    """Get real-time stock quote data."""
    client = slack_client()
    response = client.channels_create(name=channel_name)
    return response

def get_slack_channel_info(slack_token: str, channel_id: str) -> dict:
    """Get real-time stock quote data."""
    client = slack_client()
    response = client.channels_info(channel=channel_id)
    return response

def get_slack_channel_members(slack_token: str, channel_id: str) -> dict:
    client = slack_client()
    response = client.channels_members(channel=channel_id)
    return response


slack_listings_tool = StructuredTool.from_function(
    func=get_slack_channels,
    name="slack_channels",
    description="Get real-time slack channels data"
)
slack_users_tool = StructuredTool.from_function(
    func=get_slack_users,
    name="slack_users",
    description="Get real-time slack users data"
)
send_slack_message_tool = StructuredTool.from_function(
    func=send_slack_message,
    name="send_slack_message",
    description="Send a message to a slack channel"
)
slack_create_channel_tool = StructuredTool.from_function(
    func=create_slack_channel,
    name="create_slack_channel",
    description="Create a new slack channel"
)
slack_channel_info_tool = StructuredTool.from_function(
    func=get_slack_channel_info,
    name="slack_channel_info",
    description="Get real-time slack channel info data for a given channel id"
)
tools = [
    # tavily_tool, 
    # google_finance_tool, 
    # google_trends_tool, 
    slack_listings_tool, 
    slack_users_tool, 
    slack_channel_info_tool, 
    slack_create_channel_tool,
    send_slack_message_tool
]
chat = ChatOpenAI(
    temperature=0.7,
    model_name="gpt-4o",  # You can also use "gpt-4" if you have access
)

def create_tool_node_with_fallback(tools: List[BaseTool]) -> RunnableWithFallbacks[Any, dict]:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)],
        exception_key="error"
    )


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


def should_continue_function(state: AgentState):
    """Determine if we should continue or not."""
    messages = state['messages']
    last_message = messages[-1]
    
    # If there are tool calls, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise end
    return "END"


class SlackAssistant:
    def __init__(self):
        self.system = agent_prompt
        self.prompt = ChatPromptTemplate.from_messages([SystemMessage(content=self.system)])
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("tools", create_tool_node_with_fallback(tools))

        # Define the workflow edges
        graph.add_edge(START, "llm")
        # graph.add_conditional_edges("llm", should_continue_function, ["tools", END])
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "tools", False: END}
        )
        graph.add_edge("tools", "llm")
        graph.add_edge("llm", END)
       
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        print(tool_calls)
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                print("-====")
                result = self.tools[t['name']].invoke(t['args'])
                print(result)
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    




agent_prompt = """

You are an advanced copywriter AI assistant equipped with specialized tools
to access and analyze Slack API. Your primary function is to help users with
providing 

You have access to the following tools:
[slack_token_tool, slack_listings_tool, slack_users_tool, slack_channel_info_tool, slack_create_channel_tool, send_slack_message_tool]
1. Custom slack token: For retrieving real-time slack token data for a given channel and message. use slack_token_tool tool
2. Custom slack channels: For retrieving real-time slack channels data. use slack_channels_tool tool
3. Custom slack users: For retrieving real-time slack users data. use slack_users_tool tool
4. Custom slack channel info: For retrieving real-time slack channel info data for a given channel id. use slack_channel_info_tool tool
5. Custom slack create channel: For creating a new slack channel. use slack_create_channel_tool tool
6. Custom slack send message: For sending a message to a slack channel. use send_slack_message_tool tool

Your job is to help the user with their slack requests using the following instructions:

1. Get user or channel information from the prompt, use tools to determine the user or channel id
2. Write a proper message for slack based on user request
3. Use the tools to send the message to the slack channel or user
4. Custom slack send message: For sending a message to a slack channel. use send_slack_message_tool tool 


Post messages to slack channels or users and use your best judgement to determine the best way to do it."""

model = ChatOpenAI(model="gpt-4o") 
abot = SlackAssistant()

def _format_as_markdown(content: str) -> None:
    """Save the content as a markdown file."""
    with open('stock_analysis.md', 'w') as f:
        f.write(content)

def slack_generator(content):
    messages = [HumanMessage(content="User want to do : "+str(content)+".  Generate a slack message for this request")]
    result = abot.graph.invoke({"messages": messages})
    print(result)
    try:
        json_data = result['messages'][-1].content.split("\n\n```json\n")[1].split("\n```")[0]
        markdown_data = result['messages'][-1].content.split("\n\n```json\n")[0]
        print(json_data)
        print(markdown_data)
    except Exception as e:
        print(f"Could not serialize graph: {e}")
    return markdown_data, json_data