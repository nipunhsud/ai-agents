import ssl
import json
import certifi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .openai_llm import llm
from .announcement_generator import SlackAnnouncementGenerator

ssl_context = ssl.create_default_context(cafile=certifi.where())


client = WebClient(
    token='xoxb-8032017402916-8106281877078-CWv8lJ0WhgGMC3dndfP4o6rS',
    ssl=ssl_context
)


def get_users_information():
    try:
        users = client.users_list()
        print(users)
        for user in users["members"]:
            # Get title/designation from profile
            title = user.get('profile', {}).get('title', 'No title set')
            #print(f"Username: {user['name']}, ID: {user['id']}, Title: {title}")
    except SlackApiError as e:
        users = None
        print(f"Error: {e}")
    return users


def get_channels_information():
    try:
        # Get all channels (public and private if user has access)
        channels = client.conversations_list(
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




def publish_announcements(feature_announcement,users,channels):
    '''
    blocks=feature_announcement['blocks']
    title_text = feature_announcement['blocks'][0]['text']['text']
    try:
        response = client.chat_postMessage(
            channel='U082C5XMQTW',
            #channel='U080SKD43D3',
            blocks=blocks,  # Send the blocks directly
            text=title_text  # Fallback text for notifications
        )
        print(f"Message sent: {response['ts']}")
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")
    '''

    print("??????")
    print(feature_announcement)
    print(users)
    print(channels)
    blocks=feature_announcement['blocks']
    title_text = feature_announcement['blocks'][0]['text']['text']
    
    if users:
        for user in users:
            try:
                response = client.chat_postMessage(
                    channel=user,
                    blocks=blocks,  # Send the blocks directly
                    text=title_text  # Fallback text for notifications
                )
                print(f"Message sent: {response['ts']}")
            except SlackApiError as e:
                print(f"Error: {e.response['error']}")

    if channels:
        for channel in channels:
            try:
                response = client.chat_postMessage(
                    channel=channel,
                    blocks=blocks,  # Send the blocks directly
                    text=title_text # Fallback text for notifications
                )
                print(f"Message sent: {response['ts']}")
            except SlackApiError as e:
                print(f"Error: {e.response['error']}")

    


tool1 = {
        "type": "function",
        "name": "generate_announcement",
        "description": "It will return Dict containing formatted Slack message blocks basend on type,title,description,date,impact,next_steps,additional_info .",
        "parameters": {
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Type of announcement ('feature', 'company', 'milestone', 'event')",
                },
                "title": {
                    "type": "string",
                    "description": "Main announcement title",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of announcement.",
                },
                "date": {
                    "type": "string",
                    "description": "Relevant date (optional)",
                },
                "impact": {
                    "type": "string",
                    "description": "Impact description (optional)",
                },
                "next_steps": {
                    "type": "list",
                    "description": "List of next steps (optional)",
                },
                "additional_info": {
                    "type": "string",
                    "description": "Any additional fields specific to the announcement type",
                },
                

            },
            "required": ["type", "title","description"],
        },
    }
    

tool2 = {   
        "type": "function",
        "name": "publish_announcements",
        "description":"This will publish announcement to slack channel or direct messages.",
        "parameters": {
            "properties": {
                "announcement": {
                    "type": "Dict",
                    "description": "Returned Dict from generate_announcement function ",
                },
                "users": {
                    "type": "list",
                    "description": "list of user id to send.(Required, but could be empty list)",
                },
                "channels": {
                    "type": "list",
                    "description": "list of the channels id to send.(Required, but could be empty list)",
                }
            },
            "required": ["announcement", "users","channels"],
        },

    }



information = [
    {   
        "type": "users_information",
        "description":"Here are all available user's information in slack workspace. With their Username , ID , Title(optional)",
        "slack_users_info":get_users_information()
    },
    {   
        "type": "channels_information",
        "description":"Here are all available channel's information in slack workspace. With all details",
        "slack_users_info":get_channels_information()
    }
]

example = """
    {
        "users":[id,id],
        "channels":[id,id]
    }
"""


#event = "Upcoming Project Deadline all   Date 15-6-2025"
#prompt = "Here is the event ."+str(event)+". for this event generate an announcement and publish that to specific person or channel . using the tools : "+str(tools)+" . i already have these function written just need to call function with appropriate parameters.   and here are all information : "+str(information)+"."
#prompt = "Here is the event information ."+str(event)+". for this event generate an announcement using this function "+str(tool1)+". just wirte all the function parameters in json. "


#prompt2 = "Here is the event information ."+str(event)+". based on this event i already generated announcement and i have this function "+str(tool2)+" written to publish that announcement . Now you have to write two list suggesting appropriate channels and users to publish the announcement to them. or keep the list empty if there are no appropriate user or channel. here are slack users and channels information "+str(information)+". i am expecting your response as like as this format : "+example+". So that i can convert it into python dict"
def agdum(event):
    status = True

    if event is None:
        event = "create a demo announcement and send to najim"
    else:
        pass

    

    

    prompt = "Here is the event information ."+str(event)+". for this event generate an announcement using this function "+str(tool1)+". just wirte all the function parameters in json. "

    prompt2 = "Here is the event information ."+str(event)+". based on this event i already generated announcement and i have this function "+str(tool2)+" written to publish that announcement . Now you have to write two list suggesting appropriate channels and users to publish the announcement to them. or keep the list empty if there are no appropriate user or channel. here are slack users and channels information "+str(information)+". i am expecting your response as like as this format : "+example+". So that i can convert it into python dict"

    
    
    answer = llm(prompt)
    #print(answer)
    generator = SlackAnnouncementGenerator()

    # Extract additional requirements content from curly braces
    json_start = answer.find('{')
    json_end = answer.find('}')
    if json_start != -1 and json_end != -1:
        json_content = answer[json_start + 1:json_end].strip()
        print("=====")
        print(type(json_content))
        print("=====")
        try:
            dict = json.loads('{'+json_content+'}')
            print(type(dict))
            typee = dict.get('type',None)
            print(typee)

            title = dict.get('title',None)
            print(title)
            description = dict.get('description',None)
            print(description)
            date = dict.get('date',None)
            print(date)
            impact = dict.get('impact',None)
            print(impact)
            next_steps = dict.get('next_steps',None)
            print(next_steps)
            additional_info = dict.get('additional_info',None)
            print(additional_info)
            '''
            feature_announcement = generator.generate_announcement(
                type=typee,
                title=title,
                description=description,
                date=date,
                impact=impact,
                next_steps=next_steps,
                additional_info=additional_info
            )
            publish_announcements(feature_announcement,[],[])
            '''
        
            answer2 = llm(prompt2)
            print(answer2)
            json_list_start = answer2.find('{')
            json_list_end = answer2.find('}')
            if json_list_start != -1 and json_list_end != -1:
                json_list_content = answer2[json_list_start + 1:json_list_end].strip()
                print("=====")
                print(json_list_content)
                print("=====")
                dict = json.loads('{'+json_list_content+'}')
                users = dict.get('users',None)
                print(users)
                channels = dict.get('channels',None)
                print(channels)

                feature_announcement = generator.generate_announcement(
                    type=typee,
                    title=title,
                    description=description,
                    date=date,
                    impact=impact,
                    next_steps=next_steps,
                    additional_info=additional_info
                )
                publish_announcements(feature_announcement,users,channels)

                return status

        except:
            status = False
            return status
