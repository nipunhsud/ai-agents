import requests
import hmac
import hashlib
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .openai_llm import llm

# Create your views here.


github_token = ""





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



def agent_writer(request,token,secret):
    # Verify GitHub webhook signature
    global github_token
    github_token = token
    try:
        
        signature = request.headers.get('X-Hub-Signature-256')
        body = request.body
        #print(body)

        # Calculate expected signature
        hmac_obj = hmac.new(secret.encode('utf-8'), body, hashlib.sha256)
        expected_signature = f"sha256={hmac_obj.hexdigest()}"

        if not hmac.compare_digest(signature, expected_signature):
            return HttpResponse('Invalid signature', status=401)

        # Parse the JSON payload
        event = request.headers.get('X-GitHub-Event')
        data = json.loads(request.body)

        # Handle pull request events
        if event == 'pull_request':
            action = data['action']
            pr = data['pull_request']

            if action == 'opened':
                # Handle new PR
                print("event")
                print(event)
                print("pr")
                print(pr)
                result = get_commit_details(pr,github_token)
                print("result")
                print(result)
                review = generate_code_review(result,pr)
                print("review")
                print(review)
                pass
            elif action == 'synchronize':
                # Handle new commits

                pass
    except Exception as e:
        print(f"Caught error: {e}")
        return False

    return True




def get_commit_details(pull_request_data, github_token):
    commits_url = pull_request_data['commits_url']
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get all commits in the PR
    commits_response = requests.get(commits_url, headers=headers)
    commits = commits_response.json()

    commit_analyses = []
    for commit in commits:
        # Get the diff for this commit
        commit_sha = commit['sha']
        diff_url = f"{pull_request_data['base']['repo']['url']}/commits/{commit_sha}"
        diff_response = requests.get(diff_url, headers=headers)
        diff_data = diff_response.json()

        commit_analyses.append({
            'sha': commit_sha,
            'original_message': commit['commit']['message'],
            'diff': diff_data['files'],
            'stats': diff_data['stats']
        })
    commit_analyses.reverse()
    return commit_analyses



def analyze_commit(commit_data,pr):
    print("analyze_commit")
    print("commit_data")
    print(commit_data)
    changes = []
    code_changes = []

    sha = commit_data['sha']

    for file in commit_data['diff']:
        file_path = file['filename']
        #sha = file['sha']
        patch = file.get('patch', '')

        # Store basic file change info
        if file['status'] == 'added':
            changes.append(f"Added new file: {file_path}")
        elif file['status'] == 'modified':
            changes.append(f"Modified: {file_path}")
        elif file['status'] == 'removed':
            changes.append(f"Removed: {file_path}")

        # Analyze the patch content
        if patch:
            lines = patch.split('\n')
            for line in lines:
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line
                    code_changes.append({
                        'type': 'addition',
                        'content': line[1:],  # Remove the '+' prefix
                        'file': file_path
                    })
                elif line.startswith('-') and not line.startswith('---'):
                    # Removed line
                    code_changes.append({
                        'type': 'deletion',
                        'content': line[1:],  # Remove the '-' prefix
                        'file': file_path
                    })



    print("sha")
    print(sha)
    print("changes")
    print(changes)
    print("code_changes")
    print(code_changes)

    repo_owner = pr['head']['repo']['owner']['login']
    repo_name = pr['head']['repo']['name']
    branch_name = pr["head"]["ref"]


    # Generate commit name based on actual changes
    new_message = generate_commit_name(changes, code_changes)


    # Generate detailed description including the actual changes
    extended_description = generate_commit_description(changes, code_changes)

    #response_value = update_commit_message(sha, new_message, extended_description, pr, github_token)

    response_value = update_specific_commit_message(repo_owner, repo_name, sha, new_message, extended_description, github_token,branch_name)
    print("response_value")
    print(response_value)



    return {
        'suggested_name': new_message,
        'detailed_description': extended_description,
        'changes': changes,
        'code_changes': code_changes
    }




def generate_code_review(commit_analyses,pr):
    print("generate_code_review")
    total_changes = {
        'files_changed': 0,
        'additions': 0,
        'deletions': 0
    }

    review_sections = []

    # Analyze each commit
    for commit in commit_analyses:
        stats = commit['stats']
        total_changes['files_changed'] += stats['total']
        total_changes['additions'] += stats['additions']
        total_changes['deletions'] += stats['deletions']

        analysis = analyze_commit(commit,pr)
        review_sections.append(analysis)
        print("analysis")
        print(analysis)

    repo_owner = pr['head']['repo']['owner']['login']
    repo_name = pr['head']['repo']['name']
    pull_number=pr["number"]
    new_description = generate_pull_request_description(review_sections)
    new_title = generate_pull_request_title(review_sections)
    update_pr_description(new_title,repo_owner, repo_name, pull_number, new_description, github_token)
    return "review"



