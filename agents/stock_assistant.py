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


def get_financial_growth(stock_ticker: str, period: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/financial-growth/{stock_ticker}?period={period}&limit=10&apikey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None

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

def get_mutual_fund_holder(stock_ticker: str) -> dict:
    """Get real-time mutual fund holder data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/mutual-fund-holder/{stock_ticker}?apikey={api_key}"
    
    response = requests.get(url)
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
        return data if data else None
    return None

def get_stock_ma(stock_ticker: str, period: int) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/1day/{stock_ticker}?period={period}&type=ema&apikey={api_key}"
    
    response = requests.get(url)
    # print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data[:10] if data else None
    return None

def get_income_statement_by_period(stock_ticker: str, period: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{stock_ticker}?period={period}&limit=10&apikey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
    return None

def get_institutional_ownership(stock_ticker: str) -> dict:
    """Get real-time stock quote data."""
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v4/institutional-ownership/list?apikey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
    return None

def get_industry_performance():
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/sectors-performance?apikey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
    return None

def get_company_outlook(stock_ticker: str) -> dict:
    api_key = os.getenv("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v4/company-outlook?symbol={stock_ticker}&apikey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data if data else None
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
    func=get_income_statement_by_period,
    name="income_statement",
    description="Get real-time income statement data for a given ticker symbol"
)
institutional_ownership_tool = StructuredTool.from_function(
    func=get_institutional_ownership,
    name="institutional_ownership",
    description="Get real-time institutional ownership data for a given ticker symbol"
)
financial_growth_tool = StructuredTool.from_function(
    func=get_financial_growth,
    name="quarterly_financial_growth",
    description="Get real-time quarterly/annual financial growth data for a given ticker symbol"
)
sector_performance_tool = StructuredTool.from_function(
    func=get_industry_performance,
    name="sector_performance",
    description="Get real-time sector performance data"
)
mutual_fund_holder_tool = StructuredTool.from_function(
    func=get_mutual_fund_holder,
    name="mutual_fund_holder",
    description="Get real-time mutual fund holder data for a given ticker symbol"
)
tools = [
    # tavily_tool, 
    # google_finance_tool, 
    # google_trends_tool, 
    stock_quote_tool, 
    # stock_listings_tool, 
    stock_ma_tool, 
    income_statement_tool, 
    # institutional_ownership_tool, 
    # financial_growth_tool,
    sector_performance_tool,
    mutual_fund_holder_tool
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


class StockAssistant:
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
You are an advanced Quantitative Analyst AI assistant specializing in momentum trading analysis. Your role is to provide detailed stock analysis following the principles of expert traders like Mark Minervini and Bill O'Neil. All analysis should be in USD.

AVAILABLE TOOLS:
1. stock_quote_tool: Real-time stock quotes and basic metrics
2. stock_ma_tool: Moving average data for technical analysis
3. income_statement_tool: Financial statements for EPS analysis
4. sector_performance_tool: Industry and sector performance data
5. mutual_fund_holder_tool: Institutional ownership data
6. google_trends_tool: Google Trends data
7. google_finance_tool: Google Finance data

ANALYSIS REQUIREMENTS:
1. Technical Analysis
   - Price trend (higher highs/lows pattern)
   - Technical Setup (Strong, Weak, Neutral)
        - trend analysis (uptrend, downtrend, sideways)
        - volume analysis (increasing in the last 3 months)
        - moving average 20, 10 EMA increasing in the short term
        - Price action (higher highs/lows pattern) close to moving average 20 EMA or 50 EMA
   - Moving averages (50, 150, 200 EMA alignment) (increasing in the last 3 months)
   - Volume analysis vs 52-week average (Point out the sudden volume increase  in the last 3 months) (higher than 100% of 52-week average) [Reasoning] [details]
   - Volatility patterns and consolidation areas (Point out the consolidation areas and volatility patterns) [Reasoning] [details]
   - Distance from 52-week high (8% rule) [Reasoning] [details]

2. Fundamental Analysis
   - Quarterly EPS growth (minimum 25% for 3 quarters) [Reasoning] [details]
   - Annual earnings growth (minimum 25% over 3 years) [Reasoning] [details]
   - Revenue growth trends [Reasoning] [details]
   - Industry position and sector performance [Reasoning] [details]

3. Market and Sector Analysis
   - Overall market direction 
        - Market sentiment [Reasoning] [details]
        - QQQ/SPY/NASDAQ trends [Reasoning] [details]
        - Supply/demand dynamics [Reasoning] [details]
   - Sector Analysis
        - Sector relative strength [Reasoning] [details]
        - Sector performance [Reasoning] [details]
        - Sector supply/demand dynamics [Reasoning] [details]

4. Institutional and Fund Ownership
   - Institutional ownership trends [Reasoning] [details]
   - Institutional ownership data [Reasoning] [details]

5. News, Trends and Sentiment
   - Google Trends data [Reasoning] [details]
   - Tavily Search data [Reasoning] [details]

RESPONSE FORMAT:
Your analysis must be presented in two formats - Markdown and JSON:

1. MARKDOWN FORMAT:
### Stock Summary: [TICKER]
**Current Status**
- Price: $[PRICE]
- 52-Week Range: $[LOW] - $[HIGH]
- Volume: [CURRENT] vs [AVERAGE]

**Technical Analysis** [Reasoning]
- Trend Direction: [UPTREND/DOWNTREND/SIDEWAYS]
- Moving Averages: [50/150/200 EMA DETAILS]
- Volume Analysis: [DETAILS] [Reasoning]
- Volatility Pattern: [DETAILS] [Reasoning]

**Fundamental Analysis**
- Quarterly EPS Growth: [LAST 3 QUARTERS] [Reasoning]   
- Annual Growth: [DETAILS] [Reasoning]
- Industry Position: [DETAILS] [Reasoning]
- Sector Performance: [DETAILS] [Reasoning]

**Market Analysis**
- Market Direction: [UPTREND/DOWNTREND/SIDEWAYS]
- Supply/Demand Dynamics: [DETAILS] 

**Institutional Ownership**
- Institutional Ownership: [DETAILS] [Reasoning]

**News and Trends**
- News and Trends: [DETAILS] [Reasoning]

**Buy Point Analysis** [Reasoning]
- Current Setup: [DETAILS]
- Buy Point: $[PRICE] (REASON)
- Target Price: $[PRICE] (15-20% from buy point)
- Stop Loss: $[PRICE] (2-3% below buy point)

**Risk Assessment** [Reasoning]
- Market Conditions: [DETAILS]
- Volume Concerns: [DETAILS] [Reasoning]
- Technical Risks: [DETAILS] [Reasoning]

**Final Recommendation** 
- Action: [BUY/WAIT/WATCH]
- Key Triggers: [DETAILS]
- Risk Management: [DETAILS] 

2. JSON FORMAT:
{
  "stock_summary": {
    "ticker": "",
    "current_metrics": {
      "price": 0.00,
      "volume": 0,
      "avg_volume": 0,
      "fifty_two_week": {
        "high": 0.00,
        "low": 0.00
      }
    },
    "technical_analysis": {
      "trend": "", 
      "moving_averages": {
        "ema_50": 0.00,
        "ema_150": 0.00,
        "ema_200": 0.00
      },
      "volume_analysis": "", (reasoning) (details)
      "volatility_pattern": "" (reasoning) (details)
      "distance_from_52_week_high": "" (reasoning) (details)
      "technical_setup": "" (reasoning) (details)
      "technical_setup_trigger": "" (reasoning) (details)
      "technical_setup_trigger_key_triggers": "" (reasoning) (details)
      "technical_setup_trigger_risk_factors": "" (reasoning) (details)
    },
    "fundamental_analysis": {
      "quarterly_eps_growth": [],
      "quarterly_eps_growth_trend": "", (reasoning) (details)
      "annual_growth_trend": "", (reasoning) (details)
      "annual_eps_growth": [],
      "industry_position": "", (reasoning) (details)
      "sector_performance": "" (reasoning) (details)
    },
    "market_analysis": {
      "market_sentiment": "", (reasoning) (details)
      "market_trend": "", (reasoning) (details) (qqq/spy/nasdaq)
      "supply_demand_dynamics": "" (reasoning) (details)
    },
    "institutional_ownership": {
      "institutional_ownership": "", (reasoning) (details)
      "institutional_ownership_trend": "", (reasoning) (details)
    },
    # "news_and_trends": {
    #   "new_product_release": "", (reasoning) (details)
    #   "google_trends": "", (reasoning) (details)
    # },
    "sector_analysis": {
      "sector_performance": "" (reasoning) (details)
      "industry_position": "", (reasoning) (details)
      "sector_supply_demand_dynamics": "" (reasoning) (details)
    },
    "trade_setup": {
      "buy_point": 0.00,
      "target_price": 0.00,
      "stop_loss": 0.00,
      "setup_type": "" (cup, cup with handle, cup with handle and breakout, cup with handle and breakout and volume, wedge, triangle, cup and handle, cup and handle and breakout, cup and handle and breakout and volume, wedge and breakout, triangle and breakout, cup and handle and breakout and volume, wedge and breakout and volume, triangle and breakout and volume)
    },
    "risk_assessment": {
      "market_conditions": "", (reasoning) (details)
      "fundamentals_risks": "", (reasoning) (details)
      "technical_risks": "", (reasoning) (details)
      "volume_risks": "", (reasoning) (details)
      "setup_risks": "", (reasoning) (details)
    },
    "recommendation": {
      "action": "",
      "triggers": [],
      "trigger_reason": "", (reasoning) (details)
      "key_triggers": "", (reasoning) (details) (as specific as possible)
      "risk_factors": [],
      "risk_management": "" (reasoning) (details)
    }
  }
}

TRADING RULES:
1. Only recommend BUY when:
   - Stock is within 8% of 52-week high
   - EPS growth meets minimum criteria
   - Volume is above average
   - Market trend is positive
   
2. Recommend WAIT when:
   - Stock is 8-12% below 52-week high
   - Volume is below average
   - Technical pattern is incomplete

3. Recommend WATCH when:
   - Stock is >12% below 52-week high
   - Fundamentals are strong but technicals are weak
   - Market conditions are unfavorable

Always maintain professional objectivity and provide clear reasoning for all recommendations.
"""

model = ChatOpenAI(model="gpt-4o") 
abot = StockAssistant()

def _format_as_markdown(content: str) -> None:
    """Save the content as a markdown file."""
    with open('stock_analysis.md', 'w') as f:
        f.write(content)

def stock_generator(content):
    messages = [HumanMessage(content="Stock Ticker or Name: "+str(content)+".  Generate a stock trading strategy for this stock and give me the stock summary and analysis based on the rules deifined")]
    result = abot.graph.invoke({"messages": messages})
    try:
        # Save graph to a file instead of displaying
        graph = abot.graph.get_graph()
        graph.draw_mermaid_png(output_file_path="graph.png")
        print("Graph saved as graph.png")
    except Exception as e:
        print(f"Could not generate graph: {e}")
    
    try:
        json_data = result['messages'][-1].content.split("\n\n```json\n")[1].split("\n```")[0]
        # markdown_data = result['messages'][-1].content.split("\n\n```json\n")[0]
        print(json_data)
        price_history = get_stock_quote(content)
    except Exception as e:
        print(f"Could not serialize graph: {e}")
    return _, json_data, price_history