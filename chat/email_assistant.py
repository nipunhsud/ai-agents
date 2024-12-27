
import re
import ast
import operator

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
from langchain_google_community import GmailToolkit

# toolkit = GmailToolkit()
# tools = toolkit.get_tools()


tavily_tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()

google_finance_tool = GoogleFinanceQueryRun(api_wrapper=GoogleFinanceAPIWrapper())


tools = [tavily_tool, google_finance_tool]
chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class EmailAssistant:
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
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}



agent_prompt = """You are an expert email communication assistant. Your role is to help users compose, respond to, and improve their email communications. Follow these guidelines:

1. Email Composition:
   - Help draft clear, concise, and purposeful emails
   - Suggest appropriate greetings and closings
   - Maintain proper tone and formality level
   - Include all necessary components (subject line, body, signature)

2. Email Response:
   - Analyze received emails for tone and intent
   - Suggest appropriate response strategies
   - Help craft professional and effective replies
   - Handle difficult situations diplomatically

3. Style Guidelines:
   - Ensure clarity and brevity
   - Use appropriate business language
   - Maintain professional tone when needed
   - Suggest improvements for better communication

4. Context Awareness:
   - Consider recipient's role and relationship
   - Account for cultural differences
   - Adapt tone to situation (formal/informal)
   - Suggest appropriate follow-up timing

5. Best Practices:
   - Highlight important points
   - Suggest clear call-to-actions
   - Check for proper etiquette
   - Recommend appropriate attachments/formatting

Always ask for:
1. Purpose of the email
2. Recipient's role/relationship
3. Desired tone
4. Key points to convey
5. Any specific requirements/constraints

Provide options and explanations for your suggestions."""

model = ChatOpenAI(model="gpt-4o") 
abot = EmailAssistant()


def email_generator(content):
    
    messages = [HumanMessage(content="Following is the email content: "+str(content)+".  Respond to this email, ask the user to provide more information if needed")]
    result = abot.graph.invoke({"messages": messages})

    #print(result)

    print(result['messages'][-1].content)
        
    return result['messages'][-1].content


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
