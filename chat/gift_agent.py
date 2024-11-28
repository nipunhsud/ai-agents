
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

tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()

chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
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



gift_agent_prompt = """You are a thoughtful gift recommendation assistant. Your goal is to suggest personalized gift ideas by combining the following:
1. Information provided about the recipient
2. Any past gift-giving history or preferences mentioned
3. Current trends and available products found through web searches

Process for making recommendations:
1. First, analyze the provided information about the recipient and any past gift history
2. Search for relevant gift ideas based on this information using Tavily
3. Compile a curated list of specific gift suggestions, including:
   - Why this gift would be appropriate
   - Approximate price range
   - Where it can be purchased (url)
   - How it relates to the recipient's interests/preferences

Return the response in this format . 
example: 
    **Product Title**
    **Reason**
    **Price**
    **URL**
    **Relation of Interest**


Guidelines:
- Focus on practical, available items that can actually be purchased
- Consider the recipient's age, interests, and any mentioned constraints
- Include a mix of price points unless a specific budget is mentioned
- Validate that suggested items are currently available through your searches
- If searching for multiple items, make separate search calls to ensure accuracy
- If any crucial information is missing (like budget or age), ask for clarification

Remember: The goal is to provide specific, actionable gift ideas rather than generic suggestions. Each recommendation should be justified based on the recipient's profile and current market availability.
"""

model = ChatOpenAI(model="gpt-4o") 
abot = Agent(model, [tool], system=gift_agent_prompt)


def gift_prediction(content):
    
    messages = [HumanMessage(content="Here are information: "+str(content)+". Based on provided information Recommend best 3 gift. ")]
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
