# CSE Stock Prediction Platform

An agentic AI system for predicting stock returns on the Colombo Stock Exchange (CSE) using machine learning and financial data analysis.

⚠️ **DISCLAIMER**: This software is for educational and research purposes only. It is NOT investment advice. Trading stocks involves substantial risk of loss. Always consult with qualified financial professionals before making investment decisions.

## Introduction

This platform provides a comprehensive framework for predicting stock returns on the Colombo Stock Exchange using:

- **Multi-source Data Integration**: Price data, corporate actions, dividends, financial filings, market indices, and FX rates
- **Advanced Feature Engineering**: Technical indicators, fundamental ratios, and macro-economic features  
- **Machine Learning Models**: Naive baselines, LightGBM, and ensemble methods
- **Agentic AI Layer**: Tool-based agents for prediction, explanation, and scenario analysis
- **Robust Infrastructure**: SQLite storage, caching, rate limiting, and comprehensive logging

## Architecture Overview

The platform follows a modular architecture with clear separation of concerns:

```
CSE Stock Prediction Platform
│
├── Data Sources Layer
│   ├── Stock prices (OHLCV)
│   ├── Corporate actions (splits, bonuses, rights)
│   ├── Dividends and distributions
│   ├── Company filings and financial statements
│   ├── Market disclosures and announcements
│   ├── Market indices (ASI, S&P SL20)
│   └── Foreign exchange rates
│
├── Storage Layer
│   ├── SQLite database with 11 core tables
│   ├── Feature store for ML features
│   └── Caching system for performance
│
├── Processing Layer
│   ├── Price adjustments for corporate actions
│   ├── Financial ratio calculations
│   └── Feature engineering pipeline
│
├── Modeling Layer
│   ├── Naive baseline models
│   ├── LightGBM regression models
│   └── Ensemble methods with uncertainty
│
├── Agent Layer
│   ├── Tool registry for agent capabilities
│   ├── Prediction agents
│   ├── Explanation agents
│   └── Scenario analysis agents
│
└── Evaluation Layer
    ├── Performance metrics
    └── Backtesting framework
```

## Directory Structure

```
├── config.yaml                 # Global configuration
├── requirements.txt            # Python dependencies
├── run_pipeline.py            # Main CLI entry point
├── LICENSE                    # MIT License
│
├── data_sources/              # Data fetching modules
│   ├── cse_symbol_list.py     # Company listings
│   ├── prices.py              # OHLCV price data
│   ├── corporate_actions.py   # Splits, bonuses, rights
│   ├── dividends.py           # Dividend payments
│   ├── disclosures.py         # Market announcements
│   ├── filings.py             # Financial statements
│   ├── indices.py             # Market indices
│   └── fx_rates.py            # Currency exchange rates
│
├── storage/                   # Data persistence
│   ├── schema.sql             # Database schema (11 tables)
│   ├── db.py                  # Database connection manager
│   └── feature_store.py       # ML feature management
│
├── processing/                # Data transformation
│   ├── adjust_prices.py       # Corporate action adjustments
│   ├── fundamentals_normalizer.py  # Financial ratio calculations
│   ├── ratios.py              # Financial ratios
│   └── feature_engineering.py # Feature pipeline
│
├── models/                    # Machine learning models
│   ├── baseline_naive.py      # Naive prediction baselines
│   ├── lgbm_regressor.py      # LightGBM models
│   ├── ensemble.py            # Ensemble methods
│   └── datasets.py            # Dataset preparation
│
├── agents/                    # AI agent layer
│   ├── tool_registry.py       # Agent tool definitions
│   ├── prediction_agent.py    # Prediction orchestration
│   ├── explanation_agent.py   # Result explanation
│   └── scenario_agent.py      # Scenario analysis
│
├── evaluation/                # Model evaluation
│   ├── metrics.py             # Performance metrics
│   └── backtest.py            # Backtesting framework
│
├── embeddings/                # Vector search (future)
│   ├── index_builder.py       # Embedding index creation
│   └── retrieval.py           # Semantic search
│
└── utils/                     # Utility functions
    ├── logging_setup.py       # Structured logging
    ├── cache.py               # Caching utilities
    ├── throttling.py          # Rate limiting
    └── time_utils.py          # Date/time operations
```

## Data Pipeline Stages

