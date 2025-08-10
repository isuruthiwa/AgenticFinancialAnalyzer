<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Agentic Financial Analyzer - Copilot Instructions

This is a Python-based agentic AI system for financial report analysis. When working on this project:

## Architecture Guidelines
- Follow modular design with separate concerns for document processing, AI agents, analysis, and UI
- Use dependency injection patterns for AI model providers
- Implement proper error handling and logging throughout
- Follow async/await patterns for file processing and API calls

## Code Style
- Use type hints for all function parameters and return values
- Follow PEP 8 standards with black formatting
- Use dataclasses or Pydantic models for data structures
- Implement comprehensive docstrings with examples

## AI Agent Patterns
- Use LangChain for agent orchestration and tool calling
- Implement tool-based agents for specific financial analysis tasks
- Use structured output parsing for reliable data extraction
- Implement memory and context management for chat sessions

## Document Processing
- Support PDF, Word, and image file formats
- Use OCR for image-based documents with financial tables
- Implement table extraction and structure preservation
- Handle multi-page documents with proper chunking

## Financial Analysis
- Focus on standard financial metrics (ratios, trends, comparisons)
- Implement time-series analysis for historical data
- Use proper financial calculation methods and formulas
- Validate extracted financial data for accuracy

## UI Development
- Use Streamlit for the main interface
- Implement responsive design patterns
- Use proper state management for chat sessions
- Create reusable components for charts and visualizations

## Testing
- Write unit tests for all core functions
- Mock external API calls in tests
- Test document processing with sample files
- Implement integration tests for the full pipeline

## Security
- Sanitize all file uploads and inputs
- Use environment variables for API keys
- Implement proper session management
- Log security-relevant events
