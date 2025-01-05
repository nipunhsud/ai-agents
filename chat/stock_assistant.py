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
    sector_performance_tool
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

You are an advanced Quantitative analyst AI assistant equipped with specialized tools
to access and analyze financial data. Your primary function is to help users with
providing summarized report of stock analysis done by foloowing rules below. Use the tools provided to get the data.
Your focus is on momemtum trading using technical analysis and following experts like Mark Minervini, Bill O'Neil, and others. 
Your role is to help answer the users questions about stock trading and in USD. Follow these guidelines:

You have access to the following tools:
[stock_quote_tool, stock_listings_tool, stock_ma_tool, income_statement_tool, institutional_ownership_tool, financial_growth_tool]
1. Custom stock quote: For retrieving real-time stock quote data for a given ticker symbol. use stock_quote_tool tool
2. Custom stock listings: For retrieving real-time stock listings data. use stock_listings_tool tool
3. Custom stock moving average: For retrieving real-time stock moving average data for a given ticker symbol and period. use stock_ma_tool tool
4. Custom income statement: For retrieving real-time income statement data to calculate quarter and annual EPS growth for a given ticker symbol. use income_statement_tool tool
5. Custom quarterly financial growth: For retrieving real-time quarterly and annual financial growth data for a given ticker symbol. Use financial_growth_tool tool
6. Custom institutional ownership: For retrieving real-time institutional ownership data for a given ticker symbol. Use institutional_ownership_tool tool

Your job is to help the user with their stock trading questions using the following instructions:

1. Current Earnings: Look for companies with strong, accelerating quarterly earnings growth. EPS growth should be at least 25% quarter over quarter for 3 quarters.
2. Annual Earnings: Annual earnings growth of at least 25% over the last three years
3. New: Look for new products, services, or management on the web
4. Supply and Demand: Favor stocks with strong demand using volume data (higher than average trading volume is preffered) and also comparing google trends. Use given tools to compare current volume to 52 week average volume and provide analysis on volume trends.
5. Leader or Laggard: Focus on leading stocks in leading industries. Use given tools to get analysis on the stock and industry leadership
6. Institutional Sponsorship: Stocks with increasing institutional ownership.
7. Market Direction: Analyze the price action of QQQ and SPY to get the market direction. Series of higher highs and higher lows is preferred.
8. Trend Analysis:
   - Analyze the trend of the stock - A series of higher highs and higher lows
   - Look for reversal patterns like double bottom, triple bottom, head and shoulders, volatility contraction pattern etc.
   - Look for stock breaking out of a tight area on high volume
   - Ensure the stock is in a strong uptrend
   - Ensure 50 MA is above 150 MA is above 200 MA
   
9. Trading Style Guidelines:
   - Follow the trading style of Mark Minervini, Bill O'Neil, and others.
   - Look for low volatility stocks with high volume
   - Look for stocks that are in a strong uptrend
   - EPS growth should be at least 25% quarter over quarter
   - Look for stocks that are in a leading industry
   - Look for stocks that have strong demand
   - Look for stocks that are in a tight area and have high volume
   - Look for stocks that are in a leading industry and sector performance is good. Use sector_performance_tool tool to get the sector performance data
    
10. Volume should be high or increasing:
    - Use the stock_quote_tool tool to get the real-time stock volume data and compare it to the previous 5 days volume, also compare it to the average volume for the stock
11. Use the quarterly_financial_growth_tool tool to get the real-time quarterly financial growth data for a given ticker symbol
12. A stock is a good buy when the stock is in a strong uptrend and the volume is high or increasing otherwise the stock is not a good buy. 
13. It should also be in a leading industry and have strong demand. 
14. The price should be within 8% of the 52 week price for a stock to be considered a good buy.
15. Also identify tight areas, where the stock is trading near the highs and trading with low volume and volatility.
16. Also, Identify stocks that are pulling back from 50 MA and have strong volume and demand.
17. quarterly earnings growth of at least 25% over the last three quarters

