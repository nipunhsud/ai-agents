import json
import logging
import os

from django.views import View
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from langchain.schema import HumanMessage
from langchain.chat_models import ChatOpenAI
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from firebase_admin import firestore
from datetime import datetime, timezone
from firebase_admin import auth
import stripe

from .agent import Agent
from .models import Message
from .models import Document
from .models import Conversation
from .gift_agent import gift_prediction
from .email_assistant import get_emails
from .document_processor import DocumentProcessor
from .technical_writer import TechnicalWriter, DocumentType, OutputFormat
from .assistant import Assistant
#from .email_assistant import email_generator
from .stock_assistant import stock_generator
from .rental_assistant import rental_generator
from .slack import slack_generator
from .decorators import firebase_auth_required

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)


def query_page(request):
    messages = [HumanMessage(content="do you know messi")]
    response = chat(messages)
    response = str(response.content)
    return JsonResponse({'response':response})

@ensure_csrf_cookie
def email_assistant_page(request):
    try:
        return render(request, 'chat/email_writer.html')
    except Exception as e:
        logger.error(f"Error rendering react page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@ensure_csrf_cookie
def fetch_emails(request):
    if request.method == 'GET':
        try:
            emails = get_emails()
            return JsonResponse({'emails': emails}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
    
@ensure_csrf_cookie
def gift_prediction_view(request):
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'age': request.POST.get('age'),
            'relationship': request.POST.get('relationship'),
            'interests': request.POST.get('interests'),
            'brands': request.POST.get('brands'),
            'budget': request.POST.get('budget'),
            'occasion': request.POST.get('occasion'),
            'notes': request.POST.get('notes'),
            'previous_gifts': request.POST.get('previous_gifts'),
            'preferred_site':'ecommerce site'
        }
        print(data)  # For testing, you can see the data in console
        result,json_data = gift_prediction(data)

        #return render(request, 'chat/success.html', {'data': data,'result':result})
        '''
        status = True
        return JsonResponse({
            'success': True,
            'data': {
                'products': json_data,  # List of dictionaries goes here
                'status': status
            },
            'message': 'Products retrieved successfully'
        })
        '''

         # Create the response data structure
        response_data = {
            'success': True,
            'data': {
                'products': json_data,
                'status': True
            },
            'message': 'Products retrieved successfully'
        }
        
        # Render the result.html template with the data
        return render(request, 'chat/result.html', {
            'json_data': json.dumps(response_data)  # Serialize the entire response
        })
    #return render(request, 'gifts/index.html')
    return render(request, 'chat/gift_prediction.html')

@login_required
def upload_page(request):
    logger.debug(f"User {request.user} accessing upload page")
    try:
        return render(request, 'chat/upload.html')
    except Exception as e:
        logger.error(f"Error rendering upload page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

class SlackAssistantView(View):
    def post(self, request):
        user_input = request.POST.get('input', '')

        if not user_input:
            return JsonResponse({'error': 'Input cannot be empty.'}, status=400)

        try:
            result,json_data = slack_generator(user_input)
            print(result)
            print(json_data)
             # Return both the JSON data and markdown result with appropriate content type
            response = JsonResponse({
                'response': json_data, 
                'markdown': result,
                'content_type': 'text/markdown'
            })
            response['Content-Type'] = 'application/json'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# @firebase_auth_required
def react_page(request):
    logger.debug(f"User {request.user} accessing react page")
    try:
        # Access Firebase user info if needed
        # firebase_user = request.firebase_user
        return render(request, 'chat/react.html')
    except Exception as e:
        logger.error(f"Error rendering react page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
def real_estate_page(request):
    logger.debug(f"User {request.user} accessing react page")
    try:
        # Access Firebase user info if needed
        # firebase_user = request.firebase_user
        return render(request, 'chat/real_estate.html')
    except Exception as e:
        logger.error(f"Error rendering react page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def upload_document(request):
    if request.method == 'POST' and request.FILES.get('document'):
        document = request.FILES['document']
        
        # Validate file type
        file_extension = document.name.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_DOCUMENT_TYPES:
            return JsonResponse({
                'error': 'Invalid file type'
            }, status=400)
            
        # Save document
        doc = Document.objects.create(
            user=request.user,
            file=document,
            file_type=file_extension
        )
        
        # Process document
        processor = DocumentProcessor()
        extracted_text, summary = processor.process_document(
            doc.file.path,
            doc.file_type
        )
        
        # Update document with processed text and summary
        doc.processed_text = extracted_text
        doc.summary = summary
        doc.save()
        
        return JsonResponse({
            'message': 'Document processed successfully',
            'document_id': doc.id,
            'summary': summary
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def custom_summary(request, document_id):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        document = Document.objects.get(id=document_id, user=request.user)
        
        processor = DocumentProcessor()
        custom_summary = processor.generate_custom_summary(
            document.processed_text,
            prompt
        )
        
        return JsonResponse({
            'summary': custom_summary
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400) 
    
@login_required
def _extract_text(self, file_path: str, file_type: str) -> str:
        logger.debug(f"Processing file: {file_path} of type: {file_type}")

        if file_type == 'pdf':
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return '\n'.join(page.page_content for page in pages)
        
        elif file_type == 'docx':
            loader = Docx2txtLoader(file_path)
            pages = loader.load()
            return '\n'.join(page.page_content for page in pages)
        
        elif file_type in ['png', 'jpg', 'jpeg']:
            loader = UnstructuredImageLoader(file_path)
            pages = loader.load()
            return '\n'.join(page.page_content for page in pages)
        
        raise ValueError(f"Unsupported file type: {file_type}")

class AgentView(View):
    def post(self, request):
        user_input = request.POST.get('input', '')

        if not user_input:
            return JsonResponse({'error': 'Input cannot be empty.'}, status=400)

        # Instantiate the AIReActAgent
        try:
            agent = Agent()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Run the agent with the user input
        action_response = agent.run(user_input)
    
        # Return the response as JSON
        return JsonResponse({'response': action_response})
        
class UploadView(View):
    def post(self, request):
        try:
            # Get the list of uploaded files
            files = request.FILES.getlist('files')
            prompt = request.POST.get('prompt', '').strip()

            if not files:
                return JsonResponse({'error': 'No files were uploaded.'}, status=400)
            
            if not prompt:
                return JsonResponse({'error': 'Prompt cannot be empty.'}, status=400)

            results = []
            processor = DocumentProcessor()

            for file in files:
                # Get file extension
                file_extension = file.name.split('.')[-1].lower()
                
                # Validate file type
                if file_extension not in settings.ALLOWED_DOCUMENT_TYPES:
                    return JsonResponse({
                        'error': f'Invalid file type: {file_extension}'
                    }, status=400)

                # Save the file and get its path
                doc = Document.objects.create(
                    user=request.user,
                    file=file,
                    file_type=file_extension
                )

                try:
                    # Process document using the saved file path
                    extracted_text, summary = processor.process_document(
                        doc.file.path,
                        file_extension
                    )

                    # Update document with processed text and summary
                    doc.processed_text = extracted_text
                    doc.summary = summary
                    doc.save()

                    # Generate custom response based on prompt
                    custom_response = processor.generate_custom_summary(
                        extracted_text,
                        prompt
                    )

                    results.append({
                        'file_name': file.name,
                        'document_id': doc.id,
                        'summary': summary,
                        'custom_response': custom_response
                    })

                except Exception as e:
                    logger.error(f"Error processing file {file.name}: {str(e)}")
                    doc.delete()  # Clean up if processing failed
                    return JsonResponse({
                        'error': f'Error processing file {file.name}: {str(e)}'
                    }, status=500)

            return JsonResponse({
                'message': 'Files processed successfully!',
                'results': results
            })

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return JsonResponse({
                'error': f'Server error: {str(e)}'
            }, status=500)
        
@csrf_protect
async def technical_writer_view(request):
    if request.method == 'GET':
        logger.info("Received GET request for technical writer view")
        return render(request, 'chat/technical_writer_view.html')
    
    if request.method == 'POST':
        logger.info("Received POST request for document generation")
        try:
            # Log incoming request data
            logger.debug(f"Form data received: {request.POST}")
            
            # Initialize the TechnicalWriter
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables")
                raise ValueError("OpenAI API key not configured")
            
            # Get form data
            content = request.POST.get('content')
            doc_type_str = request.POST.get('doc_type')
            output_format_str = request.POST.get('output_format')
            tone = request.POST.get('tone')
            technical_level = request.POST.get('technical_level')
            
            logger.info(f"Processing request - Content length: {len(content) if content else 0}, "
                       f"Document Type: {doc_type_str}, Output Format: {output_format_str}")
            
            if not content:
                raise ValueError("No content provided")
            
            writer = TechnicalWriter(api_key=api_key)
            
            # Generate document
            logger.info("Starting document generation")
            document = await writer.generate_document(
                content=content,
                doc_type=DocumentType(doc_type_str),
                output_format=OutputFormat(output_format_str),
                tone=tone,
                technical_level=technical_level
            )
            
            logger.info("Document generation completed")
            logger.debug(f"Generated document preview: {str(document)[:200]}...")
            
            if not document:
                raise ValueError("No document content generated")
            
            return JsonResponse({
                'success': True,
                'content': document
            })
            
        except Exception as e:
            logger.error(f"Error during document generation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)  # Added status code for errors
        

class AssistantView(View):
    def post(self, request):
        user_input = request.POST.get('input', '')

        if not user_input:
            return JsonResponse({'error': 'Input cannot be empty.'}, status=400)

        # Instantiate the AIReActAgent
        try:
            assistant = Assistant()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Run the agent with the user input
        assistant.add_message(user_input)
        stream = assistant.run_assistant()
        # Return the response as JSON
        return JsonResponse({'response': "ok"})

@method_decorator(ensure_csrf_cookie, name='dispatch')
class EmailAssistantView(View):
    def get(self, request):
        return render(request, 'chat/email_writer.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            response = email_generator(
                data.get('subject', ''),
                data.get('from', ''),
                data.get('to', ''),
                data.get('original_content', '')
            )
            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@ensure_csrf_cookie
def fetch_emails(request):
    if request.method == 'GET':
        try:
            emails = get_emails()
            return JsonResponse({'emails': emails}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@method_decorator(firebase_auth_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')        
class StockAssistantView(View):
    def post(self, request):
        user_input = request.POST.get('input', '')
        user_id = request.firebase_user['uid']
        
        if not user_input:
            return JsonResponse({'error': 'Input cannot be empty.'}, status=400)
            
        try:
            # Check request count
            db = firestore.client()
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            # Get today's requests for this user
            requests = db.collection('stock_analysis')\
                .where('user_id', '==', user_id)\
                .where('timestamp', '>=', today_start)\
                .get()
                
            if len(requests) >= 10:
                return JsonResponse({
                    'error': 'Daily limit reached',
                    'message': 'You have reached your daily limit of 10 requests. Please subscribe for unlimited access.',
                    'subscribe': True
                }, status=402)

            
            
            # Process request
            result, json_data, price_history = stock_generator(user_input)
            
            # Save to Firestore
            db.collection('stock_analysis').add({
                'user_id': user_id,
                'ticker': user_input,
                'analysis': json_data,
                'markdown': result,
                'timestamp': datetime.now(timezone.utc),
            })
            
            response = JsonResponse({
                'response': json_data, 
                'markdown': result,
                'price_history': price_history,
                'content_type': 'text/markdown',
                'requests_remaining': 10 - (len(requests) + 1)
            })
            response['Content-Type'] = 'application/json'
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(View):
    def get(self, request):
        token = get_token(request)
        response = JsonResponse({'csrfToken': token})
        return response


class RentalAssistantView(View):
    def post(self, request):
        user_input = request.POST.get('input', '')

        if not user_input:
            return JsonResponse({'error': 'Input cannot be empty.'}, status=400)

        try:
            result,json_data = rental_generator(user_input)
        
             # Return both the JSON data and markdown result with appropriate content type
            response = JsonResponse({
                'response': json_data, 
                'markdown': result,
                'content_type': 'text/markdown'
            })
            response['Content-Type'] = 'application/json'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def quant_analyst_page(request):
    logger.debug(f"User {request.user} accessing react page")
    try:
        return render(request, 'chat/quant_analyst.html')
    except Exception as e:
        logger.error(f"Error rendering react page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def email_assistant_view(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Extract email information
            email_id = data.get('email_id', '')
            subject = data.get('subject', '')
            from_email = data.get('from', '')
            original_content = data.get('original_content', '')
            to_email = data.get('to', '')

            
            if not original_content:
                return JsonResponse({'error': 'Input cannot be empty.'})

            # Generate response using your email assistant
            response = email_generator(subject, from_email, to_email, original_content)
            
            return JsonResponse({'response': response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@method_decorator(firebase_auth_required, name='dispatch')
class StripeCheckoutView(View):
    def post(self, request):
        try:
            user_id = request.firebase_user['uid']
            db = firestore.client()
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': os.getenv('STRIPE_PRICE_ID'),  # Your subscription price ID
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri('/success?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/cancel'),
                client_reference_id=user_id,
            )
            
            # Store checkout session in Firestore
            db.collection('stripe_customers').document(user_id).set({
                'checkout_session_id': checkout_session.id,
                'status': 'pending'
            }, merge=True)
            
            return JsonResponse({
                'sessionId': checkout_session.id,
                'publicKey': os.getenv('STRIPE_PUBLISHABLE_KEY')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(firebase_auth_required, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        try:
            event = stripe.Event.construct_from(
                json.loads(request.body), stripe.api_key
            )
            
            if event.type == 'checkout.session.completed':
                session = event.data.object
                user_id = session.client_reference_id
                
                # Update user's subscription status
                db = firestore.client()
                db.collection('stripe_customers').document(user_id).update({
                    'status': 'active',
                    'subscription_id': session.subscription,
                    'updated_at': datetime.now(timezone.utc)
                })
                
                # Update custom claims
                auth.set_custom_user_claims(user_id, {'subscribed': True})
                
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    