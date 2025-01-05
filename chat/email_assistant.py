import re
import ast
import operator
import yaml
from pathlib import Path

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
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText

from ai_assistant.utils import load_email_templates, save_email_template

SCOPES = ['https://mail.google.com/']
tavily_tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()



tools = [tavily_tool]
chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)

def authenticate_gmail_api():
    creds = None
    # Check if token.pickle exists for saved credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If no valid credentials, initiate manual sign-in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def list_messages(service, user_id='me', query=''):
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def get_message(service, message_id, user_id='me'):
    try:
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        return message
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def create_reply_message(service, message_id, reply_text, user_id='me'):
    try:
        original_message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        headers = original_message['payload']['headers']
        subject = ''
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
                if not subject.startswith('Re:'):
                    subject = 'Re: ' + subject
            if header['name'] == 'From':
                sender = header['value']
            if header['name'] == 'To':
                recipient = header['value']

        reply = MIMEText(reply_text)
        reply['to'] = sender
        reply['from'] = recipient
        reply['subject'] = subject
        reply['In-Reply-To'] = original_message['id']
        raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        body = {'raw': raw}
        return body
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def send_message(service, message_body, user_id='me'):
    try:
        message = service.users().messages().send(userId=user_id, body=message_body).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def create_reply_message(service, message_id, reply_text, user_id='me'):
    try:
        original_message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        headers = original_message['payload']['headers']
        subject = ''
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
                if not subject.startswith('Re:'):
                    subject = 'Re: ' + subject
            if header['name'] == 'From':
                sender = header['value']
            if header['name'] == 'To':
                recipient = header['value']

        reply = MIMEText(reply_text)
        reply['to'] = sender
        reply['from'] = recipient
        reply['subject'] = subject
        reply['In-Reply-To'] = original_message['id']
        raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        body = {'raw': raw}
        return body
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def send_message(service, message_body, user_id='me'):
    try:
        message = service.users().messages().send(userId=user_id, body=message_body).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as error:
        print(f'An error occurred: {error}')
        return None


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class EmailAssistant:
    def __init__(self):
        self.service = authenticate_gmail_api()
        self.system = agent_prompt
        self.templates = load_email_templates()
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
    print(result['messages'][-1].content)
    try:
        profile = abot.service.users().getProfile(userId='me').execute()
        # Create a proper email message
        message = MIMEText(result['messages'][-1].content)
        message['to'] = 'nipun@turf.ai'  # Replace with actual recipient
        message['from'] = profile.get('emailAddress')
        message['subject'] = 'AI Assistant Response'
        
        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        # Send the message
        send_message(abot.service, body)
        print("Email sent successfully")
        print(profile.emailAddress)
        
    except Exception as e:
        print(f"Error sending email: {e}")
    
    return result['messages'][-1].content






