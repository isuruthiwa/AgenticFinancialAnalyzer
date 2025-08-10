"""
Basic chat interface without LangChain dependencies.
"""
import streamlit as st
from typing import Dict, Any, List
from src.processors.basic_processor import BasicDocumentProcessor
from src.utils.logger import logger

class BasicChatInterface:
    """Basic chat interface with minimal dependencies."""
    
    def __init__(self):
        self.processor = BasicDocumentProcessor()
        
    def render(self):
        """Render the basic chat interface."""
        st.header("💬 Financial Analysis Chat")
        st.info("⚠️ Running in basic mode. Install additional dependencies for full functionality.")
        
        # File uploader
        st.subheader("📁 Upload Financial Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF, Word, or image files",
            type=['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file not in st.session_state.get('processed_files', []):
                    # Process the file
                    file_content = uploaded_file.read()
                    result = self.processor.process_file(file_content, uploaded_file.name)
                    
                    # Store in session state
                    if 'processed_documents' not in st.session_state:
                        st.session_state.processed_documents = {}
                    
                    st.session_state.processed_documents[uploaded_file.name] = result
                    
                    if 'processed_files' not in st.session_state:
                        st.session_state.processed_files = []
                    st.session_state.processed_files.append(uploaded_file)
                    
                    st.success(f"✅ Processed {uploaded_file.name}")
        
        # Show processed documents
        if st.session_state.get('processed_documents'):
            st.subheader("📋 Processed Documents")
            for filename, doc_data in st.session_state.processed_documents.items():
                with st.expander(f"📄 {filename}"):
                    st.write(f"**Type:** {doc_data['type']}")
                    st.write(f"**Size:** {doc_data['size']} bytes")
                    st.write(f"**Content:** {doc_data['content']}")
        
        # Quick actions
        self._render_quick_actions()
        
        # Chat interface
        self._render_chat()
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.subheader("💡 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Financial Summary", use_container_width=True):
                self._add_message("assistant", "Basic financial summary: I can see you've uploaded financial documents. To provide detailed analysis, please install the required dependencies (PyPDF2, langchain, etc.)")
        
        with col2:
            if st.button("📊 Key Metrics", use_container_width=True):
                self._add_message("assistant", "Key metrics analysis requires full document processing capabilities. Please install PyPDF2 and other dependencies for detailed metric extraction.")
        
        with col3:
            if st.button("🔍 Risk Analysis", use_container_width=True):
                self._add_message("assistant", "Risk analysis is available with full installation. Current basic mode provides limited functionality.")
    
    def _render_chat(self):
        """Render basic chat interface."""
        st.subheader("💬 Chat")
        
        # Initialize chat messages
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your financial documents..."):
            # Add user message
            self._add_message("user", prompt)
            
            # Generate response
            response = self._generate_response(prompt)
            self._add_message("assistant", response)
    
    def _add_message(self, role: str, content: str):
        """Add a message to the chat."""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        st.session_state.chat_messages.append({
            "role": role,
            "content": content
        })
        
        # Display the new message
        with st.chat_message(role):
            st.write(content)
    
    def _generate_response(self, query: str) -> str:
        """Generate a basic response."""
        query_lower = query.lower()
        
        # Simple keyword-based responses
        if any(word in query_lower for word in ['revenue', 'sales', 'income']):
            return "I can help analyze revenue data once the full document processing is available. Please install PyPDF2 and LangChain dependencies for detailed financial analysis."
        
        elif any(word in query_lower for word in ['profit', 'earnings', 'margin']):
            return "Profitability analysis requires full document processing capabilities. With the complete installation, I can extract and analyze profit metrics from your financial documents."
        
        elif any(word in query_lower for word in ['risk', 'concern', 'red flag']):
            return "Risk assessment functionality is available with the full installation. I would need to process your documents with PyPDF2 and use AI analysis capabilities."
        
        elif any(word in query_lower for word in ['summary', 'overview']):
            if st.session_state.get('processed_documents'):
                docs_info = []
                for filename, doc_data in st.session_state.processed_documents.items():
                    docs_info.append(f"- {filename} ({doc_data['type']}, {doc_data['size']} bytes)")
                return f"Document Summary:\\n\\nProcessed documents:\\n" + "\\n".join(docs_info) + "\\n\\nTo provide detailed financial analysis, please install the required dependencies."
            else:
                return "No documents have been uploaded yet. Please upload financial documents to get started."
        
        else:
            return "I'm running in basic mode. For full financial analysis capabilities, please install the required dependencies (PyPDF2, langchain, pdfplumber, etc.). Currently, I can help with basic document management and provide guidance on installation."
