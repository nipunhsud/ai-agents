import re
import ast
import operator
import yaml
import json
from pathlib import Path
import platform
import pickle
import sys
import os
from django.contrib.auth.models import User
from django.db import models

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import GmailToken directly from the same directory
from .models import GmailToken

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
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
import webbrowser
from google.oauth2.credentials import Credentials
from ai_assistant.utils import load_email_templates, save_email_template
import smtplib
import subprocess

SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.modify'
]
tavily_tool = TavilySearchResults(max_results=4) #increased number of results
_ = load_dotenv()

tools = [tavily_tool]
chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)

def setup_chrome():
    """Setup Chrome for headless operation"""
    try:
        # Check if Chrome is installed in the storage directory
        chrome_bin = os.getenv('CHROME_BIN')
        if not chrome_bin or not os.path.exists(chrome_bin):
            # If not found, try to find Chrome in the storage directory
            storage_dir = '/opt/render/project/.render/chrome'
            chrome_bin = os.path.join(storage_dir, 'opt/google/chrome/google-chrome')
            if os.path.exists(chrome_bin):
                os.environ['CHROME_BIN'] = chrome_bin
            else:
                # Install Chrome if not found
                subprocess.run(['apt-get', 'update'], check=True)
                subprocess.run(['apt-get', 'install', '-y', 'google-chrome-stable'], check=True)
                # Set Chrome binary path
                os.environ['CHROME_BIN'] = '/usr/bin/google-chrome'
    except Exception as e:
        print(f"Error setting up Chrome: {e}")
        raise

def get_auth_url():
    """
    Get the authorization URL for Gmail OAuth.
    
    Returns:
        tuple: (auth_url, state) for OAuth flow
    """
    try:
        print("Starting get_auth_url") # Debug print
        
        # Set the redirect URI based on environment
        is_local = os.getenv('APP_ENV', 'local') == 'local'
        redirect_uri = 'http://localhost:8000/gmail/callback/' if is_local else 'https://www.backend.purnam.ai/gmail/callback/'
        print(f"Using redirect URI: {redirect_uri}") # Debug print
        
        # Create flow with redirect URI
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            SCOPES,
            redirect_uri=redirect_uri
        )
        print("Created flow object") # Debug print
        
        # Get the authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure we get refresh token
        )
        print(f"Generated auth URL: {auth_url}") # Debug print
        print(f"Generated state: {state}") # Debug print
        
        return auth_url, state
    except Exception as e:
        print(f"Error in get_auth_url: {str(e)}") # Debug print
        raise

def exchange_code_for_token(code):
    """
    Exchange authorization code for access token.
    
    Args:
        code: The authorization code from OAuth callback
        
    Returns:
        Credentials object
    """
    try:
        print("Starting exchange_code_for_token") # Debug print
        
        # Set the redirect URI based on environment
        is_local = os.getenv('APP_ENV', 'local') == 'local'
        redirect_uri = 'http://localhost:8000/gmail/callback/' if is_local else 'https://www.backend.purnam.ai/gmail/callback/'
        print(f"Using redirect URI: {redirect_uri}") # Debug print
        
        # Create flow with redirect URI
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            SCOPES,
            redirect_uri=redirect_uri
        )
        print("Created flow object") # Debug print
        
        # Exchange the code for tokens
        flow.fetch_token(
            code=code,
            client_id=flow.client_config['client_id'],
            client_secret=flow.client_config['client_secret']
        )
        print("Successfully exchanged code for tokens") # Debug print
        
        # Get the credentials
        creds = flow.credentials
        print(f"Got credentials type: {type(creds)}") # Debug print
        
        # Convert to dictionary for storage
        token_dict = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        print("Created token dictionary") # Debug print
        
        return token_dict
    except Exception as e:
        print(f"Error in exchange_code_for_token: {str(e)}") # Debug print
        raise

def authenticate_gmail_api(user):
    """
    Authenticate Gmail API for a specific user.
    
    Args:
        user: Django User object
        
    Returns:
        Gmail API service object or None if authentication is needed
    """
    # Check if running locally
    is_local = os.getenv('APP_ENV', 'local') == 'local'
    print(f"Environment: {'local' if is_local else 'production'}") # Debug print
    print(f"User: {user.username}") # Debug print
    
    if not is_local:
        # Setup Chrome for headless operation on non-local environment
        setup_chrome()
    
    creds = None
    
    # Try to get existing token from database
    try:
        gmail_token = GmailToken.objects.get(user=user)
        print("Found existing Gmail token") # Debug print
        print(f"Token data type: {type(gmail_token.token_data)}") # Debug print
        
        # Convert memoryview to bytes if needed
        if isinstance(gmail_token.token_data, memoryview):
            token_data = gmail_token.token_data.tobytes()
        else:
            token_data = gmail_token.token_data
            
        # Load the token data
        token_dict = pickle.loads(token_data)
        print(f"Loaded token dict type: {type(token_dict)}") # Debug print
        
        # Convert to Credentials object
        creds = Credentials(
            token=token_dict.get('token'),
            refresh_token=token_dict.get('refresh_token'),
            token_uri=token_dict.get('token_uri'),
            client_id=token_dict.get('client_id'),
            client_secret=token_dict.get('client_secret'),
            scopes=token_dict.get('scopes', SCOPES)
        )
        print(f"Created credentials type: {type(creds)}") # Debug print
        
        # Check if token needs refresh
        if creds and creds.token:
            try:
                # Try to refresh the token
                creds.refresh(Request())
                print("Token refreshed successfully") # Debug print
                
                # Save the refreshed token
                token_dict = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                
                GmailToken.objects.update_or_create(
                    user=user,
                    defaults={'token_data': pickle.dumps(token_dict)}
                )
                print("Refreshed token saved to database") # Debug print
            except Exception as e:
                print(f"Error refreshing token: {e}") # Debug print
                print(f"Error type: {type(e)}") # Debug print
                print(f"Error details: {str(e)}") # Debug print
                return None
        else:
            print("No valid token available") # Debug print
            return None
            
    except GmailToken.DoesNotExist:
        print("No existing Gmail token found") # Debug print
        return None
        
    print("Authentication successful, building Gmail service") # Debug print
    try:
        service = build('gmail', 'v1', credentials=creds)
        print(f"Gmail service built successfully: {service}") # Debug print
        return service
    except Exception as e:
        print(f"Error building Gmail service: {e}") # Debug print
        print(f"Error type: {type(e)}") # Debug print
        print(f"Error details: {str(e)}") # Debug print
        return None

