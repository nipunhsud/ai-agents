

from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from typing import Dict, List, Optional
import json
import os
import ssl
import certifi
from slack_sdk.errors import SlackApiError
from .announcement_generator import SlackAnnouncementGenerator



class SlackTools:
    def __init__(self, slack_token: str):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.client = WebClient(
            token=slack_token,
            ssl=ssl_context
        )
        self.announcement_generator = SlackAnnouncementGenerator()

        
    def get_users_information(self):
        try:
            users = self.client.users_list()
            #print(users)
            all_users = []
            for user in users["members"]:
                # Get title/designation from profile
                title = user.get('profile', {}).get('title', 'No title set')
                #print(f"Username: {user['name']}, ID: {user['id']}, Title: {title}")
                all_users.append(f"Username: {user['name']}, ID: {user['id']}, Title: {title}")
        except SlackApiError as e:
            all_users = None
            print(f"Error: {e}")
        return all_users

    def get_channels_information(self):
        try:
            # Get all channels (public and private if user has access)
            channels = self.client.conversations_list(
                types="public_channel,private_channel"  # You can also add "mpim,im" for group/direct messages
            )
            
            # Print or process channel information
            '''
            for channel in channels["channels"]:
                print(f"Channel Name: {channel['name']}, ID: {channel['id']}, "
                    f"Is Private: {channel.get('is_private', False)}")
            '''
            return channels["channels"]
            
        except SlackApiError as e:
            print(f"Error fetching channels: {e}")
            return None

    def send_message(self, message: str, users: List[str] = None, channels: List[str] = None) -> str:
        """Send a simple message to specified users and channels"""
        status = []
        
        if users:
            for user_id in users:
                try:
                    response = self.client.chat_postMessage(
                        channel=user_id,
                        text=message
                    )
                    status.append(f"Message sent to user {user_id}")
                except Exception as e:
                    status.append(f"Failed to send to user {user_id}: {str(e)}")

        if channels:
            for channel_id in channels:
                try:
                    response = self.client.chat_postMessage(
                        channel=channel_id,
                        text=message
                    )
                    status.append(f"Message sent to channel {channel_id}")
                except Exception as e:
                    status.append(f"Failed to send to channel {channel_id}: {str(e)}")

        return "\n".join(status)

    def send_announcement(self, 
                         type: str,
                         title: str,
                         description: str,
                         users: List[str] = None,
                         channels: List[str] = None,
                         **kwargs) -> str:
        """Send a formatted announcement to specified users and channels"""
        try:
            # Generate announcement blocks
            announcement = self.announcement_generator.generate_announcement(
                type=type,
                title=title,
                description=description,
                date=kwargs.get('date'),
                impact=kwargs.get('impact'),
                next_steps=kwargs.get('next_steps'),
                additional_info=kwargs.get('additional_info')
            )
            
            status = []
            blocks = announcement['blocks']
            
            if users:
                for user_id in users:
                    try:
                        response = self.client.chat_postMessage(
                            channel=user_id,
                            blocks=blocks,
                            text=title  # Fallback text
                        )
                        status.append(f"Announcement sent to user {user_id}")
                    except Exception as e:
                        status.append(f"Failed to send to user {user_id}: {str(e)}")

            if channels:
                for channel_id in channels:
                    try:
                        response = self.client.chat_postMessage(
                            channel=channel_id,
                            blocks=blocks,
                            text=title  # Fallback text
                        )
                        status.append(f"Announcement sent to channel {channel_id}")
                    except Exception as e:
                        status.append(f"Failed to send to channel {channel_id}: {str(e)}")

            return "\n".join(status)
            
        except Exception as e:
            return f"Failed to create or send announcement: {str(e)}"


class SlackAgentTool:
    def __init__(self, slack_token: str, openai_api_key: str):
        self.slack_tools = SlackTools(slack_token)
        
        # Create a ChatOpenAI instance
        self.llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openai_api_key,
            model="gpt-4"  # or whatever model you prefer
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize workspace info
        self.users_info = self.slack_tools.get_users_information()
        self.channels_info = self.slack_tools.get_channels_information()
                
        # Define input schemas
        class MessageInput(BaseModel):
            message: str = Field(..., description="The text message to send")
            users: List[str] = Field(default_factory=list, description="List of user IDs to send the message to")
            channels: Optional[List[str]] = Field(default_factory=list, description="List of channel IDs to send the message to")

        class AnnouncementInput(BaseModel):
            type: str = Field(..., description="Type of announcement (feature/company/milestone/event)")
            title: str = Field(..., description="Title of the announcement")
            description: str = Field(..., description="Main content of the announcement")
            users: List[str] = Field(default_factory=list, description="List of user IDs")
            channels: Optional[List[str]] = Field(default_factory=list, description="List of channel IDs")

        # Create tools with structured inputs
        self.tools = [
            StructuredTool.from_function(
                func=self.slack_tools.send_message,
                name="send_simple_message",
                description="Send a simple text message to Slack users or channels",
                args_schema=MessageInput
            ),
            StructuredTool.from_function(
                func=self.slack_tools.send_announcement,
                name="send_announcement",
                description="Send a formatted announcement to Slack users or channels",
                args_schema=AnnouncementInput
            )
        ]
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        # Set up system message with workspace info and explicit formatting instructions
        self.system_message = SystemMessage(content=f"""
        You are a Slack messaging assistant with access to the following workspace information:
        Users: {self.users_info}
        Channels: {self.channels_info}
        
        When sending messages, use the tools with these parameters:
        1. send_simple_message:
           - message: str (required) - The text message to send
           - users: list[str] (required) - List of user IDs from the workspace info
           - channels: list[str] (optional) - List of channel IDs from the workspace info

        2. send_announcement:
           - type: str (required) - One of: feature, company, milestone, event
           - title: str (required) - Title of the announcement
           - description: str (required) - Main content
           - users: list[str] (required) - List of user IDs from the workspace info
           - channels: list[str] (optional) - List of channel IDs from the workspace info

        Always look up and use the correct user/channel IDs from the workspace information above.
        """)

        print(self.system_message)
    def process_request(self, user_query: str) -> str:
        """Process user requests for sending messages or announcements"""
        try:
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_query}
            ]
            response = self.agent.run(messages)
            return response
        except Exception as e:
            return f"Error processing request: {str(e)}"
        


