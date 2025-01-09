import requests
import json
import hmac
import hashlib
import json
import time
import random
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .openai_llm import llm
from .planner import agent_writer
from .models import APICredentials


# Create your views here.

github_token = ""
def code_reviewer_view(request):

    '''
    repo_owner = "najim1110c"
    repo_name = "agent"
    commit_sha = "66de5f253011481ace6e92dd815663c15b06f531"
    new_message = "fahim"
    extended_description = "Hello world again"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}/comments"
    #url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/commits/{commit_sha}"
    data = {
        "body": f"Suggested commit message: {new_message}\n\nExtended description: {extended_description}"
    }
    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print(response.content)

    #url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"
    url = f"https://api.github.com/repos/najim1110c/agent/pulls/22"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "body": "new_descriptiofromonline"  # This is the PR description
    }

    response = requests.patch(url, json=data, headers=headers)
    '''

    '''
    code_changes = """
    {'sha': '5c8bfb23c46c8ba4b03f5458c5a7702cc1adb548', 'original_message': 'Update hello.py', 'diff': [{'sha': 'ef404f65b4768c38cd45fc92fc18a2a150545bdc', 'filename': 'hello.py', 'status': 'modified', 'additions': 1, 'deletions': 1, 'changes': 2, 'blob_url': 'https://github.com/najim1110c/agent/blob/5c8bfb23c46c8ba4b03f5458c5a7702cc1adb548/hello.py', 'raw_url': 'https://github.com/najim1110c/agent/raw/5c8bfb23c46c8ba4b03f5458c5a7702cc1adb548/hello.py', 'contents_url': 'https://api.github.com/repos/najim1110c/agent/contents/hello.py?ref=5c8bfb23c46c8ba4b03f5458c5a7702cc1adb548', 'patch': '@@ -1 +1 @@\n-print("najim")\n+print("hello najim")'}], 'stats': {'total': 2, 'additions': 1, 'deletions': 1}}
    """
    prompt = """
        Here is the diff of a Commit :"""+code_changes+"""\n
        Write a Commit message for this commit with best practice and wrapped in <commit_message> </commit_message> tags.
        Must return a Commit message wrapped in <commit_message> </commit_message> tags.
    """
    response = claude_llm(prompt)

    commit_message = parse_between_tags(response, start_tag="<commit_message>", end_tag="</commit_message>")
    print("commit_message")
    print(commit_message)
    '''


    return JsonResponse({"agent": "code_reviewer"})




def generate_id():
    # Get timestamp in hex with one decimal place for tenths of a second
    timestamp = hex(int(time.time() * 10))[2:]  # Multiply by 10 to include tenths
    # Add random numbers and slice to 8 chars
    random_part = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    return (random_part + timestamp)[:8]

def parse_between_tags(text, start_tag="<start>", end_tag="</end>"):
    """
    Parse text between specified start and end tags. If the text between tags
    is less than 10 characters, continue searching for the next pair of tags.

    Args:
        text (str): Input text containing the tags
        start_tag (str): Opening tag to search for (default: "<start>")
        end_tag (str): Closing tag to search for (default: "</end>")

    Returns:
        str: Text between the tags that meets the length requirement, or None if no valid text is found
    """
    current_pos = 0

    while current_pos < len(text):
        try:
            # Find the starting position after the start tag
            start_pos = text.index(start_tag, current_pos) + len(start_tag)
            # Find the ending position before the end tag
            end_pos = text.index(end_tag, start_pos)
            # Get the text between the tags
            result = text[start_pos:end_pos].strip()

            # If the text is long enough, return it
            if len(result) >=5:
                return result

            # If text is too short, continue searching from the end of current end tag
            current_pos = end_pos + len(end_tag)

        except ValueError:
            return None

    # If we've searched the entire string and found no valid text
    return None


@csrf_exempt
@require_POST  # Only allow POST requests
def github_webhook(request,variable):
    # Verify GitHub webhook signature
    print("najim again")
    print(variable)
    specific_object = APICredentials.objects.filter(unique_value=variable).first()
    print(specific_object.username)
    print(specific_object.secret_key)
    print(specific_object.github_api)

    #print(request.body)
    result = agent_writer(request,specific_object.github_api,specific_object.secret_key)
    return HttpResponse('OK')


@login_required
def github_keys_form(request):
    unique_value = generate_id()
    # Create a new record
    '''
    new_credentials = APICredentials.objects.create(
        unique_value=unique_value,
        username=request.user.username,
        secret_key='your_secret_key',
        github_api='github_token_here'
    )
    '''
    #new_credentials.save()
    specific_object = APICredentials.objects.filter(unique_value='350340ad').first()
    print(specific_object.username)
    print(specific_object.secret_key)
    print(specific_object.github_api)
    return render(request, 'code_reviewer/github_keys.html')


@csrf_exempt
@login_required
def submit_keys(request):
    if request.method == 'POST':
        unique_value =generate_id()
        username=request.user.username
        github_api = request.POST.get('api_key')
        secret_key = request.POST.get('secret_key')
        print(unique_value)
        print(username)
        print(github_api)
        print(secret_key)
        try:
            new_credentials = APICredentials.objects.create(
                unique_value=unique_value,
                username=username,
                secret_key=secret_key,
                github_api=github_api
            )
            new_credentials.save()
            saved_record = APICredentials.objects.filter(pk=new_credentials.pk).exists()
            if saved_record:
                print("Record saved successfully")
                url = 'https://dd8b-103-158-2-21.ngrok-free.app/github_webhook/'+unique_value+'/'
                context = {
                    "payload_url":url,
                    "secret":secret_key,
                    "content_type":"application/json"
                }
                return render(request, 'code_reviewer/success_page.html',context)
            else:
                return redirect('github_keys_form')

        except:
            return redirect('github_keys_form')

    return redirect('github_keys_form')



def success_view(request):
    return render(request, 'code_reviewer/success_page.html')
