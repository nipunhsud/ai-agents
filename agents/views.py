import json
import logging
import os
import requests
import csv
import io

from django.views import View
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from langchain.schema import HumanMessage
from langchain.chat_models import ChatOpenAI
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from firebase_admin import firestore
from datetime import datetime, timezone
from firebase_admin import auth
import stripe
from django.core.files.uploadedfile import InMemoryUploadedFile

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
    def post(self, request, stock_name=None):
        # Use stock_name from URL if provided, otherwise get from POST data
        user_input = stock_name or request.POST.get('input', '')
        user_id = request.firebase_user['uid']
        
        logger.info(f"Processing stock analysis for ticker: {user_input}")
        
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
            
            # Check user subscription status
            user_email = request.firebase_user['email']
            user_subscription_doc = db.collection('stripe_customers').document(user_email).get()
            
            # Only enforce limit for non-subscribed users
            if not user_subscription_doc.exists or user_subscription_doc.get('status') != 'active':
                if len(requests) >= 10:
                    return JsonResponse({
                        'error': 'Daily limit reached',
                        'message': 'You have reached your daily limit of 10 requests. Please subscribe for unlimited access.',
                        'subscribe': True
                    }, status=402)

            # Process request
            _, json_data, price_history = stock_generator(user_input)
            
            # Save to Firestore
            db.collection('stock_analysis').add({
                'user_id': user_id,
                'ticker': user_input,
                'analysis': json_data,
                'user_email': user_email,   
                'timestamp': datetime.now(timezone.utc),
            })
            
            response = JsonResponse({
                'response': json_data, 
                'price_history': price_history,
                'content_type': 'text/markdown',
                'requests_remaining': 10 - (len(requests) + 1)
            })
            response['Content-Type'] = 'application/json'
            return response
            
        except Exception as e:
            logger.error(f"Error processing stock analysis for {user_input}: {str(e)}")
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
                customer_email=request.firebase_user.get('email'),
                billing_address_collection='required',
                line_items=[{
                    'price': os.getenv('STRIPE_PRICE_ID'),
                    'quantity': 1,
                }],
                mode='subscription',
                allow_promotion_codes=True,
                success_url=request.build_absolute_uri('/success?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/cancel'),
                client_reference_id=user_id,
                payment_intent_data={
                    'metadata': {
                        'user_id': user_id
                    }
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id
                    }
                }
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

