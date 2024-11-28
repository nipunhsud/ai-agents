import json
import logging

from django.views import View
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from langchain.schema import HumanMessage
from langchain.chat_models import ChatOpenAI
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required

from .agent import Agent
from .models import Message
from .models import Document
from .models import Conversation
from .gift_agent import gift_prediction
from .document_processor import DocumentProcessor


logger = logging.getLogger(__name__)


chat = ChatOpenAI(
    temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    model_name="gpt-4"  # You can also use "gpt-4" if you have access
)


def test(request):
    messages = [HumanMessage(content="do you know messi")]
    response = chat(messages)
    response = str(response.content)
    return JsonResponse({'agdum':response})


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
            'previous_gifts': request.POST.get('previous_gifts')
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

@login_required
def react_page(request):
    logger.debug(f"User {request.user} accessing react page")
    try:
        return render(request, 'chat/react.html')
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
        
