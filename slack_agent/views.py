from django.shortcuts import render
from django.http import JsonResponse

from slack_agent.openai_llm import llm
import json
import ssl
import certifi

import os


from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .announcement_generator import SlackAnnouncementGenerator
from .planner import get_channels_information,agdum,get_users_information,publish_announcements

# Initialize client with bot token
#client = WebClient(token="xapp-1-A083ANP1W90-8135576493568-70c6c216693ac25b54574943f7ce09aece6becaf41eb2f05707d901f4df7dcc2")
ssl_context = ssl.create_default_context(cafile=certifi.where())
slack_token =  os.getenv('SLACK_TOKEN')
client = WebClient(
    #token='xoxb-8032017402916-8106281877078-l0ixOdLfA8MMZeHjsO1fJlHR',
    token = slack_token,
    ssl=ssl_context
)



'''
def test(request):

    #question = "what is your name? what model are your ? "
    #answer = llm(question)
    #print(answer)


    try:
        response = client.chat_postMessage(
            #channel="#general",
            channel="U080SKD43D3",
            text="Let me know if you receive any notification 👋"
        )
        print(f"Message sent: {response['ts']}")
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

    return JsonResponse({'agdum':"answer"})



'''
def test(request):

    
    users = client.users_list()
    for user in users["members"]:
        #print(f"Username: {user['name']}, ID: {user['id']}")
        title = user.get('profile', {}).get('title', 'No title set')
        print(f"Username: {user['name']}, ID: {user['id']}, Title: {title}")


    channels = client.conversations_list(
        types="public_channel,private_channel"  # You can also add "mpim,im" for group/direct messages
    )

    for channel in channels:
        print(channel)


    #agdum()

    
    '''
    generator = SlackAnnouncementGenerator()
    
    # Example feature announcement
    feature_announcement = generator.generate_announcement(
        type='feature',
        title='Dark Mode',
        description='Were introducing Dark Mode across all our applications!',
        date='2024-12-15',
        impact='This update will improve user experience of our app in low-light conditions and reduce eye strain.',
        next_steps=[
            'Update your app to the latest version',
            'Access settings to toggle Dark Mode',
            'Share feedback in #product-feedback channel'
        ]
    )

    #print(feature_announcement)
    text = str(feature_announcement)

    #print(feature_announcement['blocks'])
    title_text = feature_announcement['blocks'][0]['text']['text']
    print(title_text)
    try:
        response = client.chat_postMessage(
            #channel="#general",
            channel="U082C5XMQTW",
            #text=text
            blocks=feature_announcement['blocks'],  # Send the blocks directly
            text=title_text  # Fallback text for notifications
        )
        print(f"Message sent: {response['ts']}")
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

    

    '''
    return JsonResponse({'agdum':"answer"})




from django.views.decorators.csrf import csrf_exempt  # Only for testing! Not recommended for production

@csrf_exempt  # Only for testing! Remove in production and properly handle CSRF
def handle_message(request):
    print("last time")
    print(request)
    print(request.method)
    print(request.body)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
        except:
            data = False
        
        #if data.get('message'):
        if data:
            try:
                data = json.loads(request.body)
                print(data)
                message = data.get('message')
                print(message)
                
                feature_announcement,users,channels = agdum(message)
                print("this is from view")
                print(feature_announcement)
                print(users)
                print(channels)
                if not feature_announcement:
                    return render(request, 'slack/failed.html')
                status = True

                all_users = get_users_information()  # Your function to get all users
                all_channels = get_channels_information()  #
                
                type_value = feature_announcement["ty"]
                title_value = feature_announcement["title"]
                description_value = feature_announcement["description"]
                date_value = feature_announcement["date"]
                impact_value = feature_announcement["impact"]
                next_steps_value = feature_announcement["next_steps"]
                additional_info_value = feature_announcement["additional_info"]
                
                announcement_data = {
                    'type': type_value,  # Type will be determined by emoji in header
                    'title': title_value,
                    'description': description_value,
                    'date': date_value,
                    'impact': impact_value,
                    'next_steps': next_steps_value ,
                    'additional_info': additional_info_value,
                }

                # If confirm flag is in the POST data, it means form was submitted from confirmation page
                if data.get('confirm'):
                    status = True  # Your existing logic
                    if status:
                        return render(request, 'slack/success.html')
                    else:
                        return render(request, 'slack/failed.html')
                else:
                    
                    # Add console log to see what's being passed
                    print("Data being sent to template:", {
                        'announcement': announcement_data,
                        'users': users,
                        'channels': channels,
                        'all_users': all_users,  # All available users
                        'all_channels': all_channels  # All available channels
                    })

                    return render(request, 'slack/confirm.html', {
                        'announcement': announcement_data,
                        'users': users,
                        'channels': channels,
                        'all_users': all_users,  # All available users
                        'all_channels': all_channels  # All available channels
                    })
                
            except json.JSONDecodeError:
                return render(request, 'slack/failed.html')
        
        else:
            print("hello india")
            try:
                # Get all the form data
                print("Processing form submission")
                # Get form data
                type_value = request.POST.get('type')
                title_value = request.POST.get('title')
                description_value = request.POST.get('description')
                date_value = request.POST.get('date')
                impact_value = request.POST.get('impact')
                next_steps_value = request.POST.getlist('next_steps')  # Use getlist for multiple values
                additional_info_value = request.POST.get('additional_info')
                selected_channels = request.POST.getlist('channels')  # Use getlist for multiple values
                selected_users = request.POST.getlist('users')  # Use getlist for multiple values
                # Create announcement data structure
                feature_announcement = {
                    "type": type_value,
                    "title": title_value,
                    "description": description_value,
                    "date": date_value,
                    "impact": impact_value,
                    "next_steps": next_steps_value,
                    "additional_info": additional_info_value
                }
                print("final check")
                print(feature_announcement)
                print(selected_users)
                print(selected_channels)

                # Generate blocks for Slack using your generator
                
                generator = SlackAnnouncementGenerator()
                slack_message = generator.generate_announcement(
                    type=type_value,
                    title=title_value,
                    description=description_value,
                    date=date_value,
                    impact=impact_value,
                    next_steps=next_steps_value,
                    additional_info=additional_info_value
                )
                

                # Send to Slack using your publish_announcements function
                status = publish_announcements(slack_message, selected_users, selected_channels)

                if status :
                    return render(request, 'slack/success.html')
                else:
                    return render(request, 'slack/failed.html')
            except:
                return render(request, 'slack/failed.html')
        
    else:

        return render(request, 'slack/slack.html')
    