def update_commit_message(commit_sha, new_message, extended_description, pull_request_data, github_token):
    print("update_commit_message")
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    repo_owner = pull_request_data['head']['repo']['owner']['login']
    repo_name = pull_request_data['head']['repo']['name']
    pr_number = pull_request_data['number']  # Get PR number

    print(repo_owner)
    print(repo_name)
    print(pr_number)
    print(commit_sha)

    # GitHub API endpoint for updating a commit
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}/comments"

    data = {
        "body": f"Suggested commit message: {new_message}\n\nExtended description: {extended_description}"
    }

    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    print("URL:", url)
    print("Data:", data)
    return response.status_code == 201




def generate_commit_name(changes, code_changes):
    print("generate_commit_name")

    commit_message = "feat(hello.py): Update greeting message"

    prompt = """
        Here is the diff of a Commit :"""+str(code_changes)+"""\n
        Write a Commit message for this commit with best practice and wrapped in <commit_message> </commit_message> tags.
        Must return a Commit message wrapped in <commit_message> </commit_message> tags.
    """

    prompt = """You are a code review assistant following strict commit message guidelines. Review the following code changes and generate a conventional commit message.

        Guidelines:
        - Format: <type>: <description>
        - Types: feat, fix, refactor, style, docs, test, chore, perf
        - Use imperative present tense ("Add" not "Added")
        - Description should be capitalized
        - No scope is needed
        - Keep it concise (50 chars or less)

        Code changes:
        """+str(code_changes)+"""\n

        Return a single line commit message wrapped in <commit_message> </commit_message> tags.

        Example good messages:
        feat: Add user authentication system
        fix: Resolve database connection timeout
        refactor: Simplify payment processing logic
    """
    response = llm(prompt)

    commit_message = parse_between_tags(response, start_tag="<commit_message>", end_tag="</commit_message>")
    print("commit_message")
    print(commit_message)

    return commit_message



def generate_commit_description(changes, code_changes):

    extended_description = "fahim"

    prompt = """
        Here is the diff of a Commit :"""+str(code_changes)+"""\n
        Write extended description for that commit with best practice and wrapped in <description> </description> tags.
        Must return a extended description wrapped in <description> </description> tags.
    """

    prompt = """You are a code review assistant. Generate a detailed commit description for the following code changes.

        Guidelines:
        - Explain the "what" and "why" of changes
        - Be specific about implementation details
        - List any breaking changes
        - Keep paragraphs short and focused

        Code changes:
        """+str(code_changes)+"""\n

        Return the description wrapped in <description> </description> tags.
        Include formatting like:
        - What changed
        - Why it was changed
        - How it affects other parts of the system
    """

    response = llm(prompt)

    extended_description = parse_between_tags(response, start_tag="<description>", end_tag="</description>")
    return extended_description



def generate_pull_request_description(review_sections):

    prompt = """
        Here are all the commits information of a pull request :"""+str(review_sections)+"""\n
        Write description for that pull request and wrapped in <description> </description> tags.
        Must return a description wrapped in <description> </description> tags.
    """
    response = llm(prompt)

    new_description = parse_between_tags(response, start_tag="<description>", end_tag="</description>")
    return new_description



def generate_pull_request_title(review_sections):

    prompt = """
        Here are all the commits information of a pull request :"""+str(review_sections)+"""\n
        Write Title for that pull request with best practice and wrapped in <title> </title> tags.
        Must return a description wrapped in <title> </title> tags.
    """
    response = llm(prompt)

    new_title = parse_between_tags(response, start_tag="<title>", end_tag="</title>")
    return new_title




