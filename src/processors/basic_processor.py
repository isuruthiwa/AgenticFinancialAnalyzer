"""
Basic document processor without external dependencies.
"""
import os
import io
from typing import Dict, Any, List
from src.utils.logger import logger

class BasicDocumentProcessor:
    """Basic document processor with minimal dependencies."""
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process a file and extract basic information."""
        logger.info(f"Processing file: {filename} ({len(file_content)} bytes)")
        
        result = {
            'filename': filename,
            'type': self._get_file_type(filename),
            'content': '',
            'text': '',
            'tables': [],
            'financial_data': {},
            'size': len(file_content)
        }
        
        # For now, create a basic text representation
        if filename.lower().endswith('.pdf'):
            result['content'] = f"PDF file: {filename} ({len(file_content)} bytes)"
            result['text'] = "PDF processing requires additional dependencies. Please install PyPDF2 or pdfplumber."
        elif filename.lower().endswith(('.doc', '.docx')):
            result['content'] = f"Word document: {filename} ({len(file_content)} bytes)"
            result['text'] = "Word document processing requires python-docx dependency."
        else:
            result['content'] = f"File: {filename} ({len(file_content)} bytes)"
            result['text'] = "File uploaded successfully. Content analysis requires additional dependencies."
        
        # Create some dummy financial data for testing
        result['financial_data'] = {
            'revenue': ['Sample revenue data would appear here'],
            'assets': ['Sample asset data would appear here'],
            'profit': ['Sample profit data would appear here']
        }
        
        logger.info(f"Successfully processed {filename} with basic processor")
        return result
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename."""
        ext = filename.lower().split('.')[-1]
        type_map = {
            'pdf': 'pdf',
            'doc': 'word',
            'docx': 'word',
            'jpg': 'image',
            'jpeg': 'image',
            'png': 'image',
            'txt': 'text'
        }
        return type_map.get(ext, 'unknown')