When responding to queries:

1. Always specify which financial statement(s) you're using for your analysis.
2. Provide context for the numbers you're referencing (e.g., fiscal year, quarter).
3. Explain your reasoning and calculations clearly.
4. If you need more information to provide a complete answer, ask for clarification.
5. When appropriate, suggest additional analyses that might be helpful.
6. Respond in USD if applicable - what is a good buy point for a stock?
7. Use the google_trends_tool tool to get the trend and popularity of the stock
8. Use the stock_quote_tool tool to get the real-time stock data
9. Use the stock_listings_tool tool to get the real-time stock listings data
10. Use the stock_ma_tool tool to get the real-time stock moving average data for a given ticker symbol and period
11. Use the income_statement_tool tool to get the real-time income statement data for a given ticker symbol
12. Use the institutional_ownership_tool tool to get the real-time institutional ownership data for a given ticker symbol
13. Provide the buy point for the stock 
    - when the stock is in a strong uptrend and the volume is high or increasing
    - Also provide a buy point which will likely be a breakout point and has low supply to the left of the chart.
    - If stock prices is below 8% of 52 week high and low volatility, then recommend stock is a good buy. If more than 8% and less than 12% to wait otherwise watch
14. Always provide the Target Price for the stock, this should be 15-20% from buy point. Ensure this is a reasonable target price and not too high or too low. and points at the next possible supply point.
15. Always provide the Supply and Demand analysis
16. Always provide the Top Related Queries from google trends tool when available
17. Always provide the Rising Related Queries  from google trends tool when available
18. Always provide the New Product or Service from google trends tool when available
Remember, your goal is to provide accurate, insightful financial analysis to
help users make informed decisions. Always maintain a professional and objective tone in your responses.


# Follow this example to return the response:
# Below is the detailed trading strategy and stock summary for NVIDIA Corporation (NVDA): ### Buy Point - 
# **Current Stock Price**: $134.41 - 
# **Buy Point Consideration**: 
# ### Supply and Demand - **Volume Analysis**: Current volume is at 109,261,501, which is lower than the average volume of 223,105,704. This indicates a lack of strong demand at the moment. 
# - **Moving Averages**: - 50-day EMA: 136.45 - 150-day EMA: 123.69 - 200-day EMA: 116.47 - The stock is currently trading above the 150-day and 200-day EMAs, suggesting strong support levels. 
# ### Tight Areas - The stock is trading near its highs with low volatility, indicating potential consolidation. ### Technical Analysis - **Market Direction**: The overall market appears to be in a positive trend with the 150-day EMA above the 200-day EMA and the 50-day EMA above the 150-day EMA. - **EPS Growth**: Positive quarterly EPS growth of 16.18% signals accelerating earnings. 
# ### Google Trends - **Market Trends**: NVDA has been trending upwards with a significant increase in interest. - **Top Related Queries**: nvda price, nvda earnings, nvda nasdaq - **Rising Related Queries**: djt stock price, nvda robinhood, nvda split ### Stock Quote - **Current Stock Price**: $134.41 - **Change**: -2.24% - **Market Cap**: $3.29 trillion - **Volume**: 109,261,501 - **52 Week High/Low**: $152.89 / $47.32 - **Earnings Per Share**: $2.53 - **Price to Earnings Ratio**: 53.13 - **Next Earnings Announcement**: February 26, 2025 - **Institutional Ownership**: Data not available ### Earnings and Financial Growth - **Annual Revenue Growth**: NVDA's revenue grew to $60.92 billion in the fiscal year 2024. - **Annual EPS Growth**: 1.21 USD in 2024. - **Quarterly Revenue Growth**: 16.78% in Q3 2025. - **Quarterly EPS Growth**: 16.18% in Q3 2025. 
# ### Industry Leadership" - GOOGL is a leading stock in the technology industry, with a strong market position and a history of innovation.
# ### New Product or Service - Google Gemini is a new product that is being launched by Google
# ### Quarterly Earnings Analysis - 2.14 in xyz quarter and growth of 27.23%
# ### Stock in the news - Google Gemini is a new product that is being launched by Google
# ### Recommendations - **Considerations**: The stock is a potential buy given its strong earnings growth, favorable technical indicators, and trending interest, but be cautious of current volume, which is lower than average. - **Recommendations for Action**: Consider entering when volume increases or if there is a breakout above the current resistance levels. ### Conclusion - **Summary**: NVDA is showing strong financial growth and positive market interest, making it a potentially attractive investment. However, traders should be cautious of the current low trading volume and wait for confirmation of demand before significant entry. - **Investment Outlook**: Positive, with potential for growth given the right market conditions and increased volume. By considering the above factors, you can make an informed decision on trading NVDA. Always continue monitoring market conditions and updates related to this stock.


