"""
Chat interface component for the Agentic Financial Analyzer.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid

from src.agents.financial_agent import FinancialAgent
from src.processors.document_processor import DocumentProcessor
from src.utils.logger import logger

@dataclass
class ChatMessage:
    """Chat message data structure."""
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    files_referenced: List[str] = None

class ChatInterface:
    """Interactive chat interface for financial analysis."""
    
    def __init__(self, uploaded_files: List[Any], config: Any):
        """Initialize chat interface."""
        self.uploaded_files = uploaded_files or []
        self.config = config
        self.agent = FinancialAgent(config)
        self.processor = DocumentProcessor(config)
        
        # Initialize session state
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if 'processed_documents' not in st.session_state:
            st.session_state.processed_documents = {}
    
    def render(self):
        """Render the chat interface."""
        # Process uploaded files if any
        if self.uploaded_files and not st.session_state.processed_documents:
            self._process_uploaded_files()
        
        # Chat messages container
        chat_container = st.container()
        
        # Display chat history
        with chat_container:
            for message in st.session_state.chat_messages:
                self._render_message(message)
        
        # Chat input
        self._render_chat_input()
        
        # Quick action buttons
        self._render_quick_actions()
    
    def _process_uploaded_files(self):
        """Process uploaded files and extract financial data."""
        with st.spinner("Processing uploaded documents..."):
            for file in self.uploaded_files:
                try:
                    # Process the document
                    processed_data = self.processor.process_file(file)
                    st.session_state.processed_documents[file.name] = processed_data
                    
                    # Create detailed success message
                    text_length = len(processed_data.get('text', ''))
                    tables_count = len(processed_data.get('tables', []))
                    financial_data = processed_data.get('financial_data', {})
                    
                    success_msg = f"✅ Successfully processed **{file.name}**\n\n"
                    success_msg += f"📄 **Content Summary:**\n"
                    success_msg += f"• Text extracted: {text_length:,} characters\n"
                    success_msg += f"• Tables found: {tables_count}\n"
                    success_msg += f"• Financial metrics detected: {len(financial_data)}\n\n"
                    
                    if financial_data:
                        success_msg += f"🔍 **Detected Financial Data:**\n"
                        for key, value in list(financial_data.items())[:5]:  # Show first 5 metrics
                            success_msg += f"• {key.replace('_', ' ').title()}: {value}\n"
                        if len(financial_data) > 5:
                            success_msg += f"• ... and {len(financial_data) - 5} more metrics\n"
                    
                    success_msg += f"\n💬 I can now answer questions about this financial document!"
                    
                    # Add system message about processed file
                    self._add_message(
                        role="assistant",
                        content=success_msg,
                        files_referenced=[file.name]
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.name}: {e}")
                    
                    # Provide helpful error message based on the error type
                    error_msg = f"❌ **Error processing {file.name}**\n\n"
                    
                    if "empty" in str(e).lower():
                        error_msg += "🔍 **Issue:** The file appears to be empty or corrupted.\n\n"
                        error_msg += "**Possible solutions:**\n"
                        error_msg += "• Verify the file isn't corrupted\n"
                        error_msg += "• Try re-uploading the file\n"
                        error_msg += "• For scanned PDFs, ensure text is selectable\n"
                    elif "readable content" in str(e).lower():
                        error_msg += "🔍 **Issue:** No readable text could be extracted from the document.\n\n"
                        error_msg += "**Possible causes:**\n"
                        error_msg += "• The PDF is scanned/image-based (OCR needed)\n"
                        error_msg += "• The document is password-protected\n"
                        error_msg += "• The file format isn't fully supported\n\n"
                        error_msg += "**Try:** Converting to a text-based PDF or Word document"
                    else:
                        error_msg += f"**Technical details:** {str(e)}\n\n"
                        error_msg += "**Suggestions:**\n"
                        error_msg += "• Check if the file is corrupted\n"
                        error_msg += "• Try a different file format (PDF, Word, or image)\n"
                        error_msg += "• Ensure the file contains financial data"
                    
                    self._add_message(
                        role="assistant",
                        content=error_msg,
                        files_referenced=[file.name]
                    )
    
    def _render_message(self, message: ChatMessage):
        """Render a single chat message."""
        with st.chat_message(message.role):
            st.write(message.content)
            
            if message.files_referenced:
                with st.expander(f"📄 Referenced files ({len(message.files_referenced)})"):
                    for file_name in message.files_referenced:
                        st.write(f"• {file_name}")
    
    def _render_chat_input(self):
        """Render chat input and handle user messages."""
        # Chat input
        if prompt := st.chat_input("Ask me anything about your financial documents..."):
            # Add user message
            self._add_message(role="user", content=prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        # Get response from agent
                        response = self.agent.process_query(
                            query=prompt,
                            documents=st.session_state.processed_documents
                        )
                        
                        # Display response
                        st.write(response.content)
                        
                        # Add assistant message
                        self._add_message(
                            role="assistant",
                            content=response.content,
                            files_referenced=response.sources if hasattr(response, 'sources') else None
                        )
                        
                    except Exception as e:
                        error_msg = f"I encountered an error while processing your request: {str(e)}"
                        st.error(error_msg)
                        self._add_message(role="assistant", content=error_msg)
    
    def _render_quick_actions(self):
        """Render quick action buttons for common queries."""
        st.subheader("💡 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Financial Summary", use_container_width=True):
                self._handle_quick_action("Provide a comprehensive financial summary of the uploaded documents.")
        
        with col2:
            if st.button("📊 Key Metrics", use_container_width=True):
                self._handle_quick_action("Extract and analyze the key financial metrics and ratios.")
        
        with col3:
            if st.button("🔍 Risk Analysis", use_container_width=True):
                self._handle_quick_action("Perform a risk analysis based on the financial data.")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            if st.button("📅 Trend Analysis", use_container_width=True):
                self._handle_quick_action("Analyze trends and patterns in the financial data over time.")
        
        with col5:
            if st.button("💰 Profitability", use_container_width=True):
                self._handle_quick_action("Analyze the company's profitability and margins.")
        
        with col6:
            if st.button("⚠️ Red Flags", use_container_width=True):
                self._handle_quick_action("Identify any potential red flags or areas of concern.")
    
    def _handle_quick_action(self, query: str):
        """Handle quick action button clicks."""
        # Ensure processed_documents exists
        if 'processed_documents' not in st.session_state:
            st.session_state.processed_documents = {}
        
        # Add user message to chat
        self._add_message(role="user", content=query)
        
        # Display user message
        with st.chat_message("user"):
            st.write(query)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    # Get response from agent
                    response = self.agent.process_query(
                        query=query,
                        documents=st.session_state.processed_documents
                    )
                    
                    # Display response
                    st.write(response.content)
                    
                    # Add assistant message
                    self._add_message(
                        role="assistant",
                        content=response.content,
                        files_referenced=response.sources if hasattr(response, 'sources') else None
                    )
                    
                except Exception as e:
                    error_msg = f"I encountered an error while processing your request: {str(e)}"
                    st.error(error_msg)
                    self._add_message(role="assistant", content=error_msg)
    
    def _add_message(
        self,
        role: str,
        content: str,
        files_referenced: Optional[List[str]] = None
    ):
        """Add a message to the chat history."""
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=str(st.session_state.get('timestamp', '')),
            files_referenced=files_referenced or []
        )
        
        st.session_state.chat_messages.append(message)
