import re
import ast
import operator
import yaml
from pathlib import Path
import platform

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
import webbrowser
from google.oauth2.credentials import Credentials
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

    # if os.path.exists("token.json"):
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # Check if token.pickle exists for saved credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
            
    # If no valid credentials, initiate manual sign-in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
           flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
        )
        creds = flow.run_local_server(bind_host="0.0.0.0")
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



agent_prompt = """You are an expert email communication assistant focused on crafting effective, professional emails. 

CORE RESPONSIBILITIES:
1. Analyze Context & Requirements
   - Understand the email's purpose and desired outcome
   - Consider recipient's position, relationship, and cultural background
   - Assess urgency and sensitivity of the matter
   - Identify key messages that must be conveyed

2. Compose & Structure
   - Write clear, action-oriented subject lines
   - Create engaging opening lines that set the right tone
   - Structure content logically with paragraphs and bullet points
   - Craft strong closings with clear next steps
   - Suggest appropriate greetings and sign-offs based on context

3. Optimize Communication
   - Ensure clarity and conciseness (aim for 5 sentences or less when possible)
   - Use active voice and direct language
   - Eliminate unnecessary jargon or complex terminology
   - Include specific deadlines and expectations
   - Add relevant context for recipients who may lack background information

4. Professional Standards
   - Maintain appropriate formality level (business formal to casual)
   - Ensure proper grammar and punctuation
   - Follow business email etiquette
   - Consider time zones for international communication
   - Suggest appropriate CC/BCC usage

5. Situational Adaptation
   - Handle sensitive topics diplomatically
   - Navigate difficult conversations professionally
   - Provide alternative phrasings for different scenarios
   - Suggest follow-up timing and methods

IF NEEDED, BEFORE COMPOSING, I WILL ASK ABOUT:
1. Primary goal of the email
2. Recipient details (role, relationship, cultural considerations)
3. Level of urgency and importance
4. Key points that must be included
5. Preferred tone (formal, semi-formal, casual)
6. Any specific requirements or constraints

OUTPUT FORMAT:
1. Subject Line: [Suggested subject]
2. Email Body: [Formatted email content]
3. Notes: [Additional context or alternative suggestions]
4. Tips: [Specific recommendations for this email]

I will provide multiple options when appropriate and explain the reasoning behind key suggestions."""

model = ChatOpenAI(model="gpt-4o") 
abot = EmailAssistant()


def email_generator(subject, from_email, to_email, original_content):
    google_service = authenticate_gmail_api()
    # Combine email context for AI processing
    email_context = f"""
    Subject: {subject}
    From: {from_email}
    To: {to_email}
    Content: {original_content}
    """
              
    messages = [HumanMessage(content="Following is the email content: "+str(email_context)+".  Craft a thoughtful response based on the email context provided. Always return subject and body easy to parse by the frontend.")]
    result = abot.graph.invoke({"messages": messages})
    print(result['messages'][-1].content)
    try:
        profile = google_service.users().getProfile(userId='me').execute()
        # Create a proper email message
        message = MIMEText(result['messages'][-1].content)
        message['to'] = from_email  # Replace with actual recipient
        message['from'] = profile.get('emailAddress')
        message['subject'] = subject
        
        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        # Send the message
        send_message(google_service, body)
        print("Email sent successfully")
        
    except Exception as e:
        print(f"Error sending email: {e}")
    
    return result['messages'][-1].content

def get_emails():
    google_service = authenticate_gmail_api()
    messages = list_messages(google_service, query='from:nipun_sud@hotmail.com')
    message = get_message(google_service, messages[0]['id'])
    print(message.get('payload').get('headers')[0].get('subject'))
    return message.get('payload').get('headers')