### 1. Data Ingestion
- **Symbol Discovery**: Fetch active companies from CSE
- **Price Data**: Historical OHLCV data with volume and turnover
- **Corporate Actions**: Stock splits, bonus issues, rights offerings
- **Dividends**: Cash and stock dividend announcements
- **Financial Filings**: Annual reports, quarterly statements
- **Market Data**: Indices, announcements, FX rates

### 2. Data Processing
- **Price Adjustments**: Normalize prices for corporate actions
- **Data Validation**: Quality checks and outlier detection
- **Missing Data**: Interpolation and forward-filling strategies

### 3. Feature Engineering
- **Technical Indicators**: Moving averages, momentum, volatility
- **Fundamental Ratios**: P/E, P/B, ROE, debt ratios
- **Macro Features**: Market indices, FX rates, sector performance
- **Sentiment Features**: News sentiment, analyst recommendations (future)

### 4. Model Training
- **Target Creation**: Forward returns (1-day, 5-day, 20-day)
- **Cross-Validation**: Time-series aware validation splits
- **Model Selection**: Hyperparameter optimization
- **Ensemble Training**: Multiple model combination

## Modeling Approach

### Prediction Targets
- **1-day forward returns**: Short-term momentum/mean-reversion
- **5-day forward returns**: Weekly trend prediction
- **20-day forward returns**: Monthly performance forecasting

### Model Types

#### 1. Naive Baselines
- **Momentum**: Recent trends continue
- **Mean Reversion**: Prices revert to historical mean
- **Random Walk**: No predictability assumption
- **Historical Mean**: Long-term average returns

#### 2. LightGBM Models
- **Gradient Boosting**: Non-linear feature interactions
- **Feature Importance**: Interpretable model insights
- **Early Stopping**: Prevents overfitting
- **Cross-Validation**: Robust model selection

#### 3. Ensemble Methods
- **Weighted Averaging**: Combine multiple models
- **Uncertainty Quantification**: Prediction confidence intervals
- **Dynamic Weighting**: Adaptive model weights based on performance

### Feature Categories
- **Price-Based**: Returns, volatility, moving averages
- **Volume-Based**: Trading activity, turnover ratios
- **Fundamental**: Financial ratios, growth metrics
- **Market-Wide**: Index performance, sector rotation
- **Macro-Economic**: FX rates, interest rates

## Agent Layer

### Tool Registry
Central registry of agent capabilities:
- **Data Retrieval**: Get price, fundamental, and market data
- **Feature Calculation**: Generate technical and fundamental features
- **Model Prediction**: Execute trained models
- **Performance Analysis**: Calculate metrics and statistics

### Agent Types

#### Prediction Agent
- **Multi-Horizon Forecasting**: 1-day, 5-day, 20-day predictions
- **Ensemble Coordination**: Combine multiple model outputs
- **Uncertainty Estimation**: Confidence intervals and risk metrics

#### Explanation Agent
- **Feature Attribution**: Which factors drive predictions
- **Model Interpretation**: How models make decisions
- **Historical Context**: Compare with past performance

#### Scenario Agent
- **Stress Testing**: Performance under market stress
- **Sensitivity Analysis**: Impact of parameter changes
- **What-If Analysis**: Hypothetical scenario modeling

## Setup

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd AgenticFinancialAnalyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy and edit configuration
cp config.yaml config.local.yaml
# Edit config.local.yaml with your settings

# Set up environment variables (optional)
cp .env.example .env
# Edit .env with API keys if needed
```

### 3. Database Initialization
```bash
# Initialize database schema
python -c "
from storage.db import init_database
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
init_database(config)
"
```

### 4. Basic Usage
```bash
# Run data ingestion
python run_pipeline.py --tasks ingest

# Generate features
python run_pipeline.py --tasks features

# Train models
python run_pipeline.py --tasks train

# Generate predictions
python run_pipeline.py --tasks predict --symbols DIAL,JKH,COMB
```

## Usage Examples

### Data Ingestion
```python
from data_sources.prices import fetch_and_store_prices
from datetime import date, timedelta
import yaml

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Fetch price data for major stocks
symbols = ['DIAL', 'JKH', 'COMB', 'SAMP']
end_date = date.today()
start_date = end_date - timedelta(days=365)

fetch_and_store_prices(symbols, start_date, end_date, config)
```

### Feature Engineering
```python
from processing.feature_engineering import FeatureEngineer

# Initialize feature engineer
engineer = FeatureEngineer(config)

