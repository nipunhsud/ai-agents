import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from groq import Groq
from .openai_llm import llm
import os



api_key = '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'

def check_groq_api_key(question):
    client = Groq(api_key=api_key)
    try:
        # Make a simple API call
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model="llama3-70b-8192",
        )

        return chat_completion.choices[0].message.content
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if "Invalid authentication credentials" in str(e):
            print("Groq API key is invalid or has been revoked.")
        elif "model_not_found" in str(e):
            print("The specified model is not available. Please check available models in your Groq account.")
        return False


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
# Create your views here.

def test_help_desk_agent_view(request):
    print("test_help_desk_agent_view")
    question = "what is your name ?"
    answer = llm(question)
    print(answer)

    return JsonResponse({'agdum':answer})




def help_desk(request):
    print("test_help_desk_agent_view")

    
    context = {
        'json_data': 'lklk'
    }
    return render(request, 'help_desk/get_help.html', context)



@csrf_exempt
@require_POST  #Only allow POST requests
def help_desk_receive(request):
    print("help_desk_receive")
    data = json.loads(request.body)
    text = data.get('text')
    timestamp = data.get('timestamp')
    reason = data.get('reason')
    language = data.get('language')
    #answer = llm(text)
    answer = help_desk_agent(text)
    print(answer)

    print(f"Received: text={text}, timestamp={timestamp}, reason={reason}, language={language}")


    return JsonResponse({'agdum':answer})



def help_desk_agent(user_query):
    '''
    prompt = """
        You are a help desk agent . You can only answer to user question if the question is based on the the information.
        if the question is not related tell the user that you dont have information to answer that question .
        Here is user's question: <question> """+str(user_query)+""" 
        <information>
            - doctor shamsunnahar is in room 308.
            - doctor shafikul only in chember at tuesday . 
        </information>
        write all your answer in bangla language wrapped in <answer> </answer> tags .
    """
    '''

    prompt = """You are a professional help desk agent at a medical facility. Your responses should be based strictly on the following information. If a question falls outside this scope, politely inform the user that you don't have the relevant information to answer their query.

    Available Information:
    Doctor Schedules and Locations:
    1. Dr. Shamsunnahar Rahman (Cardiologist)
    - Room: 308
    - Available: Monday to Thursday, 9 AM - 3 PM
    - Evening sessions: Tuesday and Wednesday, 5 PM - 8 PM

    2. Dr. Shafikul Islam (Orthopedic)
    - Room: 205
    - Available: Only on Tuesdays and Thursdays
    - Hours: 10 AM - 4 PM

    3. Dr. Tahmina Akter (Pediatrician)
    - Room: 401
    - Available: Monday, Wednesday, Friday
    - Hours: 8 AM - 2 PM
    - Emergency consultant on weekends

    4. Dr. Rashid Khan (Neurologist)
    - Room: 512
    - Available: Monday to Friday
    - Hours: 11 AM - 5 PM
    - Special appointments only on Saturdays

    5. Dr. Nasreen Jahan (Gynecologist)
    - Room: 303
    - Available: Sunday to Thursday
    - Hours: 10 AM - 3 PM
    - Women's clinic: Friday mornings

    6. Dr. Abdul Karim (Dentist)
    - Room: 102
    - Available: All days except Friday
    - Hours: 9 AM - 4 PM

    7. Dr. Fatima Begum (Dermatologist)
    - Room: 207
    - Available: Sunday, Tuesday, Thursday
    - Hours: 2 PM - 8 PM

    8. Dr. Mahbub Alam (Psychiatrist)
    - Room: 601
    - Available: By appointment only
    - Hours: Monday to Thursday, 10 AM - 6 PM

    9. Dr. Sultana Razia (ENT Specialist)
    - Room: 405
    - Available: Monday, Wednesday, Thursday
    - Hours: 11 AM - 7 PM

    10. Dr. Kamrul Hasan (Pulmonologist)
        - Room: 309
        - Available: Sunday to Wednesday
        - Hours: 9:30 AM - 3:30 PM

    11. Dr. Nusrat Jahan (Endocrinologist)
        - Room: 404
        - Available: Tuesday to Saturday
        - Hours: 10 AM - 4 PM
        - Diabetes clinic: Thursday afternoons

    12. Dr. Zahir Uddin (Urologist)
        - Room: 503
        - Available: Monday, Tuesday, Thursday
        - Hours: 11 AM - 5 PM

    13. Dr. Rubina Akter (Nutritionist)
        - Room: 201
        - Available: All days
        - Hours: 9 AM - 3 PM
        - Diet counseling: Afternoon sessions

    14. Dr. Masud Parvez (Ophthalmologist)
        - Room: 306
        - Available: Sunday to Thursday
        - Hours: 10 AM - 6 PM

    15. Dr. Shabnam Hassan (Rheumatologist)
        - Room: 408
        - Available: Monday, Wednesday, Friday
        - Hours: 9 AM - 3 PM

    16. Dr. Imran Ahmed (General Physician)
        - Room: 101
        - Available: All days
        - Hours: 8 AM - 8 PM
        - Emergency duty doctor

    17. Dr. Laila Khatun (Pediatric Surgeon)
        - Room: 502
        - Available: Sunday, Tuesday, Thursday
        - Hours: 10 AM - 4 PM

    18. Dr. Mahmud Hassan (Physiotherapist)
        - Room: 203
        - Available: All days except Sunday
        - Hours: 8 AM - 2 PM

    19. Dr. Dilara Zaman (Diabetologist)
        - Room: 307
        - Available: Monday to Friday
        - Hours: 11 AM - 5 PM
        - Special diabetes care: Wednesday

    20. Dr. Kamal Uddin (Gastroenterologist)
        - Room: 406
        - Available: Sunday, Monday, Wednesday, Thursday
        - Hours: 10 AM - 4 PM

    User Question: """+str(user_query)+"""

    Requirements:
    1. Please respond in the same language that the user uses to ask their question.
    2. Wrap your response in <answer> tags
    3. Be polite and professional in your responses
    4. For out-of-scope questions, explain that you can only provide information about doctors' locations and schedules

    Response Format:
    <answer>
    [Please respond in the same language that the user uses to ask their question.]
    </answer>"""
    response = check_groq_api_key(prompt)

    answer = parse_between_tags(response,start_tag="<answer>", end_tag="</answer>")
    return answer