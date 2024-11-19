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
import pytesseract
from pdf2image import convert_from_path
from django.conf import settings

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
        
        raise ValueError(f"Unsupported file type: {file_type}")

    def _generate_summary(self, text: str) -> str:
        docs = self.text_splitter.create_documents([text])
        chain = load_summarize_chain(
            self.llm,
            chain_type="map_reduce",
            verbose=True
        )
        summary = chain.run(docs)
        return summary

    def generate_custom_summary(self, text: str, prompt: str) -> str:
        """Generate a summary based on a custom prompt"""
        docs = self.text_splitter.create_documents([text])
        custom_prompt = f"""
        Based on the following text, {prompt}
        
        Text: {{text}}
        
        Summary:
        """
        chain = load_summarize_chain(
            self.llm,
            chain_type="map_reduce",
            verbose=True,
            prompt=custom_prompt
        )
        summary = chain.run(docs)
        return summary 