-- CSE Stock Prediction Platform Database Schema
-- SQLite compatible with PostgreSQL migration path

-- Companies table: Core company information
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(20,2),
    listing_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price data table: Daily OHLCV data
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT DEFAULT 0,
    turnover DECIMAL(20,2) DEFAULT 0,
    trades_count INTEGER DEFAULT 0,
    adjusted_close DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Corporate actions table: Splits, bonuses, rights issues
CREATE TABLE IF NOT EXISTS corporate_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'split', 'bonus', 'rights', 'spin_off'
    announcement_date DATE NOT NULL,
    ex_date DATE,
    record_date DATE,
    payment_date DATE,
    ratio_numerator INTEGER,
    ratio_denominator INTEGER,
    description TEXT,
    adjustment_factor DECIMAL(10,6) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dividends table: Cash and stock dividends
CREATE TABLE IF NOT EXISTS dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    dividend_type VARCHAR(20) DEFAULT 'cash', -- 'cash', 'stock', 'interim', 'final'
    announcement_date DATE NOT NULL,
    ex_date DATE,
    record_date DATE,
    payment_date DATE,
    amount DECIMAL(10,4),
    currency VARCHAR(3) DEFAULT 'LKR',
    yield_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Corporate filings table: Annual reports, financial statements
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    filing_type VARCHAR(50) NOT NULL, -- 'annual_report', 'quarterly', 'interim'
    filing_date DATE NOT NULL,
    period_end DATE,
    title VARCHAR(500),
    description TEXT,
    file_url VARCHAR(1000),
    file_path VARCHAR(500),
    file_size BIGINT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial line items: Extracted from filings
CREATE TABLE IF NOT EXISTS financial_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    period_end DATE NOT NULL,
    line_item VARCHAR(100) NOT NULL, -- 'revenue', 'net_income', 'total_assets', etc.
    value DECIMAL(20,2),
    currency VARCHAR(3) DEFAULT 'LKR',
    unit VARCHAR(20) DEFAULT 'millions', -- 'thousands', 'millions', 'billions'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (filing_id) REFERENCES filings(id)
);

-- Market announcements: Price sensitive information
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    announcement_date DATE NOT NULL,
    time_published TIME,
    category VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(1000),
    sentiment_score DECIMAL(3,2), -- -1 to 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market indices: ASI, S&P SL20, etc.
CREATE TABLE IF NOT EXISTS indices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code VARCHAR(20) NOT NULL, -- 'ASI', 'SPL20', 'SPL'
    index_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    open_value DECIMAL(10,2),
    high_value DECIMAL(10,2),
    low_value DECIMAL(10,2),
    close_value DECIMAL(10,2),
    volume BIGINT DEFAULT 0,
    market_cap DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_code, date)
);

-- Foreign exchange rates: USD/LKR, EUR/LKR, etc.
CREATE TABLE IF NOT EXISTS fx_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_pair VARCHAR(10) NOT NULL, -- 'USD/LKR', 'EUR/LKR'
    date DATE NOT NULL,
    rate DECIMAL(10,4) NOT NULL,
    rate_type VARCHAR(20) DEFAULT 'spot', -- 'spot', 'forward'
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(currency_pair, date, rate_type)
);

-- Features table: Engineered features for modeling
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(15,6),
    feature_group VARCHAR(50), -- 'technical', 'fundamental', 'sentiment', 'macro'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, feature_name)
);

-- Model runs table: Track training runs and metadata
CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL, -- 'naive', 'lgbm', 'ensemble'
    horizon_days INTEGER NOT NULL, -- 1, 5, 20
    train_start_date DATE NOT NULL,
    train_end_date DATE NOT NULL,
    validation_start_date DATE,
    validation_end_date DATE,
    hyperparameters TEXT, -- JSON string
    feature_list TEXT, -- JSON array of feature names
    performance_metrics TEXT, -- JSON object
    model_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table: Model predictions
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    prediction_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    predicted_return DECIMAL(10,6),
    confidence_score DECIMAL(5,4), -- 0 to 1
    actual_return DECIMAL(10,6), -- filled in later for evaluation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES model_runs(run_id),
    UNIQUE(run_id, symbol, prediction_date, horizon_days)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON prices(symbol, date);
CREATE INDEX IF NOT EXISTS idx_corporate_actions_symbol_date ON corporate_actions(symbol, ex_date);
CREATE INDEX IF NOT EXISTS idx_dividends_symbol_date ON dividends(symbol, ex_date);
CREATE INDEX IF NOT EXISTS idx_filings_symbol_date ON filings(symbol, filing_date);
CREATE INDEX IF NOT EXISTS idx_financial_lines_symbol_period ON financial_lines(symbol, period_end);
CREATE INDEX IF NOT EXISTS idx_announcements_symbol_date ON announcements(symbol, announcement_date);
CREATE INDEX IF NOT EXISTS idx_indices_code_date ON indices(index_code, date);
CREATE INDEX IF NOT EXISTS idx_fx_rates_pair_date ON fx_rates(currency_pair, date);
CREATE INDEX IF NOT EXISTS idx_features_symbol_date ON features(symbol, date);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_date ON predictions(symbol, prediction_date);