# Generate features for specific symbols
engineer.generate_features(
    symbols=['DIAL', 'JKH'],
    start_date=start_date,
    end_date=end_date
)
```

### Model Training
```python
from models.ensemble import create_production_ensemble
from models.datasets import prepare_datasets

# Prepare training data
datasets = prepare_datasets(config)

# Create and train ensemble
ensemble = create_production_ensemble(config)
results = ensemble.train(datasets['train'], datasets['validation'])

# Generate predictions
predictions = ensemble.predict(['DIAL', 'JKH'])
```

## Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Database schema and storage layer
- [x] Data source integration framework
- [x] Feature engineering pipeline
- [x] Baseline modeling framework
- [x] Configuration and logging systems

### Phase 2: Data Integration (In Progress)
- [ ] CSE website scraping implementation
- [ ] Financial statement parsing
- [ ] Real-time data feeds
- [ ] Data quality monitoring
- [ ] Historical data backfill

### Phase 3: Advanced Modeling
- [ ] Deep learning models (LSTM, Transformer)
- [ ] Hyperparameter optimization
- [ ] Model ensembling strategies
- [ ] Cross-validation frameworks
- [ ] Feature selection algorithms

### Phase 4: Agent Enhancement
- [ ] LLM integration for natural language queries
- [ ] Advanced explanation capabilities
- [ ] Interactive scenario planning
- [ ] Automated report generation
- [ ] Risk management tools

### Phase 5: Production Deployment
- [ ] API development
- [ ] Web dashboard
- [ ] Real-time prediction serving
- [ ] Model monitoring and retraining
- [ ] Performance analytics

### Phase 6: Advanced Features
- [ ] Multi-asset portfolio optimization
- [ ] Alternative data integration
- [ ] Sentiment analysis from news/social media
- [ ] Market regime detection
- [ ] Factor attribution analysis

## Configuration

Key configuration options in `config.yaml`:

```yaml
# Database settings
database:
  uri: "sqlite:///data/agenticfa.db"
  
# Model parameters
models:
  prediction_horizons: [1, 5, 20]
  train_window_days: 252
  validation_split: 0.2
  
# Feature engineering
features:
  technical_indicators: true
  fundamental_ratios: true
  macro_features: true
  
# Data sources
data_sources:
  throttle_delay: 1.0
  timeout: 30
```

## Performance Metrics

The platform tracks multiple performance metrics:

- **Directional Accuracy**: Percentage of correct directional predictions
- **Root Mean Square Error (RMSE)**: Prediction accuracy measure
- **Spearman Rank Correlation**: Rank-based correlation with actual returns
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown**: Worst peak-to-trough loss
- **Information Ratio**: Active return per unit of active risk

## Risk Management

### Model Risk
- **Overfitting Prevention**: Cross-validation and regularization
- **Concept Drift Detection**: Monitor model performance over time
- **Ensemble Diversity**: Multiple uncorrelated models
- **Uncertainty Quantification**: Confidence intervals on predictions

### Data Risk
- **Quality Monitoring**: Automated data validation
- **Survivorship Bias**: Include delisted stocks in analysis
- **Look-Ahead Bias**: Strict temporal data splits
- **Corporate Action Handling**: Proper price adjustments

### Operational Risk
- **Model Versioning**: Track model changes and performance
- **Fallback Strategies**: Graceful degradation when models fail
- **Performance Monitoring**: Real-time model health checks
- **Alert Systems**: Notification of anomalies or failures

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new functionality
- Update documentation for significant changes
- Use type hints for function parameters

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**IMPORTANT DISCLAIMER**: This software is provided for educational and research purposes only. It is NOT intended as investment advice, financial guidance, or trading recommendations. 

- **No Investment Advice**: The predictions and analysis generated by this software should not be used as the sole basis for investment decisions
- **High Risk**: Stock trading involves substantial risk of loss and is not suitable for all investors
- **No Guarantees**: Past performance does not guarantee future results
- **Professional Advice**: Always consult with qualified financial professionals before making investment decisions
- **Use at Your Own Risk**: Users assume full responsibility for any financial losses resulting from the use of this software

The developers and contributors of this project are not licensed financial advisors and do not provide investment advice. Any financial decisions made based on this software are solely the responsibility of the user.

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Review the documentation
- Check existing discussions and FAQs

---

*Built with ❤️ for the Sri Lankan financial technology community*
