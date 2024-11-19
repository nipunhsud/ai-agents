from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Conversation, Message, Document
from .document_processor import DocumentProcessor
from django.conf import settings
import os
import logging
from django.views import View

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

class UploadView(View):
    def post(self, request):
        files = request.FILES.getlist('files')
        prompt = request.POST.get('prompt', '')  # Get the prompt from the form
        
        if not files:
            return JsonResponse({'error': 'No files were uploaded.'}, status=400)

        results = []
        processor = DocumentProcessor()

        # Process each file
        for file in files:
            file_type = file.name.split('.')[-1]  # Get the file type from the file name
            extracted_text, summary = processor.process_documents([file], [file_type])[0]  # Process the file
            
            # Here you can use the prompt for further processing
            # For example, you might want to generate a response based on the prompt
            response = self.generate_response_based_on_prompt(extracted_text, prompt)

            results.append({
                'file_name': file.name,
                'extracted_text': extracted_text,
                'summary': summary,
                'response': response  # Include the response based on the prompt
            })

        return JsonResponse({'message': 'Files uploaded and processed successfully!', 'results': results})

    def generate_response_based_on_prompt(self, extracted_text, prompt):
        # Implement your logic to generate a response based on the extracted text and prompt
        # This could involve calling another service or processing the text
        return f"Response based on prompt: {prompt} and extracted text." 