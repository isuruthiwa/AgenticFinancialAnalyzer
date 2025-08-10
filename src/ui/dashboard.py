"""
Dashboard component for the Agentic Financial Analyzer.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional
import numpy as np

from src.processors.document_processor import DocumentProcessor
from src.analysis.financial_analyzer import FinancialAnalyzer
from src.utils.logger import logger

class Dashboard:
    """Financial analytics dashboard component."""
    
    def __init__(self, uploaded_files: List[Any], config: Any):
        """Initialize dashboard."""
        self.uploaded_files = uploaded_files or []
        self.config = config
        self.processor = DocumentProcessor(config)
        self.analyzer = FinancialAnalyzer(config)
        
        # Initialize session state for dashboard data
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = {}
    
    def render(self):
        """Render the dashboard."""
        if not self.uploaded_files:
            self._render_empty_state()
            return
        
        # Process files if not already done
        if not st.session_state.dashboard_data:
            self._process_files_for_dashboard()
        
        # Render dashboard sections
        self._render_overview_metrics()
        self._render_financial_charts()
        self._render_detailed_analysis()
    
    def _render_empty_state(self):
        """Render empty state when no files are uploaded."""
        st.info("📁 Upload financial documents to see analytics dashboard")
        
        # Show demo/sample dashboard
        st.subheader("📊 Sample Dashboard")
        st.write("This is what your dashboard will look like once you upload financial documents:")
        
        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Revenue", "$12.5M", "+15.3%")
        
        with col2:
            st.metric("Net Income", "$2.1M", "+8.7%")
        
        with col3:
            st.metric("ROE", "18.4%", "+2.1%")
        
        with col4:
            st.metric("Debt Ratio", "0.35", "-0.05")
        
        # Sample chart
        dates = pd.date_range('2020-01-01', periods=36, freq='M')
        sample_data = pd.DataFrame({
            'Date': dates,
            'Revenue': np.random.normal(10000000, 1000000, 36).cumsum() / 36 + 8000000,
            'Net Income': np.random.normal(1500000, 200000, 36).cumsum() / 36 + 1200000
        })
        
        fig = px.line(sample_data, x='Date', y=['Revenue', 'Net Income'],
                     title='Sample Financial Trends')
        st.plotly_chart(fig, use_container_width=True)
    
    def _process_files_for_dashboard(self):
        """Process uploaded files for dashboard analytics."""
        with st.spinner("Processing files for dashboard analytics..."):
            dashboard_data = {}
            
        for file in self.uploaded_files:
            try:
                # Check if file is already processed in session state
                if file.name in st.session_state.get('processed_documents', {}):
                    processed_data = st.session_state.processed_documents[file.name]
                    logger.info(f"Using cached data for {file.name}")
                else:
                    # Process document
                    processed_data = self.processor.process_file(file)
                    
                    # Cache the processed data
                    if 'processed_documents' not in st.session_state:
                        st.session_state.processed_documents = {}
                    st.session_state.processed_documents[file.name] = processed_data
                
                # Analyze financial metrics
                analysis = self.analyzer.analyze_document(processed_data)
                
                dashboard_data[file.name] = {
                    'processed_data': processed_data,
                    'analysis': analysis
                }
                
            except Exception as e:
                logger.error(f"Error processing {file.name} for dashboard: {e}")
                st.error(f"Error processing {file.name}: {str(e)}")
        
        st.session_state.dashboard_data = dashboard_data
    
    def _render_overview_metrics(self):
        """Render key financial metrics overview."""
        st.subheader("📊 Key Financial Metrics")
        
        # Aggregate metrics from all documents
        metrics = self._aggregate_metrics()
        
        if not metrics:
            st.warning("No financial metrics found in uploaded documents.")
            return
        
        # Display metrics in columns
        cols = st.columns(len(metrics))
        
        for i, (metric_name, metric_data) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(
                    label=metric_name,
                    value=metric_data.get('value', 'N/A'),
                    delta=metric_data.get('change', None)
                )
    
    def _render_financial_charts(self):
        """Render financial charts and visualizations."""
        st.subheader("📈 Financial Visualizations")
        
        # Create tabs for different chart types
        tab1, tab2, tab3 = st.tabs(["Trends", "Ratios", "Composition"])
        
        with tab1:
            self._render_trend_charts()
        
        with tab2:
            self._render_ratio_charts()
        
        with tab3:
            self._render_composition_charts()
    
    def _render_trend_charts(self):
        """Render trend analysis charts."""
        trend_data = self._get_trend_data()
        
        if trend_data.empty:
            st.info("No trend data available. Upload multiple periods of financial data to see trends.")
            return
        
        # Revenue and profit trends
        fig = px.line(
            trend_data,
            x='Period',
            y=['Revenue', 'Net Income', 'Operating Income'],
            title='Revenue and Profitability Trends',
            labels={'value': 'Amount ($)', 'variable': 'Metric'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth rates
        if len(trend_data) > 1:
            growth_data = self._calculate_growth_rates(trend_data)
            
            fig_growth = px.bar(
                growth_data,
                x='Period',
                y=['Revenue Growth', 'Income Growth'],
                title='Year-over-Year Growth Rates',
                labels={'value': 'Growth Rate (%)', 'variable': 'Metric'}
            )
            st.plotly_chart(fig_growth, use_container_width=True)
    
    def _render_ratio_charts(self):
        """Render financial ratio charts."""
        ratio_data = self._get_ratio_data()
        
        if not ratio_data:
            st.info("No ratio data available. Upload complete financial statements to see ratios.")
            return
        
        # Profitability ratios
        col1, col2 = st.columns(2)
        
        with col1:
            profitability_ratios = {k: v for k, v in ratio_data.items() 
                                  if 'margin' in k.lower() or 'roe' in k.lower() or 'roa' in k.lower()}
            
            if profitability_ratios:
                fig = go.Figure(data=go.Bar(
                    x=list(profitability_ratios.keys()),
                    y=list(profitability_ratios.values()),
                    marker_color='lightblue'
                ))
                fig.update_layout(title='Profitability Ratios', yaxis_title='Ratio')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            liquidity_ratios = {k: v for k, v in ratio_data.items() 
                              if 'ratio' in k.lower() and 'debt' not in k.lower()}
            
            if liquidity_ratios:
                fig = go.Figure(data=go.Bar(
                    x=list(liquidity_ratios.keys()),
                    y=list(liquidity_ratios.values()),
                    marker_color='lightgreen'
                ))
                fig.update_layout(title='Liquidity Ratios', yaxis_title='Ratio')
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_composition_charts(self):
        """Render composition and breakdown charts."""
        composition_data = self._get_composition_data()
        
        if not composition_data:
            st.info("No composition data available.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue breakdown
            if 'revenue_breakdown' in composition_data:
                revenue_data = composition_data['revenue_breakdown']
                fig = px.pie(
                    values=list(revenue_data.values()),
                    names=list(revenue_data.keys()),
                    title='Revenue Breakdown'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Expense breakdown
            if 'expense_breakdown' in composition_data:
                expense_data = composition_data['expense_breakdown']
                fig = px.pie(
                    values=list(expense_data.values()),
                    names=list(expense_data.keys()),
                    title='Expense Breakdown'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_analysis(self):
        """Render detailed financial analysis section."""
        st.subheader("🔍 Detailed Analysis")
        
        # Analysis summary
        analysis_summary = self._get_analysis_summary()
        
        if analysis_summary:
            st.write("**Key Insights:**")
            for insight in analysis_summary.get('insights', []):
                st.write(f"• {insight}")
            
            if analysis_summary.get('recommendations'):
                st.write("**Recommendations:**")
                for rec in analysis_summary['recommendations']:
                    st.write(f"• {rec}")
        
        # Data tables
        with st.expander("📋 Raw Financial Data"):
            self._render_data_tables()
    
    def _render_data_tables(self):
        """Render data tables with financial information."""
        for file_name, data in st.session_state.dashboard_data.items():
            st.write(f"**{file_name}**")
            
            # Display extracted data as tables
            if 'tables' in data['processed_data']:
                for i, table in enumerate(data['processed_data']['tables']):
                    st.write(f"Table {i+1}:")
                    
                    # Fix duplicate column names
                    if hasattr(table, 'columns'):
                        cols = table.columns.tolist()
                        # Make column names unique by adding suffixes
                        seen = {}
                        new_cols = []
                        for col in cols:
                            if col in seen:
                                seen[col] += 1
                                new_cols.append(f"{col}_{seen[col]}")
                            else:
                                seen[col] = 0
                                new_cols.append(col)
                        table.columns = new_cols
                    
                    st.dataframe(table, use_container_width=True)
    
    def _aggregate_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate key metrics from all processed documents."""
        # Placeholder implementation
        return {
            "Revenue": {"value": "$12.5M", "change": "+15.3%"},
            "Net Income": {"value": "$2.1M", "change": "+8.7%"},
            "ROE": {"value": "18.4%", "change": "+2.1%"},
            "Current Ratio": {"value": "2.3", "change": "+0.2"}
        }
    
    def _get_trend_data(self) -> pd.DataFrame:
        """Get trend data for charts."""
        # Placeholder implementation
        return pd.DataFrame()
    
    def _get_ratio_data(self) -> Dict[str, float]:
        """Get financial ratio data."""
        # Placeholder implementation
        return {
            "Gross Margin": 0.45,
            "Operating Margin": 0.18,
            "Net Margin": 0.12,
            "ROE": 0.184,
            "ROA": 0.098,
            "Current Ratio": 2.3,
            "Quick Ratio": 1.8
        }
    
    def _get_composition_data(self) -> Dict[str, Dict[str, float]]:
        """Get composition data for pie charts."""
        # Placeholder implementation
        return {
            "revenue_breakdown": {
                "Product Sales": 8500000,
                "Services": 2800000,
                "Licensing": 1200000
            },
            "expense_breakdown": {
                "COGS": 6200000,
                "Operating Expenses": 3800000,
                "Interest": 300000,
                "Taxes": 700000
            }
        }
    
    def _get_analysis_summary(self) -> Dict[str, List[str]]:
        """Get analysis summary and insights."""
        # Placeholder implementation
        return {
            "insights": [
                "Revenue growth has accelerated in the last quarter",
                "Operating margins are improving due to cost optimization",
                "Strong balance sheet with low debt levels",
                "Cash flow generation is robust and consistent"
            ],
            "recommendations": [
                "Consider increasing investment in high-growth segments",
                "Monitor working capital management closely",
                "Evaluate opportunities for strategic acquisitions",
                "Maintain current dividend policy given strong cash position"
            ]
        }
    
    def _calculate_growth_rates(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate growth rates from trend data."""
        # Placeholder implementation
        return pd.DataFrame()