class SlackAgent:
    def __init__(self, slack_token: str, openai_api_key: str):
        self.slack_tools = SlackTools(slack_token)
        
        self.llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openai_api_key,
            model="gpt-4"
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize workspace info
        self.users_info = self.slack_tools.get_users_information()
        self.channels_info = self.slack_tools.get_channels_information()
                
        # Define input schemas
        class MessageInput(BaseModel):
            message: str = Field(..., description="The text message to send")
            users: List[str] = Field(default_factory=list, description="List of user IDs to send the message to")
            channels: Optional[List[str]] = Field(default_factory=list, description="List of channel IDs to send the message to")

        class AnnouncementInput(BaseModel):
            type: str = Field(..., description="Type of announcement (feature/company/milestone/event)")
            title: str = Field(..., description="Title of the announcement")
            description: str = Field(..., description="Main content of the announcement")
            users: List[str] = Field(default_factory=list, description="List of user IDs")
            channels: Optional[List[str]] = Field(default_factory=list, description="List of channel IDs")

        self.tools = [
            StructuredTool.from_function(
                func=self._preview_message,
                name="send_simple_message",
                description="Send a simple text message to Slack users or channels",
                args_schema=MessageInput
            ),
            StructuredTool.from_function(
                func=self._preview_announcement,
                name="send_announcement",
                description="Send a formatted announcement to Slack users or channels",
                args_schema=AnnouncementInput
            )
        ]
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        self.system_message = SystemMessage(content=f"""
        You are a Slack messaging assistant with access to the following workspace information:
        Users: {self.users_info}
        Channels: {self.channels_info}
        
        When sending messages, use the tools with these parameters:
        1. send_simple_message:
           - message: str (required) - The text message to send
           - users: list[str] (required) - List of user IDs from the workspace info
           - channels: list[str] (optional) - List of channel IDs from the workspace info

        2. send_announcement:
           - type: str (required) - One of: feature, company, milestone, event
           - title: str (required) - Title of the announcement
           - description: str (required) - Main content
           - users: list[str] (required) - List of user IDs from the workspace info
           - channels: list[str] (optional) - List of channel IDs from the workspace info

        Always look up and use the correct user/channel IDs from the workspace information above.
        """)
        
        # Store previewed messages
        self.previewed_messages = []

    def _preview_message(self, message: str, users: List[str] = None, channels: List[str] = None) -> str:
        """Store message preview instead of sending"""
        preview = {
            'type': 'simple_message',
            'content': message,
            'recipients': {
                'users': users or [],
                'channels': channels or []
            }
        }
        self.previewed_messages.append(preview)
        return "Message preview stored"

    def _preview_announcement(self, type: str, title: str, description: str, 
                            users: List[str] = None, channels: List[str] = None) -> str:
        """Store announcement preview instead of sending"""
        preview = {
            'type': 'announcement',
            'content': {
                'type': type,
                'title': title,
                'description': description
            },
            'recipients': {
                'users': users or [],
                'channels': channels or []
            }
        }
        self.previewed_messages.append(preview)
        return "Announcement preview stored"

    def generate_preview(self, user_query: str) -> List[dict]:
        """Generate message previews from user query"""
        try:
            # Clear previous previews
            self.previewed_messages = []
            
            # Generate preview
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_query}
            ]
            self.agent.run(messages)
            
            # Return previews
            return self.previewed_messages
            
        except Exception as e:
            raise Exception(f"Error generating preview: {str(e)}")

    def send_messages(self, messages: List[dict]) -> List[str]:
        """Send a list of edited messages"""
        try:
            results = []
            for msg in messages:
                if msg['type'] == 'simple_message':
                    result = self.slack_tools.send_message(
                        message=msg['content'],
                        users=msg['recipients']['users'],
                        channels=msg['recipients']['channels']
                    )
                else:
                    result = self.slack_tools.send_announcement(
                        type=msg['content']['type'],
                        title=msg['content']['title'],
                        description=msg['content']['description'],
                        users=msg['recipients']['users'],
                        channels=msg['recipients']['channels']
                    )
                results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error sending messages: {str(e)}")

    def get_workspace_info(self) -> dict:
        """Get workspace information for the UI"""
        return {
            'users': self.users_info,
            'channels': self.channels_info
        }