def list_messages(service, user_id='me', query=''):
    """
    List messages in the user's mailbox.
    
    Args:
        service: Gmail API service instance
        user_id: User's email address or 'me'
        query: Query string to filter messages
        
    Returns:
        List of messages or None if service is None
    """
    if service is None:
        print("Service is None in list_messages")
        return None
        
    try:
        print(f"Fetching messages with query: {query}")
        print(f"Service object type: {type(service)}")
        print(f"Service object: {service}")
        
        # Get the messages list
        messages_list = service.users().messages()
        print(f"Messages list object: {messages_list}")
        
        # Execute the list request
        response = messages_list.list(userId=user_id, q=query).execute()
        print(f"Gmail API response: {response}")
        
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
            print(f"Found {len(messages)} messages")
            print(f"First message ID: {messages[0]['id'] if messages else 'No messages'}")
        else:
            print("No messages found in response")
            print(f"Full response: {response}")
            
        return messages
    except Exception as error:
        print(f'Error in list_messages: {error}')
        print(f'Error type: {type(error)}')
        print(f'Error details: {str(error)}')
        return None

def get_message(service, message_id, user_id='me'):
    """
    Get a specific message by ID.
    
    Args:
        service: Gmail API service instance
        message_id: ID of the message to retrieve
        user_id: User's email address or 'me'
        
    Returns:
        Message object or None if service is None
    """
    if service is None:
        print("Service is None in get_message")
        return None
        
    try:
        print(f"Fetching message with ID: {message_id}")
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        print(f"Got message: {message.get('snippet', 'No snippet')}")
        return message
    except Exception as error:
        print(f'Error in get_message: {error}')
        return None

def create_reply_message(service, message_id, reply_text, user_id='me'):
    """
    Create a reply message.
    
    Args:
        service: Gmail API service instance
        message_id: ID of the message to reply to
        reply_text: Text of the reply
        user_id: User's email address or 'me'
        
    Returns:
        Message object or None if service is None
    """
    if service is None:
        print("Service is None in create_reply_message")
        return None
        
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
        print(f'Error in create_reply_message: {error}')
        return None

def send_message(service, message_body, user_id='me'):
    """
    Send a message.
    
    Args:
        service: Gmail API service instance
        message_body: Message body to send
        user_id: User's email address or 'me'
        
    Returns:
        Message object or None if service is None
    """
    if service is None:
        print("Service is None in send_message")
        return None
        
    try:
        message = service.users().messages().send(userId=user_id, body=message_body).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as error:
        print(f'Error in send_message: {error}')
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


OUTPUT FORMAT IN JSON:
1. Subject Line: [Suggested subject]
2. Email Body: [Formatted email content]
3. Notes: [Additional context or alternative suggestions]
4. Tips: [Specific recommendations for this email]

I will provide multiple options when appropriate and explain the reasoning behind key suggestions."""

model = ChatOpenAI(model="gpt-4o") 
abot = EmailAssistant()


def email_generator(subject, from_email, to_email, original_content, reply_content):
    # Combine email context for AI processing
    email_context = f"""
    Subject: {subject}
    From: {from_email}
    To: {to_email}
    Content: {original_content}
    """
    print("Email Context:", email_context)
    messages = [HumanMessage(content="Following is the email content: "+str(email_context)+". And this is the users prompt:"+reply_content+" Craft a thoughtful response based on the email context provided. Always return subject and body easy to parse by the frontend.")]
    result = abot.graph.invoke({"messages": messages})
    print("Raw Response:", result['messages'][-1].content)
    
    # Parse JSON data
    try:
        message_content = result['messages'][-1].content
        print("Message Content:", message_content)
        # Extract JSON from the response
        json_start = message_content.find('{')
        json_end = message_content.rfind('}') + 1
        if json_start == -1 or json_end == -1:
            raise ValueError("Could not find JSON in response")
            
        json_str = message_content[json_start:json_end]
        print("Extracted JSON:", json_str)
        json_data = json.loads(json_str)
        print("Parsed JSON:", json_data)
        
        # Extract email body from the parsed JSON
        email_body = json_data.get('Email Body', '')
        subject = json_data.get('Subject Line', '')
        if not email_body:
            raise ValueError("Email Body not found in response")
            
        return json_data
    except Exception as e:
        print(f"Error parsing response: {e}")
        return result['messages'][-1].content  # Return raw content if parsing fails

def construct_query(query_params):
    """
    Construct a Gmail API query string from parameters.
    
    Args:
        query_params: Dictionary of query parameters
        
    Returns:
        Query string for Gmail API
    """
    query_parts = []
    
    if 'subject' in query_params:
        query_parts.append(f"subject:{query_params['subject']}")
    
    if 'newer_than' in query_params:
        days, unit = query_params['newer_than']
        query_parts.append(f"newer_than:{days}{unit}")
    
    query = ' '.join(query_parts)
    print(f"Constructed query: {query}")
    return query




