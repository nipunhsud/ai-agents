import re
import ast
import operator
import requests

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


def get_market_stats(zip_code: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("RENT_CAST_API_KEY")
    url = f"https://api.rentcast.io/v1/markets?zipCode={zip_code}&dataType=All&historyRange=6"

    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
    return None

def get_sale_listings(zip_code: str, city: str, state: str, address: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("RENT_CAST_API_KEY")
    url = "https://api.rentcast.io/v1/listings/sale?city=Austin&state=TX&status=Active&limit=5"

    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def get_rent_estimate(zip_code: str, city: str, state: str, address: str, property_type: str, bedrooms: int, bathrooms: int, square_footage: int, comp_count: int) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("RENT_CAST_API_KEY")
    url = f"https://api.rentcast.io/v1/avm/rent/long-term?address={address}&propertyType={property_type}&bedrooms={bedrooms}&bathrooms={bathrooms}&squareFootage={square_footage}&compCount={comp_count}"

    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }

    response = requests.get(url, headers=headers)

    print(response.text)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
    return None


market_stats_tool = StructuredTool.from_function(
    func=get_market_stats,
    name="market_stats",
    description="Get real-time market stats data for a given zip code"
)
sale_listings_tool = StructuredTool.from_function(
    func=get_sale_listings,
    name="sale_listings",
    description="Get real-time sale listings data"
)
rent_estimate_tool = StructuredTool.from_function(
    func=get_rent_estimate,
    name="rent_estimate",
    description="Get real-time rent estimate data for a given zip code, city, state, address, property type, bedrooms, bathrooms, square footage, and comp count"
)

tools = [
    tavily_tool, 
    # google_finance_tool, 
    # google_trends_tool, 
    market_stats_tool, 
    sale_listings_tool, 
    rent_estimate_tool, 
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


class RentalAssistant:
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

You are an advanced Realtor, Real Estate Analyst AI assistant equipped with specialized tools
to access and analyze real estate data. Your primary function is to help users with
providing summarized report of real estate analysis done by foloowing rules below. Use the tools provided to get the data.

Your focus is on real estate analysis and your role is to help answer the users questions about real estate and in USD. Follow these guidelines:

You have access to the following tools:
[market_stats_tool, sale_listings_tool, rent_estimate_tool]
1. Custom market stats: For retrieving real-time market stats data for a given zip code. use market_stats_tool tool
2. Custom sale listings: For retrieving real-time sale listings data. use sale_listings_tool tool
3. Custom rent estimate: For retrieving real-time rent estimate data for a given zip code, city, state, address, property type, bedrooms, bathrooms, square footage, and comp count. use rent_estimate_tool tool

Your job is to help the user with their real estate research using the following instructions:

1. Current Listing Price: Look for the current listing price of the property
2. Estimated Rent: Look for the estimated rent of the property
3. Market Stats: Look for the market stats of the property and break it down by areas in the city
4. Sale Listings: Look for the sale listings of the property, provide the property details and price and links to the property
5. Rent Estimate: Look for the rent estimate of the property, break it down by property type, bedrooms, bathrooms, square footage, and comp count
6. Market Direction: based on the market stats, provide the market direction of the property
7. Tax and Fees: provide the tax and fees of the property, state, county, city, and property management fee and other costs that may impact the cash flow
8. Split by parts of the city: split the property by parts of the city and provide the analysis for each part and Rent Estimate: Look for the rent estimate of the property, break it down by property type, bedrooms, bathrooms, square footage, and comp count

Response should be in markdown format.
Provide options and explanations for your suggestions."""

model = ChatOpenAI(model="gpt-4o") 
abot = RentalAssistant()

def _format_as_markdown(content: str) -> None:
    """Save the content as a markdown file."""
    with open('stock_analysis.md', 'w') as f:
        f.write(content)

def rental_generator(content):
    messages = [HumanMessage(content="City, State or Address: "+str(content)+".  Generate a real estate analysis for this property and give me the property summary and analysis based on the rules deifined")]
    result = abot.graph.invoke({"messages": messages})
    print(result)
    #     print("Graph saved as graph.png")
    # except Exception as e:
    #     print(f"Could not generate graph: {e}")
    
    try:
        json_data = result['messages'][-1].content
        markdown_data = result['messages'][-1].content
        print(json_data)
        print(markdown_data)
    except Exception as e:
        print(f"Could not serialize graph: {e}")
    return markdown_data, json_data