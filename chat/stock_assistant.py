import re
import ast
import operator
import requests

from dotenv import load_dotenv
from langgraph.graph import END
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
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

tavily_tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()

def get_stock_quote(stock_ticker: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/quote/{stock_ticker}?apikey={api_key}"
    
    response = requests.get(url)
    # print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def get_stock_listings() -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
    
    response = requests.get(url)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def get_stock_ma(stock_ticker: str, period: int) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/1day/{stock_ticker}?period={period}&type=ema&apikey={api_key}"
    
    response = requests.get(url)
    # print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def get_income_statement(stock_ticker: str, period: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{stock_ticker}?period={period}&apikey={api_key}"
    
    response = requests.get(url)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

def get_institutional_ownership(stock_ticker: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v4/institutional-ownership/list?apikey={api_key}"
    
    response = requests.get(url)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

google_finance_tool = GoogleFinanceQueryRun(api_wrapper=GoogleFinanceAPIWrapper())
google_trends_tool = GoogleTrendsQueryRun(api_wrapper=GoogleTrendsAPIWrapper())
yahoo_finance_tool = YahooFinanceNewsTool()
stock_quote_tool = StructuredTool.from_function(
    func=get_stock_quote,
    name="stock_quote",
    description="Get real-time stock quote data for a given ticker symbol"
)
stock_listings_tool = StructuredTool.from_function(
    func=get_stock_listings,
    name="stock_listings",
    description="Get real-time stock listings data"
)
stock_ma_tool = StructuredTool.from_function(
    func=get_stock_ma,
    name="stock_ma",
    description="Get real-time stock moving average data for a given ticker symbol and period"
)
income_statement_tool = StructuredTool.from_function(
    func=get_income_statement,
    name="income_statement",
    description="Get real-time income statement data for a given ticker symbol"
)
institutional_ownership_tool = StructuredTool.from_function(
    func=get_institutional_ownership,
    name="institutional_ownership",
    description="Get real-time institutional ownership data for a given ticker symbol"
)
tools = [google_trends_tool, google_finance_tool, stock_quote_tool, stock_listings_tool, stock_ma_tool, income_statement_tool, institutional_ownership_tool]
chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class StockAssistant:
    def __init__(self):
        self.system = agent_prompt
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
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

You are an advanced financial analysis AI assistant equipped with specialized tools
to access and analyze financial data. Your primary function is to help users with
financial analysis by retrieving and interpreting income statements, balance sheets,
and cash flow statements for publicly traded companies. 
You are an expert stock trading assistant that is an expert at momemtum trading like Mark Minervini, Bill O'Neil, and others. 
Your role is to help answer the users questions about stock trading and in USD. Follow these guidelines:

You have access to the following tools:

1. Tavily Search: For retrieving recent market news and analysis
2. Google Trends: For analyzing market interest and trends
3. Yahoo Finance News: For retrieving recent news and analysis
Your capabilities include:
4. Custom stock quote: For retrieving real-time stock quote data for a given ticker symbol
5. Custom stock listings: For retrieving real-time stock listings data
6. Custom stock moving average: For retrieving real-time stock moving average data for a given ticker symbol and period
Your job is to help the user with their stock trading questions using the following instructions:

1. Current Earnings: Look for companies with strong, accelerating quarterly earnings growth. Use get_income_statement tool
2. Annual Earnings: Annual earnings growth of at least 25% over the last three years.
3. New: Look for new products, services, or management.
4. Supply and Demand: Favor stocks with strong demand, indicated by higher trading volumes.
5. Leader or Laggard: Focus on leading stocks in leading industries.
6. Institutional Sponsorship: Stocks with increasing institutional ownership.
7. Market Direction: The overall market should be in an uptrend.
   - Ensure 150 MA is above 200 MA
   - Ensure 50 MA is above 150 MA
8. Trend Analysis:
   - Analyze the trend of the stock
   - Ensure the stock is in a strong uptrend
9. Trading Style Guidelines:
   - Follow the trading style of Mark Minervini, Bill O'Neil, and others.
   - Look for low volatility stocks with high volume
   - Look for stocks that are in a strong uptrend
   - EPS growth should be at least 25% quarter over quarter

When responding to queries:

1. Always specify which financial statement(s) you're using for your analysis.
2. Provide context for the numbers you're referencing (e.g., fiscal year, quarter).
3. Explain your reasoning and calculations clearly.
4. If you need more information to provide a complete answer, ask for clarification.
5. When appropriate, suggest additional analyses that might be helpful.
6. Respond in USD if applicable - what is a good buy point for a stock?
7. Use the google_trends_tool tool to get the trend and popularity of the stock
8. Use the google_finance_tool tool to get the real-time stock news data
Remember, your goal is to provide accurate, insightful financial analysis to
help users make informed decisions. Always maintain a professional and objective tone in your responses.




Provide options and explanations for your suggestions."""

model = ChatOpenAI(model="gpt-4o") 
abot = StockAssistant()


def stock_generator(content):
    
    messages = [HumanMessage(content="Here are information: "+str(content)+".  Generate a stock trading strategy for this stock and give me the stock summary and analysis on the street")]
    result = abot.graph.invoke({"messages": messages})

    #print(result)

    print(result['messages'][-1].content)
    
    json_data,status =parse_product_listings(result['messages'][-1].content)
    print(json_data)
    if status:
        #print(json_data)
        return result['messages'][-1].content,json_data
    else:

        content="""
            Here are some products infomation ."""+result['messages'][-1].content+""" can you please give me these information in json format inside of a list
            example:
            [{
                'product_title': '',
                'reason': '',
                'price': '',
                'url': '',
                'relation_of_interest': ''
            }{
                'product_title': '',
                'reason': '',
                'price': '',
                'url': '',
                'relation_of_interest': ''
            }]
        """
        messages = [HumanMessage(content=content)]
        response = chat(messages)
        product_list=response.content

        command_start = product_list.find('[')-1
        command_end = product_list.find(']')+1
        if command_start != -1 and command_end != -1:
            command_content = product_list[command_start + 1:command_end].strip()
            json_data = ast.literal_eval(command_content)
        
        print(response.content)
        
        return result['messages'][-1].content,json_data


def parse_product_listings(text):
    # Split text into individual product listings
    products = []
    product_blocks = text.split('\n\n')  # Split by double newline to separate products
    
    for block in product_blocks:
        if not block.strip():  # Skip empty blocks
            continue
            
        product = {
            "product_title": "",
            "reason": "",
            "price": "",
            "url": "",
            "relation_of_interest": ""
        }
        
        # Get Product Title
        title_match = re.search(r'^\d+\.\s+\*\*([^*]+?)\*\*', block)
        if title_match:
            product["product_title"] = title_match.group(1).strip()
        
        # Get Reason
        reason_match = re.search(r'\*\*Reason\*\*:\s*(.+?)(?=\n|$)', block)
        if reason_match:
            product["reason"] = reason_match.group(1).strip()
            
        # Get Price
        price_match = re.search(r'\*\*Price\*\*:\s*(.+?)(?=\n|$)', block)
        if price_match:
            product["price"] = price_match.group(1).strip()
            
        # Get URL - handles markdown link format
        url_match = re.search(r'\*\*URL\*\*:\s*\[.+?\]\((.+?)\)', block)
        if url_match:
            product["url"] = url_match.group(1).strip()
            
        # Get Relation of Interest
        roi_match = re.search(r'\*\*Relation of Interest\*\*:\s*(.+?)(?=\n|$)', block)
        if roi_match:
            product["relation_of_interest"] = roi_match.group(1).strip()

        
        
        if any(product.values()):  # Only add if at least one field was found
            products.append(product)

    # Check for empty values in all products after processing
    status = True
    for product in products:       
        if (product['product_title'] == "" or 
            product['reason'] == "" or 
            product['price'] == "" or 
            product['url'] == ""):
            print("One or more fields are empty")
            status = False
        else:
            print("All fields have values")

        
    
    return products,status
