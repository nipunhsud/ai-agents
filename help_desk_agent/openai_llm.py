from langchain.schema import HumanMessage
from langchain.chat_models import ChatOpenAI



chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4o"  # You can also use "gpt-4" if you have access
)



def llm(content):

    messages = [HumanMessage(content=content)]
    response = chat(messages)
    response = str(response.content)

    return response