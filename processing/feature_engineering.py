"""
Feature Engineering Framework

Comprehensive feature engineering pipeline for CSE stock prediction.
Generates technical indicators, fundamental ratios, sentiment features,
and macro-economic indicators for machine learning models.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from storage.feature_store import FeatureStore
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Main feature engineering class for CSE stock prediction.
    
    Orchestrates the creation of various feature types including
    technical indicators, fundamental ratios, and macro features.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize feature engineer.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.db_manager = get_db_manager(config)
        self.feature_store = FeatureStore(config)
        self.feature_config = config.get("features", {})
    
    def generate_features(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> None:
        """
        Generate all enabled features for specified symbols and date range.
        
        Args:
            symbols: List of stock symbols (if None, processes all symbols)
            start_date: Start date for feature generation
            end_date: End date for feature generation
        """
        logger.info("Starting feature generation process")
        
        if symbols is None:
            symbols = self._get_all_symbols()
        
        if start_date is None:
            start_date = date.today() - timedelta(days=365)  # 1 year default
        
        if end_date is None:
            end_date = date.today()
        
        # Generate different feature types based on configuration
        if self.feature_config.get("technical_indicators", True):
            self._generate_technical_features(symbols, start_date, end_date)
        
        if self.feature_config.get("fundamental_ratios", True):
            self._generate_fundamental_features(symbols, start_date, end_date)
        
        if self.feature_config.get("macro_features", True):
            self._generate_macro_features(symbols, start_date, end_date)
        
        if self.feature_config.get("sentiment_features", False):
            self._generate_sentiment_features(symbols, start_date, end_date)
        
        logger.info("Feature generation process completed")
    
    def _get_all_symbols(self) -> List[str]:
        """Get all available symbols from database."""
        sql = "SELECT DISTINCT symbol FROM companies WHERE status = 'active'"
        
        with self.db_manager.get_session() as session:
            result = session.execute(sql)
            symbols = [row[0] for row in result.fetchall()]
        
        return symbols
    
    def _generate_technical_features(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> None:
        """
        Generate technical indicator features.
        
        TODO: Implement comprehensive technical indicators
        Currently generates basic price-based features.
        """
        logger.info("Generating technical features")
        
        for symbol in symbols:
            try:
                # Get price data
                price_df = self._get_price_data(symbol, start_date, end_date)
                
                if price_df.empty:
                    logger.warning(f"No price data for {symbol}")
                    continue
                
                # Generate technical features
                features_df = self._calculate_technical_indicators(price_df)
                
                # Store features
                if not features_df.empty:
                    self.feature_store.store_features(features_df, "technical")
                
            except Exception as e:
                logger.error(f"Error generating technical features for {symbol}: {e}")
                continue
    
    def _calculate_technical_indicators(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators from price data.
        
        TODO: Implement comprehensive technical indicators
        Currently calculates basic moving averages and returns.
        """
        if price_df.empty:
            return pd.DataFrame()
        
        symbol = price_df.iloc[0]['symbol']
        price_df = price_df.sort_values('date').copy()
        
        features_list = []
        
        # Basic price features
        price_df['returns_1d'] = price_df['close_price'].pct_change()
        price_df['returns_5d'] = price_df['close_price'].pct_change(periods=5)
        price_df['returns_20d'] = price_df['close_price'].pct_change(periods=20)
        
        # Moving averages
        price_df['sma_5'] = price_df['close_price'].rolling(window=5).mean()
        price_df['sma_20'] = price_df['close_price'].rolling(window=20).mean()
        price_df['sma_50'] = price_df['close_price'].rolling(window=50).mean()
        
        # Price relative to moving averages
        price_df['price_vs_sma5'] = price_df['close_price'] / price_df['sma_5'] - 1
        price_df['price_vs_sma20'] = price_df['close_price'] / price_df['sma_20'] - 1
        
        # Volatility features
        price_df['volatility_5d'] = price_df['returns_1d'].rolling(window=5).std()
        price_df['volatility_20d'] = price_df['returns_1d'].rolling(window=20).std()
        
        # Volume features
        price_df['volume_sma_20'] = price_df['volume'].rolling(window=20).mean()
        price_df['volume_ratio'] = price_df['volume'] / price_df['volume_sma_20']
        
        # TODO: Add more sophisticated indicators
        # - RSI, MACD, Bollinger Bands
        # - Momentum indicators
        # - Support/resistance levels
        
        # Convert to long format for feature store
        feature_columns = [
            'returns_1d', 'returns_5d', 'returns_20d',
            'price_vs_sma5', 'price_vs_sma20',
            'volatility_5d', 'volatility_20d',
            'volume_ratio'
        ]
        
        for _, row in price_df.iterrows():
            for feature_name in feature_columns:
                feature_value = row.get(feature_name)
                if pd.notna(feature_value):
                    features_list.append({
                        'symbol': symbol,
                        'date': row['date'],
                        'feature_name': feature_name,
                        'feature_value': feature_value
                    })
        
        return pd.DataFrame(features_list)
    
    def _generate_fundamental_features(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> None:
        """
        Generate fundamental ratio features.
        
        TODO: Implement fundamental analysis features
        Currently placeholder implementation.
        """
        logger.warning("_generate_fundamental_features: Stub implementation")
        
        # TODO: Implement fundamental features:
        # - P/E ratio, P/B ratio, Debt/Equity
        # - ROE, ROA, Profit margins
        # - Revenue growth, earnings growth
        # - Dividend yield, payout ratio
        
        for symbol in symbols:
            # Placeholder: create empty fundamental features
            features_list = []
            
            # TODO: Get financial data and calculate ratios
            
            if features_list:
                features_df = pd.DataFrame(features_list)
                self.feature_store.store_features(features_df, "fundamental")
    
    def _generate_macro_features(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> None:
        """
        Generate macro-economic features.
        
        TODO: Implement macro features based on FX rates and indices
        Currently generates basic market features.
        """
        logger.info("Generating macro features")
        
        # Get market index data
        index_features = self._calculate_market_features(start_date, end_date)
        
        # Get FX rate features
        fx_features = self._calculate_fx_features(start_date, end_date)
        
        # Apply market features to all symbols
        for symbol in symbols:
            try:
                symbol_features = []
                
                # Add market features for this symbol
                for feature_dict in index_features:
                    symbol_features.append({
                        'symbol': symbol,
                        'date': feature_dict['date'],
                        'feature_name': feature_dict['feature_name'],
                        'feature_value': feature_dict['feature_value']
                    })
                
                # Add FX features for this symbol
                for feature_dict in fx_features:
                    symbol_features.append({
                        'symbol': symbol,
                        'date': feature_dict['date'],
                        'feature_name': feature_dict['feature_name'],
                        'feature_value': feature_dict['feature_value']
                    })
                
                if symbol_features:
                    features_df = pd.DataFrame(symbol_features)
                    self.feature_store.store_features(features_df, "macro")
                
            except Exception as e:
                logger.error(f"Error generating macro features for {symbol}: {e}")
                continue
    
    def _calculate_market_features(self, start_date: date, end_date: date) -> List[Dict]:
        """Calculate market-level features from indices."""
        features_list = []
        
        # TODO: Get actual index data and calculate features
        # For now, return empty list
        
        return features_list
    
    def _calculate_fx_features(self, start_date: date, end_date: date) -> List[Dict]:
        """Calculate FX-related features."""
        features_list = []
        
        # TODO: Get actual FX data and calculate features
        # For now, return empty list
        
        return features_list
    
    def _generate_sentiment_features(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> None:
        """
        Generate sentiment-based features.
        
        TODO: Implement sentiment analysis features
        Currently disabled by default.
        """
        logger.warning("_generate_sentiment_features: Not implemented yet")
        
        # TODO: Implement sentiment features:
        # - News sentiment scores
        # - Social media sentiment
        # - Analyst recommendations
        # - Insider trading activity
    
    def _get_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Get price data for a symbol."""
        sql = """
            SELECT symbol, date, open_price, high_price, low_price, 
                   close_price, volume, adjusted_close
            FROM prices
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """
        
        with self.db_manager.get_session() as session:
            result = session.execute(sql, (symbol, start_date, end_date))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        return df


def generate_features_for_prediction(
    symbols: List[str],
    as_of_date: date,
    config: Dict,
    lookback_days: int = 252
) -> pd.DataFrame:
    """
    Generate features for prediction as of a specific date.
    
    Args:
        symbols: List of stock symbols
        as_of_date: Date for feature calculation
        config: Configuration dictionary
        lookback_days: Number of days to look back for feature calculation
        
    Returns:
        DataFrame with features in wide format for model input
    """
    feature_store = FeatureStore(config)
    
    start_date = as_of_date - timedelta(days=lookback_days)
    
    # Get features from feature store
    features_df = feature_store.get_feature_matrix(
        symbols=symbols,
        start_date=start_date,
        end_date=as_of_date
    )
    
    if features_df.empty:
        logger.warning(f"No features found for prediction as of {as_of_date}")
        return pd.DataFrame()
    
    # Take the most recent features for each symbol
    latest_features = features_df.groupby('symbol').last()
    
    return latest_features


def create_target_variables(
    symbols: List[str],
    start_date: date,
    end_date: date,
    horizons: List[int],
    config: Dict
) -> pd.DataFrame:
    """
    Create target variables for model training.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for target creation
        end_date: End date for target creation
        horizons: List of prediction horizons in days
        config: Configuration dictionary
        
    Returns:
        DataFrame with target variables
    """
    logger.info(f"Creating target variables for {len(symbols)} symbols")
    
    db_manager = get_db_manager(config)
    targets_list = []
    
    for symbol in symbols:
        try:
            # Get price data with extra buffer for forward returns
            buffer_days = max(horizons) + 10
            extended_end = end_date + timedelta(days=buffer_days)
            
            sql = """
                SELECT date, adjusted_close
                FROM prices
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            
            with db_manager.get_session() as session:
                result = session.execute(sql, (symbol, start_date, extended_end))
                price_df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            if price_df.empty:
                continue
            
            price_df['date'] = pd.to_datetime(price_df['date'])
            price_df = price_df.set_index('date')
            
            # Calculate forward returns for each horizon
            for horizon in horizons:
                future_prices = price_df['adjusted_close'].shift(-horizon)
                forward_returns = (future_prices / price_df['adjusted_close']) - 1
                
                # Only keep targets within the original date range
                valid_dates = forward_returns.loc[start_date:end_date].dropna()
                
                for date_idx, target_value in valid_dates.items():
                    targets_list.append({
                        'symbol': symbol,
                        'date': date_idx.date(),
                        'horizon': horizon,
                        'target_return': target_value
                    })
        
        except Exception as e:
            logger.error(f"Error creating targets for {symbol}: {e}")
            continue
    
    targets_df = pd.DataFrame(targets_list)
    logger.info(f"Created {len(targets_df)} target records")
    
    return targets_df