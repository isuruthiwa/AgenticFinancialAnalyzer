"""
Financial AI agent for analyzing documents and answering queries.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from langchain_openai import OpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory

from src.utils.logger import logger

@dataclass
class AgentResponse:
    """Response from the financial agent."""
    content: str
    sources: List[str] = None
    confidence: float = 0.0
    reasoning: str = ""

class FinancialAgent:
    """AI agent for financial analysis and query processing."""
    
    def __init__(self, config: Any):
        """Initialize the financial agent."""
        self.config = config
        self.llm = self._initialize_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = self._create_tools()
        self.agent = self._initialize_agent()
    
    def _initialize_llm(self):
        """Initialize the language model."""
        if self.config.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.config.openai_api_key,
                model_name="gpt-4",
                temperature=0.1
            )
        else:
            logger.warning("No OpenAI API key provided, using mock responses")
            return None
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent."""
        tools = [
            Tool(
                name="financial_calculator",
                description="Calculate financial ratios and metrics",
                func=self._calculate_financial_metrics
            ),
            Tool(
                name="trend_analyzer",
                description="Analyze financial trends and patterns",
                func=self._analyze_trends
            ),
            Tool(
                name="risk_assessor",
                description="Assess financial risks and red flags",
                func=self._assess_risks
            ),
            Tool(
                name="document_searcher",
                description="Search for specific information in financial documents",
                func=self._search_documents
            )
        ]
        return tools
    
    def _initialize_agent(self):
        """Initialize the agent with tools and memory."""
        if not self.llm:
            return None
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
    
    def process_query(
        self,
        query: str,
        documents: Dict[str, Any]
    ) -> AgentResponse:
        """Process a user query about financial documents."""
        try:
            # Store documents in context
            self._update_document_context(documents)
            
            if self.agent:
                # Use the LangChain agent
                response = self.agent.run(input=query)
                
                return AgentResponse(
                    content=response,
                    sources=list(documents.keys()),
                    confidence=0.8,
                    reasoning="Generated using LLM agent"
                )
            else:
                # Fallback to rule-based responses
                return self._generate_fallback_response(query, documents)
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return AgentResponse(
                content=f"I encountered an error while processing your query: {str(e)}",
                confidence=0.0
            )
    
    def _update_document_context(self, documents: Dict[str, Any]):
        """Update the agent's context with document information."""
        # Store documents for tool access
        self.current_documents = documents
        
        context_summary = []
        
        for doc_name, doc_data in documents.items():
            summary = f"Document: {doc_name}\n"
            
            if 'text' in doc_data:
                text_preview = doc_data['text'][:500] + "..." if len(doc_data['text']) > 500 else doc_data['text']
                summary += f"Content preview: {text_preview}\n"
            
            if 'content' in doc_data:
                content_preview = doc_data['content'][:500] + "..." if len(doc_data['content']) > 500 else doc_data['content']
                summary += f"Content preview: {content_preview}\n"
            
            if 'tables' in doc_data and doc_data['tables']:
                summary += f"Contains {len(doc_data['tables'])} financial tables\n"
            
            if 'financial_data' in doc_data:
                summary += f"Extracted financial metrics: {list(doc_data['financial_data'].keys())}\n"
            
            context_summary.append(summary)
        
        # Store in memory for agent
        if self.memory:
            context_message = "Financial documents context:\n" + "\n---\n".join(context_summary)
            self.memory.chat_memory.add_ai_message(context_message)
    
    def _generate_fallback_response(
        self,
        query: str,
        documents: Dict[str, Any]
    ) -> AgentResponse:
        """Generate a fallback response when LLM is not available."""
        query_lower = query.lower()
        
        # Analyze query intent
        if any(keyword in query_lower for keyword in ['summary', 'overview', 'summarize']):
            return self._generate_summary_response(documents)
        
        elif any(keyword in query_lower for keyword in ['ratio', 'metric', 'kpi']):
            return self._generate_metrics_response(documents)
        
        elif any(keyword in query_lower for keyword in ['risk', 'concern', 'red flag']):
            return self._generate_risk_response(documents)
        
        elif any(keyword in query_lower for keyword in ['trend', 'growth', 'change']):
            return self._generate_trend_response(documents)
        
        else:
            return AgentResponse(
                content="I understand you're asking about your financial documents. "
                       "To provide better responses, please set up your OpenAI API key in the configuration. "
                       "For now, I can help with basic document summaries and metric calculations.",
                confidence=0.3
            )
    
    def _generate_summary_response(self, documents: Dict[str, Any]) -> AgentResponse:
        """Generate a summary response."""
        if not documents:
            return AgentResponse(
                content="No documents have been uploaded for analysis.",
                confidence=1.0
            )
        
        doc_count = len(documents)
        doc_names = list(documents.keys())
        
        content = f"📄 **Document Summary**\n\n"
        content += f"I've analyzed {doc_count} financial document(s):\n"
        
        for doc_name in doc_names:
            content += f"• {doc_name}\n"
        
        content += "\nKey observations:\n"
        content += "• Documents contain financial data and statements\n"
        content += "• Ready for detailed analysis and metric calculations\n"
        content += "• Ask me specific questions about ratios, trends, or performance\n"
        
        return AgentResponse(
            content=content,
            sources=doc_names,
            confidence=0.7
        )
    
    def _generate_metrics_response(self, documents: Dict[str, Any]) -> AgentResponse:
        """Generate a metrics-focused response."""
        content = "📊 **Financial Metrics Analysis**\n\n"
        
        if not documents:
            content += "Please upload financial documents to calculate metrics."
        else:
            content += "Based on your uploaded documents, I can help calculate:\n\n"
            content += "**Profitability Ratios:**\n"
            content += "• Gross Profit Margin\n"
            content += "• Operating Margin\n"
            content += "• Net Profit Margin\n"
            content += "• Return on Equity (ROE)\n"
            content += "• Return on Assets (ROA)\n\n"
            
            content += "**Liquidity Ratios:**\n"
            content += "• Current Ratio\n"
            content += "• Quick Ratio\n"
            content += "• Cash Ratio\n\n"
            
            content += "**Leverage Ratios:**\n"
            content += "• Debt-to-Equity\n"
            content += "• Interest Coverage\n"
            content += "• Debt Service Coverage\n\n"
            
            content += "Please ask about specific metrics or ratios you'd like me to calculate."
        
        return AgentResponse(
            content=content,
            sources=list(documents.keys()),
            confidence=0.8
        )
    
    def _generate_risk_response(self, documents: Dict[str, Any]) -> AgentResponse:
        """Generate a risk analysis response."""
        content = "⚠️ **Risk Analysis**\n\n"
        
        if not documents:
            content += "Please upload financial documents for risk analysis."
        else:
            content += "I can help identify potential financial risks including:\n\n"
            content += "**Liquidity Risks:**\n"
            content += "• Low cash reserves\n"
            content += "• Poor working capital management\n"
            content += "• High short-term debt burden\n\n"
            
            content += "**Profitability Risks:**\n"
            content += "• Declining margins\n"
            content += "• Increasing costs\n"
            content += "• Revenue concentration\n\n"
            
            content += "**Leverage Risks:**\n"
            content += "• High debt levels\n"
            content += "• Poor interest coverage\n"
            content += "• Covenant violations\n\n"
            
            content += "Upload your financial statements for a detailed risk assessment."
        
        return AgentResponse(
            content=content,
            sources=list(documents.keys()),
            confidence=0.7
        )
    
    def _generate_trend_response(self, documents: Dict[str, Any]) -> AgentResponse:
        """Generate a trend analysis response."""
        content = "📈 **Trend Analysis**\n\n"
        
        if not documents:
            content += "Please upload multiple periods of financial data for trend analysis."
        else:
            content += "For comprehensive trend analysis, I can examine:\n\n"
            content += "**Revenue Trends:**\n"
            content += "• Growth rates over time\n"
            content += "• Seasonality patterns\n"
            content += "• Revenue mix changes\n\n"
            
            content += "**Profitability Trends:**\n"
            content += "• Margin evolution\n"
            content += "• Cost structure changes\n"
            content += "• Efficiency improvements\n\n"
            
            content += "**Balance Sheet Trends:**\n"
            content += "• Asset composition changes\n"
            content += "• Debt level evolution\n"
            content += "• Working capital trends\n\n"
            
            content += "Upload multiple years of financial data for detailed trend analysis."
        
        return AgentResponse(
            content=content,
            sources=list(documents.keys()),
            confidence=0.7
        )
    
    # Tool functions
    def _calculate_financial_metrics(self, query: str) -> str:
        """Calculate financial metrics based on the query."""
        try:
            if not hasattr(self, 'current_documents') or not self.current_documents:
                return "No documents loaded. Please upload financial documents to calculate metrics."
            
            # Search for common financial terms in the documents
            financial_terms = [
                'revenue', 'sales', 'income', 'profit', 'loss',
                'assets', 'liabilities', 'equity', 'cash',
                'debt', 'earnings', 'ebitda', 'net income'
            ]
            
            found_metrics = {}
            for doc_name, doc_data in self.current_documents.items():
                content = doc_data.get('content', '').lower()
                tables = doc_data.get('tables', [])
                
                for term in financial_terms:
                    if term in content:
                        # Find numerical values near the term
                        import re
                        pattern = rf'{term}[:\s]+[\$]?([0-9,]+\.?[0-9]*)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            found_metrics[term] = matches[:3]  # Keep first 3 matches
            
            if found_metrics:
                result = "Found these financial metrics in your documents:\n\n"
                for metric, values in found_metrics.items():
                    result += f"• {metric.title()}: {', '.join(values)}\n"
                return result
            else:
                return "I can analyze financial metrics from your documents. The document contains financial data, but specific metrics need to be extracted. Please ask specific questions about ratios, profitability, or financial performance."
                
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return f"Error calculating financial metrics: {str(e)}"
    
    def _analyze_trends(self, query: str) -> str:
        """Analyze financial trends."""
        try:
            if not hasattr(self, 'current_documents') or not self.current_documents:
                return "No documents loaded. Please upload financial documents to analyze trends."
            
            trend_indicators = []
            for doc_name, doc_data in self.current_documents.items():
                content = doc_data.get('content', '').lower()
                
                # Look for year-over-year comparisons and trend language
                trend_keywords = [
                    'increased', 'decreased', 'growth', 'decline', 'improved', 'declined',
                    'year over year', 'compared to', 'versus', 'from.*to', 'up.*%', 'down.*%'
                ]
                
                for keyword in trend_keywords:
                    import re
                    pattern = rf'[^.]*{keyword}[^.]*'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches[:2]:  # Limit to 2 per keyword
                        if len(match.strip()) > 20:  # Only meaningful sentences
                            trend_indicators.append(match.strip())
            
            if trend_indicators:
                result = "Found these trend indicators in your financial documents:\n\n"
                for i, indicator in enumerate(trend_indicators[:8], 1):  # Limit to 8 total
                    result += f"{i}. {indicator}\n\n"
                return result
            else:
                return "I can analyze trends from your financial documents. The documents contain financial data, but I need more specific trend-related queries to provide detailed analysis. Try asking about 'revenue growth' or 'year-over-year changes'."
                
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return f"Error analyzing trends: {str(e)}"
    
    def _assess_risks(self, query: str) -> str:
        """Assess financial risks."""
        try:
            if not hasattr(self, 'current_documents') or not self.current_documents:
                return "No documents loaded. Please upload financial documents to assess risks."
            
            risk_indicators = []
            for doc_name, doc_data in self.current_documents.items():
                content = doc_data.get('content', '').lower()
                
                # Look for risk-related keywords and phrases
                risk_keywords = [
                    'risk', 'loss', 'decline', 'decrease', 'concern', 'challenge',
                    'uncertainty', 'volatile', 'liability', 'debt', 'default',
                    'impairment', 'contingent', 'litigation', 'regulatory'
                ]
                
                for keyword in risk_keywords:
                    import re
                    # Find sentences containing risk keywords
                    sentences = content.split('.')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence.strip()) > 30:
                            risk_indicators.append(sentence.strip())
                            if len(risk_indicators) >= 10:  # Limit total findings
                                break
                    if len(risk_indicators) >= 10:
                        break
            
            if risk_indicators:
                result = "Found these potential risk indicators in your financial documents:\n\n"
                for i, indicator in enumerate(risk_indicators[:8], 1):  # Show top 8
                    result += f"{i}. {indicator}.\n\n"
                result += "\nNote: These are potential risk indicators found in the text. Professional financial analysis is recommended for comprehensive risk assessment."
                return result
            else:
                return "I've reviewed your financial documents for risk indicators. While I can identify potential concerns mentioned in the text, comprehensive risk analysis requires detailed financial ratio analysis and comparison with industry benchmarks."
                
        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
            return f"Error assessing risks: {str(e)}"
    
    def _search_documents(self, query: str) -> str:
        """Search for information in documents."""
        try:
            # Parse the query if it's JSON (from agent tool calling)
            if query.startswith('{'):
                import json
                query_data = json.loads(query)
                search_terms = query_data.get('query', [])
                document_name = query_data.get('document', '')
            else:
                # Direct string query
                search_terms = [query.lower()]
                document_name = ''
            
            if not hasattr(self, 'current_documents') or not self.current_documents:
                return "No documents are currently loaded. Please upload a financial document first."
            
            results = []
            total_content = ""
            
            # Search through all loaded documents
            for doc_name, doc_data in self.current_documents.items():
                if document_name and document_name not in doc_name:
                    continue
                    
                content = doc_data.get('content', '')
                tables = doc_data.get('tables', [])
                
                # Add all content for context
                total_content += f"\n--- Document: {doc_name} ---\n"
                total_content += content[:5000]  # First 5000 chars
                
                # Search for specific terms
                found_sections = []
                for term in search_terms:
                    if isinstance(term, str):
                        term_lower = term.lower()
                        content_lower = content.lower()
                        
                        # Find sentences containing the term
                        sentences = content.split('.')
                        for i, sentence in enumerate(sentences):
                            if term_lower in sentence.lower():
                                # Get some context around the found sentence
                                start_idx = max(0, i-1)
                                end_idx = min(len(sentences), i+2)
                                context = '. '.join(sentences[start_idx:end_idx]).strip()
                                if context and len(context) > 10:
                                    found_sections.append(f"Found '{term}': {context}")
                
                if found_sections:
                    results.extend(found_sections[:3])  # Limit to 3 results per term
            
            if results:
                response = f"Found the following relevant information:\n\n"
                response += "\n\n".join(results[:10])  # Limit total results
                response += f"\n\nDocument content summary: {total_content[:1000]}..."
                return response
            else:
                return f"No specific matches found for the search terms. However, I have access to the document content. Here's a summary: {total_content[:1500]}..."
                
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return f"Error searching documents: {str(e)}"
