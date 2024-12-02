from typing import List, Dict, Optional
import openai
from pathlib import Path
import json
from enum import Enum
import logging
from openai import AsyncOpenAI

# Get logger
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    PRD = "prd"
    TECHNICAL_DOC = "technical_doc"
    SOP = "sop"
    API_DOC = "api_doc"

class OutputFormat(Enum):
    NOTION = "notion"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"

class TechnicalWriter:
    def __init__(self, api_key: str):
        """Initialize the Technical Writer AI agent.
        
        Args:
            api_key: OpenAI API key for GPT access
        """
        logger.info("Initializing TechnicalWriter")
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Load document templates
        logger.info("Loading document templates")
        self.templates = self._load_templates()
        logger.debug(f"Loaded templates: {list(self.templates.keys())}")

    def _load_templates(self) -> Dict:
        """Load document templates from the templates directory."""
        template_dir = Path(__file__).parent / "templates"
        logger.debug(f"Loading templates from: {template_dir}")
        templates = {}
        
        if not template_dir.exists():
            logger.error(f"Template directory not found: {template_dir}")
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
        
        for template_file in template_dir.glob("*.json"):
            logger.debug(f"Loading template file: {template_file}")
            try:
                with open(template_file) as f:
                    templates[template_file.stem] = json.load(f)
                    logger.debug(f"Successfully loaded template: {template_file.stem}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse template {template_file}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")
                raise
                
        return templates

    async def generate_document(
        self,
        content: str,
        doc_type: DocumentType,
        output_format: OutputFormat,
        custom_template: Optional[Dict] = None,
        tone: str = "professional",
        technical_level: str = "intermediate"
    ) -> str:
        """Generate a technical document from input content.
        
        Args:
            content: Raw input text/notes to process
            doc_type: Type of document to generate
            output_format: Desired output format
            custom_template: Optional custom document template
            tone: Writing tone (casual, professional, formal)
            technical_level: Technical detail level (basic, intermediate, advanced)
            
        Returns:
            Generated document in the specified format
        """
        logger.info(f"Generating document of type: {doc_type.value}")
        
        # Select template
        template = custom_template if custom_template else self.templates.get(doc_type.value)
        if not template:
            logger.error(f"Template not found for document type: {doc_type.value}")
            raise ValueError(f"Template not found for document type: {doc_type.value}")
        
        logger.debug("Generating document structure")
        structure = await self._generate_structure(content, template)
     
        logger.debug(f"Formatting output as {output_format.value}")
        return self._format_output(structure, output_format)

    async def _generate_structure(self, content: str, template: Dict) -> Dict:
        """Generate document structure from input content using the template."""
        try:
            prompt = self._create_structure_prompt(content, template)
            logger.debug(f"Structure generation prompt: {prompt[:200]}...")
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical writing assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            logger.debug(f"Structure generation response: {result[:200]}...")
            
            # Ensure we have valid JSON
            if isinstance(result, str):
                result = json.loads(result)
            
            return result
        except Exception as e:
            logger.error(f"Error in _generate_structure: {str(e)}", exc_info=True)
            raise

    async def _generate_content(self, structure: Dict, tone: str, technical_level: str) -> Dict:
        """Generate full document content from the structure."""
        try:
            prompt = self._create_content_prompt(structure, tone, technical_level)
            logger.debug(f"Content generation prompt: {prompt[:200]}...")
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical writing assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            result = response.choices[0].message.content
            print(result)
            logger.debug(f"Content generation response: {result[:200]}...")
            
            # Ensure we have valid JSON
            if isinstance(result, str):
                result = json.loads(result)
                
            return result
        except Exception as e:
            logger.error(f"Error in _generate_content: {str(e)}", exc_info=True)
            raise

    def _format_output(self, document: Dict, output_format: OutputFormat) -> str:
        """Format the generated document in the desired output format."""
        return json.dumps(document, indent=2)
        try:
            logger.debug(f"Formatting output for format: {output_format}")
            
            if not document:
                raise ValueError("No document content to format")
            
            if output_format == OutputFormat.MARKDOWN:
                return self._format_as_markdown(document)
            elif output_format == OutputFormat.HTML:
                return self._format_as_html(document)
            elif output_format == OutputFormat.PDF:
                return self._format_as_pdf(document)
            elif output_format == OutputFormat.NOTION:
                return self._format_for_notion(document)
            else:
                # Default to JSON
                return json.dumps(document, indent=2)
                
        except Exception as e:
            logger.error(f"Error in _format_output: {str(e)}", exc_info=True)
            # Return JSON as fallback
            return json.dumps(document, indent=2) if document else ""

    def _create_structure_prompt(self, content: str, template: Dict) -> str:
        """Create prompt for generating document structure."""
        return f"""
        As a technical writing assistant, analyze the following content and create a structured document 
        following the provided template. Return the result as a valid JSON object.
        
        Content to process: {content}
        
        Template Structure: {json.dumps(template, indent=2)}
        
        Requirements:
        1. Follow the template structure exactly
        2. Fill in all relevant sections based on the content
        3. Maintain proper JSON format
        4. Ensure no sections are left empty
        5. Return only the JSON object, no additional text
        """

    def _create_content_prompt(self, structure: Dict, tone: str, technical_level: str) -> str:
        """Create prompt for generating full document content."""
        return f"""
        As a technical writing assistant, expand this document structure into a full technical document.
        Return the result as a valid JSON object.
        
        Document Structure: {json.dumps(structure, indent=2)}
        
        Writing Guidelines:
        - Tone: {tone}
        - Technical Level: {technical_level}
        
        Requirements:
        1. Maintain the exact structure provided
        2. Expand each section with detailed content
        3. Match the specified tone and technical level
        4. Ensure all content is relevant and meaningful
        5. Return only the JSON object, no additional text
        """

    def _format_for_notion(self, document: Dict) -> str:
        """Format document for Notion export.
        
        Formats document as Notion-compatible markdown with additional properties
        for Notion's API format.
        """
        formatted = []
        
        # Add title
        if "title" in document:
            formatted.append(f"# {document['title']}\n")
        
        # Process each section recursively
        def process_section(section: Dict, level: int = 1):
            if "heading" in section:
                formatted.append(f"{'#' * level} {section['heading']}\n")
            if "content" in section:
                formatted.append(f"{section['content']}\n")
            if "subsections" in section:
                for subsection in section["subsections"]:
                    process_section(subsection, level + 1)
        
        # Process main sections
        if "sections" in document:
            for section in document["sections"]:
                process_section(section)
        
        return "\n".join(formatted)

    def _format_as_markdown(self, document: Dict) -> str:
        """Format document as Markdown.
        
        Converts the document structure into standard markdown format.
        """
        formatted = []
        
        # Add title and metadata
        if "title" in document:
            formatted.extend([
                f"# {document['title']}\n",
                f"_{document.get('date', '')}_\n" if 'date' in document else "",
                f"_{document.get('author', '')}_\n" if 'author' in document else "",
                "\n---\n"
            ])
        
        # Process sections recursively
        def process_section(section: Dict, level: int = 1):
            if "heading" in section:
                formatted.append(f"\n{'#' * level} {section['heading']}\n")
            if "content" in section:
                formatted.append(f"{section['content']}\n")
            if "subsections" in section:
                for subsection in section["subsections"]:
                    process_section(subsection, level + 1)
        
        # Process main sections
        if "sections" in document:
            for section in document["sections"]:
                process_section(section)
        
        return "\n".join(formatted)

    def _format_as_html(self, document: Dict) -> str:
        """Format document as HTML.
        
        Converts the document structure into HTML format with basic styling.
        """
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<style>",
            "body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1, h2, h3, h4, h5, h6 { color: #333; }",
            "</style>",
            "</head>",
            "<body>"
        ]
        
        if "title" in document:
            html.append(f"<h1>{document['title']}</h1>")
        
        def process_section(section: Dict, level: int = 1):
            if "heading" in section:
                html.append(f"<h{level}>{section['heading']}</h{level}>")
            if "content" in section:
                html.append(f"<p>{section['content']}</p>")
            if "subsections" in section:
                for subsection in section["subsections"]:
                    process_section(subsection, min(level + 1, 6))
        
        if "sections" in document:
            for section in document["sections"]:
                process_section(section, 2)
        
        html.extend(["</body>", "</html>"])
        return "\n".join(html)

    def _format_as_pdf(self, document: Dict) -> str:
        """Format document as PDF.
        
        Returns HTML that can be converted to PDF using a PDF rendering library.
        Note: Actual PDF conversion would require additional dependencies like
        WeasyPrint or pdfkit.
        """
        # For PDF generation, we'll return HTML that can be converted to PDF
        # The actual PDF conversion should be handled by the calling code
        return self._format_as_html(document)