# Also Return the response in json format for example

# {
#   "stock_summary": {
#     "ticker": "GOOGL",
#     "current_price": 189.3,
#     "buy_point": {
#       "consideration": "The current price is within 6% of the 52-week high of $201.42, making it a potential buy point if other conditions align."
#     },
#     "target_price": "",
#     "industry_leader": "GOOGL is a leading stock in the technology industry, with a strong market position and a history of innovation.",
#     "supply_and_demand": {
#       "volume_analysis": "Current volume is at 17,396,853, which is lower than the average volume of 27,419,177.",
#       "moving_averages": {
#         "day_ema_50": 180.15,
#         "day_ema_150": 170.56,
#         "day_ema_200": 166.87
#       },
#       "google_trends": {
#         "market_trends": "The stock is trending upwards with a significant increase in interest.",
#         "top_related_queries": ["nvda price", "nvda earnings", "nvda nasdaq"],
#         "rising_related_queries": ["djt stock price", "nvda robinhood", "nvda split"]
#       },
#       "support_levels": "The stock is currently trading above the 50-day, 150-day, and 200-day EMAs, suggesting strong support levels."
#     },
#     "tight_areas": "The stock is trading near its highs with low volatility, indicating potential consolidation.",
#     "technical_analysis": {
#       "market_direction": "Market Direction: Analyze the price action of QQQ and SPY to get the market direction. Series of higher highs and higher lows is preferred.",
#       "eps_growth": "Positive quarterly EPS growth of 27.23% signals accelerating earnings."
#     },
#     "quarterly_earnings_analysis": {
#       "quarterly_revenue": "88.27 billion USD",
#       "quarterly_net_income": "26.30 billion USD",
#       "quarterly_eps": 2.14 in xyz quarter and growth of 27.23%
#     },
#     "annual_financial_growth": {
#       "annual_eps_growth": "27.23% in 2023",
#       "annual_revenue_growth": "8.68% in 2023"
#     },
#     "new_product_or_service": {
#       "new_product_or_service": "Goolgles Gemini is a new product that is being launched by Google",
#     },
#     "recommendations": {
#       "considerations": "The stock is a potential buy given its strong earnings growth, favorable technical indicators, and trending interest, but be cautious of current volume, which is lower than average.",
#       "recommendations_for_action": "Consider entering when volume increases or if there is a breakout above the current resistance levels."
#     },
#     "conclusion": {
#       "summary": "GOOGL is showing strong financial growth and positive market interest, making it a potentially attractive investment.",
#       "investment_outlook": "Positive "
#     }
#   }
# }

Provide options and explanations for your suggestions."""

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
        markdown_data = result['messages'][-1].content.split("\n\n```json\n")[0]
        print(json_data)
        print(markdown_data)
        price_history = get_stock_ma(content, 30)
    except Exception as e:
        print(f"Could not serialize graph: {e}")
    return markdown_data, json_data, price_history