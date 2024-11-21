from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Conversation, Message, Document
from .document_processor import DocumentProcessor
from django.conf import settings
import os
import logging
from django.views import View
from django.core.files.storage import default_storage
from .agent import Agent
logger = logging.getLogger(__name__)

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