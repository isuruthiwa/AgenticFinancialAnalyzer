# Agentic Financial Analyzer

An intelligent AI-powered system for analyzing financial reports and providing comprehensive insights from company data. The system supports multiple document formats (PDF, Word, Images) and provides both chat interface and dashboard for interaction.

## Features

- **Multi-format Document Processing**: Supports PDF, Word documents, and images
- **AI-Powered Analysis**: Uses advanced LLMs for intelligent financial data interpretation
- **Interactive Chat Interface**: Natural language queries about financial data
- **Comprehensive Dashboard**: Visual analytics and insights dashboard
- **Historical Data Integration**: Combines current reports with historical company data
- **Automated Insights**: Generates actionable financial insights and recommendations

## Architecture

```
src/
├── agents/           # AI agent implementations
├── processors/       # Document processing modules
├── analysis/         # Financial analysis engines
├── ui/              # User interface components
├── data/            # Data management and storage
└── utils/           # Utility functions
```

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AgenticFinancialAnalyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   streamlit run src/main.py
   ```

## Configuration

Set up your environment variables in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional)
- `DATABASE_URL`: Database connection string
- `VECTOR_DB_PATH`: Path for vector database storage

## Usage

### Document Upload
- Drag and drop PDF, Word, or image files
- The system automatically extracts and processes financial data
- Multiple files can be uploaded for comprehensive analysis

### Chat Interface
- Ask natural language questions about the financial data
- Get explanations of financial metrics and trends
- Request specific analysis or comparisons

### Dashboard
- View key financial metrics and KPIs
- Interactive charts and visualizations
- Historical trend analysis
- Comparative analysis with industry benchmarks

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Project Structure
- `src/main.py`: Main Streamlit application entry point
- `src/agents/`: AI agent implementations for different analysis tasks
- `src/processors/`: Document processing and data extraction
- `src/analysis/`: Financial analysis and calculation engines
- `src/ui/`: UI components and pages
- `src/data/`: Data models and database interactions
- `src/utils/`: Shared utility functions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License
