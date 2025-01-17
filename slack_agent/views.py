from django.shortcuts import render, redirect
from django.http import JsonResponse
import ssl
import certifi
from django.views.decorators.csrf import csrf_exempt  # Only for testing! Not recommended for production
import os
from .agent_slack import SlackAgent,SlackTools,SlackAgentTool
from django.contrib.auth.decorators import login_required
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .announcement_generator import SlackAnnouncementGenerator
from .models import SlackToken
import json
from django.utils.safestring import mark_safe

# Initialize client with bot token
ssl_context = ssl.create_default_context(cafile=certifi.where())

@login_required
def test(request):

    #slack_token = os.getenv('SLACK_TOKEN')
    slack_token = SlackToken.objects.filter(username=request.user.username).first().token
    print(slack_token)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    #najims user id U082C5XMQTW
    #agent = SlackAgentTool(slack_token=slack_token, openai_api_key=openai_api_key)
    #response = agent.process_request("Send a message to only najim about the server maintenance tomorrow.")
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
    
    
    

@csrf_exempt  # Only for testing! Remove in production and properly handle CSRF
@login_required
def handle_message(request):
    #print(request)
    #print(request.method)
    #print(request.body)
    if request.method == 'POST':
        print("najim")
        data = request.POST.get('message')
        print(data)
        '''
        try:
            data = json.loads(request.body)
            print(data)
        except:
            data = False
        '''
        
        if data:
            try:    
                query = data
                
                # Get user's Slack token
                slack_token = SlackToken.objects.filter(username=request.user.username).first()
                if not slack_token:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No Slack token found. Please add your Slack token first.'
                    })
                
                # Initialize agent
                agent = SlackAgent(
                    slack_token=slack_token.token,
                    openai_api_key=os.getenv('OPENAI_API_KEY')
                )
                
                # Generate previews
                agent.previewed_messages = []  # Clear previous previews
                agent.agent.run([
                    {"role": "system", "content": agent.system_message},
                    {"role": "user", "content": query}
                ])
                
                print(agent.previewed_messages)
                print(type(agent.previewed_messages))
                return render(request, 'slack/message_preview.html', {
                    "messages": mark_safe(json.dumps(agent.previewed_messages,ensure_ascii=False)),#agent.previewed_messages,
                    "users_info": agent.users_info,
                    "channels_info": agent.channels_info
                })
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        return render(request, 'slack/slack.html')
    else:
        return render(request, 'slack/slack.html')
    



@csrf_exempt  # Remove in production and handle CSRF properly
@login_required
def send_messages(request):
    """Send edited messages"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            messages = data.get('messages', [])
            
            # Get user's Slack token
            slack_token = SlackToken.objects.filter(username=request.user.username).first()
            if not slack_token:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No Slack token found. Please add your Slack token first.'
                })
            
            # Initialize agent
            agent = SlackAgent(
                slack_token=slack_token.token,
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
            
            # Send messages
            print("message sent")
            results = []
            for msg in messages:
                if msg['type'] == 'simple_message':
                    result = agent.slack_tools.send_message(
                        message=msg['content'],
                        users=msg['recipients']['users'],
                        channels=msg['recipients']['channels']
                    )
                else:
                    result = agent.slack_tools.send_announcement(
                        type=msg['content']['type'],
                        title=msg['content']['title'],
                        description=msg['content']['description'],
                        users=msg['recipients']['users'],
                        channels=msg['recipients']['channels']
                    )
                results.append(result)
                print(results)
            
            return JsonResponse({
                'status': 'success',
                'results': str(results)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })


def slack_success_view(request):

    return render(request, 'slack/success.html') 