def update_specific_commit_message(repo_owner, repo_name, target_commit_sha, new_title, new_description, github_token,branch_name):
    print("update_specific_commit_message")
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get the target commit's info
    commit_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{target_commit_sha}"
    commit_response = requests.get(commit_url, headers=headers)
    commit_data = commit_response.json()

    # Get parent of target commit
    parent_sha = commit_data['parents'][0]['sha']  # First parent
    tree_sha = commit_data['commit']['tree']['sha']

    # 2. Create new commit with updated message
    create_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/commits"
    new_message = f"{new_title}\n\n{new_description}"  # Combine title and extended description

    commit_data = {
        "message": new_message,
        "tree": tree_sha,
        "parents": [parent_sha]  # Use parent of target commit
    }

    create_response = requests.post(create_url, json=commit_data, headers=headers)
    print("Status Code:", create_response.status_code)
    print("Response:", create_response.json())
    print("URL:", create_url)
    print("Data:", commit_data)


    if create_response.status_code == 201:
        new_commit_sha = create_response.json()['sha']

        # 3. Update all subsequent commits to use new commit as their parent
        # First get all commits after target commit
        branch_name = branch_name  # Get this from PR info
        branch_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?sha={branch_name}"
        branch_commits = requests.get(branch_url, headers=headers).json()

        # Find position of target commit and get all later commits
        target_index = next(i for i, commit in enumerate(branch_commits) if commit['sha'] == target_commit_sha)
        later_commits = branch_commits[:target_index]  # Commits are in reverse chronological order

        # Recreate each subsequent commit with updated parent
        current_parent = new_commit_sha
        for commit in reversed(later_commits):
            commit_info = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit['sha']}", headers=headers).json()

            new_commit_data = {
                "message": commit_info['commit']['message'],
                "tree": commit_info['commit']['tree']['sha'],
                "parents": [current_parent]
            }

            response = requests.post(create_url, json=new_commit_data, headers=headers)
            if response.status_code == 201:
                current_parent = response.json()['sha']
            else:
                raise Exception("Failed to recreate commit chain")

        # 4. Update branch reference to point to final new commit
        ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch_name}"
        ref_data = {
            "sha": current_parent,
            "force": True
        }

        return requests.patch(ref_url, json=ref_data, headers=headers)



def update_pr_description(new_title,repo_owner, repo_name, pull_number, new_description, github_token):

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "body": new_description,  # This is the PR description
        "title":new_title
    }

    response = requests.patch(url, json=data, headers=headers)
    return response.status_code == 201









'''
#generate_pull_request_title------------------------
prompt = """You are a code review assistant. Generate a PR title based on the following commit information.

Guidelines:
- Format: Type: Brief description
- Types match commit types (Feature, Fix, Refactor, etc.)
- Be clear and concise
- Capitalize first word
- No period at the end

Commit information:
{review_sections}

Return the PR title wrapped in <title> </title> tags.

Example good titles:
Feature: Add chess timer component
Fix: Resolve authentication timeout issues
Refactor: Simplify payment processing flow
"""

#generate_pull_request_description----------------------
prompt = """You are a code review assistant. Generate a PR description based on the following commit information.

Follow this template structure:
## Description
Brief description of the changes

## Type of Commits Covered in PR
- [ ] Feature: New feature
- [ ] Fix: Bug fix
- [ ] Refactor: Code change that neither fixes a bug nor adds a feature
- [ ] Style: Changes that don't affect code meaning
- [ ] Documentation: Documentation only changes
- [ ] Test: Adding missing tests
- [ ] Chore: Changes to build process
- [ ] Performance: Performance improvements

## Testing Done
- List test cases covered

## Screenshots/Videos
Add relevant media (if applicable)

Commit information:
{review_sections}

Return the formatted description wrapped in <description> </description> tags.
"""



#generate_commit_description--------------------------------------
prompt = """You are a code review assistant. Generate a detailed commit description for the following code changes.

Guidelines:
- Explain the "what" and "why" of changes
- Be specific about implementation details
- List any breaking changes
- Include testing done if applicable
- Keep paragraphs short and focused

Code changes:
{code_changes}

Return the description wrapped in <description> </description> tags.
Include formatting like:
- What changed
- Why it was changed
- How it affects other parts of the system
- Testing considerations
"""



#generate_commit_name----------------------------------------------
prompt = """You are a code review assistant following strict commit message guidelines. Review the following code changes and generate a conventional commit message.

Guidelines:
- Format: <type>: <description>
- Types: feat, fix, refactor, style, docs, test, chore, perf
- Use imperative present tense ("Add" not "Added")
- Description should be capitalized
- No scope is needed
- Keep it concise (50 chars or less)

Code changes:
{code_changes}

Return a single line commit message wrapped in <commit_message> </commit_message> tags.

Example good messages:
feat: Add user authentication system
fix: Resolve database connection timeout
refactor: Simplify payment processing logic
"""




'''