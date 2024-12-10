from django.shortcuts import render
from django.http import JsonResponse

from slack_agent.openai_llm import llm
import json
import ssl
import certifi




from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .announcement_generator import SlackAnnouncementGenerator
from .planner import get_channels_information,agdum

# Initialize client with bot token
#client = WebClient(token="xapp-1-A083ANP1W90-8135576493568-70c6c216693ac25b54574943f7ce09aece6becaf41eb2f05707d901f4df7dcc2")
ssl_context = ssl.create_default_context(cafile=certifi.where())

client = WebClient(
    token='xoxb-8032017402916-8106281877078-CWv8lJ0WhgGMC3dndfP4o6rS',
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

    '''
    users = client.users_list()
    for user in users["members"]:
        #print(f"Username: {user['name']}, ID: {user['id']}")
        title = user.get('profile', {}).get('title', 'No title set')
        print(f"Username: {user['name']}, ID: {user['id']}, Title: {title}")

    '''
    

    agdum()

    
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            print(message)

            status = agdum(message)

            if status :
                return render(request, 'slack/success.html')
            else:
                return render(request, 'slack/failed.html')


            
            # Do something with the message here
            # For example, save to database
            
            return render(request, 'slack/success.html')
        except json.JSONDecodeError:
            return render(request, 'slack/failed.html')
        
    else:

        return render(request, 'slack/slack.html')



