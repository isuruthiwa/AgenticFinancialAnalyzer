import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configuration and utilities
from src.utils.config import load_config
from src.utils.logger import setup_logger

def check_advanced_ui_availability():
    """Check if advanced UI components are available."""
    try:
        from src.ui.dashboard import Dashboard
        dashboard_available = True
    except ImportError:
        dashboard_available = False

    try:
        from src.ui.chat_interface import ChatInterface
        chat_available = True
    except ImportError:
        chat_available = False

    return dashboard_available and chat_available

def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Agentic Financial Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load configuration
    config = load_config()
    logger = setup_logger()
    
    # Check component availability
    advanced_ui_available = check_advanced_ui_availability()
    
    if not advanced_ui_available:
        # Use basic interface when advanced components are not available
        st.title("📊 Agentic Financial Analyzer (Basic Mode)")
        st.warning("🔧 Running in basic mode. Some dependencies are missing. Install requirements.txt for full functionality.")
        
        try:
            from src.ui.basic_chat import BasicChatInterface
            basic_chat = BasicChatInterface()
            basic_chat.render()
        except ImportError as e:
            st.error(f"Cannot load basic interface: {e}")
            st.markdown("""
            ## Installation Required
            
            Please install the required dependencies:
            
            ```bash
            pip install streamlit PyPDF2 langchain langchain-openai pdfplumber python-docx
            ```
            
            Then restart the application.
            """)
        return
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🤖 Agentic Financial Analyzer")
    st.markdown("*AI-powered financial report analysis and insights*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("Navigation")
        
        # File upload section
        st.subheader("📄 Upload Documents")
        
        # Display file size limit
        st.caption("📁 Max file size: 200MB per file")
        
        uploaded_files = st.file_uploader(
            "Choose financial documents",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'],
            help="Upload PDF, Word documents, or images containing financial data. Max 200MB per file."
        )
        
        if uploaded_files:
            # Check file sizes
            total_size = sum(file.size for file in uploaded_files if hasattr(file, 'size'))
            
            if total_size > 200 * 1024 * 1024:  # 200MB total limit
                st.error("⚠️ Total file size exceeds 200MB. Please upload smaller files or fewer files at once.")
            else:
                st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")
                for file in uploaded_files:
                    file_size = getattr(file, 'size', 0)
                    size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                    st.write(f"• {file.name} ({size_mb:.1f} MB)" if file_size > 0 else f"• {file.name}")
                
                # Add troubleshooting info
                with st.expander("🔧 Having upload issues?"):
                    st.markdown("""
                    **If you're getting 403 errors:**
                    - Check your internet connection
                    - Try refreshing the page (F5)
                    - Make sure the file isn't corrupted
                    - Try uploading one file at a time
                    - Ensure file size is under 200MB
                    
                    **Supported formats:**
                    - PDF documents (text-based preferred)
                    - Word documents (.docx, .doc)
                    - Images (.png, .jpg, .jpeg)
                    """)
        
        st.divider()
        
        # Settings
        st.subheader("⚙️ Settings")
        analysis_depth = st.selectbox(
            "Analysis Depth",
            ["Quick Overview", "Standard Analysis", "Deep Dive"],
            index=1
        )
        
        include_historical = st.checkbox("Include Historical Data", value=True)
        include_predictions = st.checkbox("Generate Predictions", value=False)
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["💬 Chat Analysis", "📊 Dashboard"])
    
    with tab1:
        st.header("Chat with Your Financial Data")
        from src.ui.chat_interface import ChatInterface
        chat_interface = ChatInterface(uploaded_files, config)
        chat_interface.render()
    
    with tab2:
        st.header("Financial Analytics Dashboard")
        from src.ui.dashboard import Dashboard
        dashboard = Dashboard(uploaded_files, config)
        dashboard.render()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "Agentic Financial Analyzer - Powered by AI"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
