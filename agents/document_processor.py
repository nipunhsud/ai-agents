import os
from typing import Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredImageLoader,
)
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import pytesseract
from pdf2image import convert_from_path
from django.conf import settings
from django.http import JsonResponse
from django.views import View
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo-16k",
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

    def process_document(self, file_path: str, file_type: str) -> tuple[str, str]:
        """Process document and return extracted text and summary with details"""
        logger.debug(f"Processing file: {file_path} of type: {file_type}")
        extracted_text = self._extract_text(file_path, file_type)
        summary = self._generate_summary(extracted_text)
        return extracted_text, summary
        
    def _extract_text(self, file_path: str, file_type: str) -> str:
        if file_type == 'pdf':
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return '\n'.join(page.page_content for page in pages)
        
        elif file_type == 'docx':
            loader = Docx2txtLoader(file_path)
            pages = loader.load()
            return '\n'.join(page.page_content for page in pages)
        
        elif file_type in ['png', 'jpg', 'jpeg']:
            if file_type == 'pdf':
                images = convert_from_path(file_path)
                text = ''
                for image in images:
                    text += pytesseract.image_to_string(image)
                return text
            else:
                loader = UnstructuredImageLoader(file_path)
                pages = loader.load()
                return '\n'.join(page.page_content for page in pages)
        
        logger.debug(f"Unsupported file type: {file_type}")
        raise ValueError(f"Unsupported file type: {file_type}")

    def _generate_summary(self, text: str) -> str:
        docs = self.text_splitter.create_documents([text])
        
        # Create map prompt
        map_prompt_template = """Write a concise summary of the following text:
        {text}
        CONCISE SUMMARY:"""
        map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])
        
        # Create combine prompt
        combine_prompt_template = """Write a concise summary of the following summaries:
        {text}
        CONCISE SUMMARY:"""
        combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])
        
        chain = load_summarize_chain(
            self.llm,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
            verbose=True
        )
        
        summary = chain.run(docs)
        return summary

    def generate_custom_summary(self, text: str, prompt: str) -> str:
        """Generate a summary based on a custom prompt"""
        docs = self.text_splitter.create_documents([text])
        
        # Create map prompt with custom instruction
        map_template = """Based on the following text, {prompt}
        
        TEXT: {text}
        
        RESPONSE:"""
        map_prompt = PromptTemplate(template=map_template, input_variables=["text", "prompt"])
        
        # Create combine prompt
        combine_template = """Based on these responses, provide a unified response that {prompt}
        
        RESPONSES: {text}
        
        UNIFIED RESPONSE:"""
        combine_prompt = PromptTemplate(template=combine_template, input_variables=["text", "prompt"])
        
        chain = load_summarize_chain(
            self.llm,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
            verbose=True
        )
        
        # Include prompt in the chain run
        summary = chain.run({"input_documents": docs, "prompt": prompt})
        return summary

class UploadView(View):
    def post(self, request):
        logger.debug(f"Request data: {request.POST}")
        logger.debug(f"Files: {request.FILES}")

        # Get the list of uploaded files
        files = request.FILES.getlist('files')
        # Get the prompt from the form
        prompt = request.POST.get('prompt', '').strip()  # Trim whitespace

        # Check if any files were uploaded
        if not files:
            return JsonResponse({'error': 'No files were uploaded.'}, status=400)
        
        if not prompt:
            return JsonResponse({'error': 'Prompt cannot be empty.'}, status=400)

        results = []
        processor = DocumentProcessor()

        # Process each file
        for file in files:
            file_type = file.name.split('.')[-1]  # Get the file type from the file name
            
            # Process the document and get extracted text and summary
            extracted_text, summary = processor.process_document([file], [file_type])[0]  # Process the file
            logger.debug(f"Extracted text: {extracted_text}")
            # Generate a response based on the extracted text and the prompt
            response = self.generate_custom_summary(extracted_text, prompt)

            results.append({
                'prompt': prompt,
                'file_name': file.name,
                'extracted_text': extracted_text,
                'summary': summary,
                'response': response  # Include the response based on the prompt
            })

        return JsonResponse({'message': 'Files uploaded and processed successfully!', 'results': results})

