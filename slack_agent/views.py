from django.shortcuts import render, redirect
from django.http import JsonResponse
import ssl
import certifi
from django.views.decorators.csrf import csrf_exempt  # Only for testing! Not recommended for production
import os
from .agent_slack import SlackAgent,SlackTools
from django.contrib.auth.decorators import login_required
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .announcement_generator import SlackAnnouncementGenerator
from .models import SlackToken
# Initialize client with bot token
ssl_context = ssl.create_default_context(cafile=certifi.where())


def test(request):

    slack_token = os.getenv('SLACK_TOKEN')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    #tool =SlackTools(slack_token)
    #print(tool.get_users_information())
        
    # Example usage
    #najims user id U082C5XMQTW
    agent = SlackAgent(slack_token=slack_token, openai_api_key=openai_api_key)
    response = agent.process_request("Send a message to only najim about the server maintenance tomorrow.")
    #print(slack_token)
    


    
    
    return JsonResponse({'agdum':"answer"})



@csrf_exempt
@login_required
def add_slack_token(request):
    print("happended")
    if request.method == 'POST':
        print("najim")
        
        username=request.user.username
        slack_token = request.POST.get('slack_token')
        print(username)
        print(slack_token)


        try:
            # Try to get existing token for the user
            existing_token = SlackToken.objects.filter(username=username).first()
            
            if existing_token:
                # Update existing token
                existing_token.token = slack_token
                existing_token.save()
                return render(request, 'slack/token_updated.html')  # Success update page
            else:
                # Create new token if doesn't exist
                new_token = SlackToken.objects.create(
                    username=username,
                    token=slack_token,
                )
                return render(request, 'slack/token_added.html')

        except Exception as e:
            #messages.error(request, f'Error saving token: {str(e)}')
            return render(request, 'slack/api_setter.html')

    return render(request, 'slack/api_setter.html')
    
    
    