@method_decorator(csrf_exempt, name='dispatch')  # Stripe webhooks can't include CSRF
class StripeWebhookView(View):
    def post(self, request):
        try:
            # Log incoming webhook
            logger.info("Received Stripe webhook")
            
            # Parse the JSON payload
            payload = json.loads(request.body.decode('utf-8'))
            event_type = payload['type']
            event_data = payload['data']['object']
            
            logger.info(f"Processing webhook event type: {event_type}")
            logger.debug(f"Webhook payload: {payload}")
            print(event_data)
            # Handle different event types
            if event_type == 'checkout.session.completed':
                # Update user's subscription status
                db = firestore.client()
                email =  event_data['customer_details']['email']
                subscription_data = {
                    'email': event_data['customer_details']['email'],    
                    'name': event_data['customer_details']['name'],
                    'status': 'active',
                    'subscription_id': event_data.get('subscription'),
                    'date': event_data,
                    'created_at': datetime.now(timezone.utc),
                }
                logger.info(f"Updating Firestore for user {email} with data: {subscription_data}")
                
                db.collection('stripe_customers').document(email).set(
                    subscription_data, 
                    merge=True
                )
                
                # Update custom claims                
                logger.info("Successfully processed checkout.session.completed")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Subscription activated successfully'
                })
            
            # Handle other event types if needed
            logger.info(f"Unhandled event type: {event_type}")
            return JsonResponse({
                'status': 'success',
                'message': f'Unhandled event type: {event_type}'
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {str(e)}")
            logger.debug(f"Raw payload: {request.body.decode('utf-8')}")
            return JsonResponse({
                'error': 'Invalid JSON payload',
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Stripe webhook error: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': str(e),
                'message': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RAGAssistantView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            query = data.get('query', '')

            if not query:
                return JsonResponse({'error': 'Query cannot be empty'}, status=400)

            # Call RAG API
            response = requests.post(
                'https://rag-agent-axt4.onrender.com/ask',
                json={'query': query},
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Origin': 'https://www.purnam.ai'
                }
            )
            
            if response.status_code != 200:
                return JsonResponse({
                    'error': f'RAG API error: {response.text}'
                }, status=response.status_code)

            return JsonResponse(response.json())

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(firebase_auth_required, name='dispatch')
class UserStockAnalysisView(View):
    def get(self, request):
        try:
            # Get ticker from query params
            ticker = request.GET.get('ticker')
            
            # Get user email from firebase auth
            user_email = request.firebase_user.get('email')
            if not user_email:
                return JsonResponse({
                    'success': False,
                    'error': 'User email not found in token'
                }, status=401)

            logger.info(f"Fetching stock analyses for user: {user_email} {'for ticker: ' + ticker if ticker else ''}")
            
            # Query Firestore for analyses
            db = firestore.client()
            query = db.collection('stock_analysis').where('user_email', '==', user_email)
            
            # Add ticker filter if provided
            if ticker:
                query = query.where('ticker', '==', ticker.upper())
            
            # Get results
            analyses = query.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
            
            # Format the response data
            analysis_list = []
            for analysis in analyses:
                data = analysis.to_dict()
                analysis_list.append({
                    'id': analysis.id,
                    'ticker': data.get('ticker'),
                    'analysis': data.get('analysis'),
                    'markdown': data.get('markdown'),
                    'timestamp': data.get('timestamp').isoformat() if data.get('timestamp') else None,
                    'user_email': data.get('user_email')
                })
            
            # Sort the list to put BUY recommendations first
            analysis_list.sort(
                key=lambda x: (
                    0 if x.get('analysis', '').upper().find('BUY') != -1 else 1,
                    -datetime.fromisoformat(x.get('timestamp')).timestamp() if x.get('timestamp') else float('-inf')
                )
            )
            
            logger.info(f"Found {len(analysis_list)} analyses for user {user_email}")
            return JsonResponse({
                'success': True,
                'analyses': analysis_list
            })
            
        except Exception as e:
            logger.error(f"Error fetching stock analyses: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(firebase_auth_required, name='dispatch')
class StockTickerCSVUploadView(View):
    def post(self, request):
        try:
            # Check if file was uploaded
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded'
                }, status=400)
            
            csv_file: InMemoryUploadedFile = request.FILES['file']
            
            # Validate file type
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({
                    'success': False,
                    'error': 'File must be a CSV'
                }, status=400)
            
            # Read CSV file
            tickers = set()  # Using set to avoid duplicates
            try:
                # Decode the file content
                file_content = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(file_content))
                user_email = request.firebase_user.get('email')
                user_id = request.firebase_user.get('uid')
                
                # Find the symbol column
                headers = csv_reader.fieldnames
                if not headers:
                    return JsonResponse({
                        'success': False,
                        'error': 'CSV file has no headers'
                    }, status=400)
                
                # Create a mapping of lowercase headers to actual headers
                header_map = {h.lower(): h for h in headers}
                
                # Look for symbol column in various forms
                symbol_variants = ['symbol', 'ticker', 'stock']
                symbol_col = next((header_map[variant] for variant in symbol_variants 
                                if variant in header_map), None)
                
                if not symbol_col:
                    return JsonResponse({
                        'success': False,
                        'error': 'No Symbol/Ticker column found in CSV',
                        'available_columns': headers
                    }, status=400)
                
                logger.info(f"Found symbol column: {symbol_col}")
                
                # Process each row
                for row in csv_reader:
                    if symbol_col not in row:
                        logger.error(f"Missing column {symbol_col} in row: {row}")
                        continue
                        
                    ticker = row[symbol_col].strip().upper()
                    if ticker and len(ticker) <= 5:  # Basic ticker validation
                        tickers.add(ticker)
                
                tickers = list(tickers)  # Convert set back to list
                db = firestore.client()
                valid_analyses = []
                for ticker in tickers:
                    try:
                        # Process request
                        _, json_data, price_history = stock_generator(ticker)
                        
                        # Validate json_data
                        if not json_data:
                            logger.warning(f"Invalid json_data for ticker {ticker}, skipping...")
                            continue
                        
                        # Save to Firestore
                        db.collection('stock_analysis').add({
                            'user_id': user_id,
                            'ticker': ticker,
                            'analysis': json_data,
                            'user_email': user_email,   
                            'timestamp': datetime.now(timezone.utc),
                        })
                        valid_analyses.append(ticker)
                    except Exception as e:
                        logger.error(f"Error processing ticker {ticker}: {str(e)}")
                        continue

                if not valid_analyses:
                    return JsonResponse({
                        'success': False,
                        'error': 'No valid analyses could be generated from the provided tickers'
                    }, status=400)
                
                logger.info(f"Successfully processed {len(valid_analyses)} out of {len(tickers)} tickers")
                
                db.collection('stock_bulk').add({
                    'tickers': valid_analyses,
                    'timestamp': datetime.now(timezone.utc),
                })
                
                return JsonResponse({
                    'success': True,
                    'tickers': valid_analyses,
                    'analyses': []
                })
                
            except UnicodeDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid file encoding. Please ensure the file is UTF-8 encoded.'
                }, status=400)
            except csv.Error:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid CSV format'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    