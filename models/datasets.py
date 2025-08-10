"""
Dataset Preparation Utilities

Provides functions for preparing training and validation datasets
for machine learning models, including windowing, target creation,
and data splitting strategies.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from storage.feature_store import FeatureStore
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


def prepare_datasets(
    config: Dict,
    symbols: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    validation_split: float = 0.2
) -> Dict[str, Dict]:
    """
    Prepare training and validation datasets for model training.
    
    Args:
        config: Application configuration
        symbols: List of symbols to include (if None, uses all available)
        start_date: Start date for dataset
        end_date: End date for dataset
        validation_split: Fraction of data for validation
        
    Returns:
        Dictionary with 'train' and 'validation' datasets
    """
    logger.info("Preparing datasets for model training")
    
    if start_date is None:
        start_date = date.today() - timedelta(days=1000)  # ~3 years
    if end_date is None:
        end_date = date.today()
    
    # Calculate split date
    total_days = (end_date - start_date).days
    val_days = int(total_days * validation_split)
    split_date = end_date - timedelta(days=val_days)
    
    logger.info(f"Dataset split: train={start_date} to {split_date}, val={split_date} to {end_date}")
    
    # Prepare training dataset
    train_data = prepare_single_dataset(
        config, symbols, start_date, split_date, "train"
    )
    
    # Prepare validation dataset
    val_data = prepare_single_dataset(
        config, symbols, split_date, end_date, "validation"
    )
    
    return {
        "train": train_data,
        "validation": val_data
    }


def prepare_single_dataset(
    config: Dict,
    symbols: Optional[List[str]],
    start_date: date,
    end_date: date,
    dataset_name: str
) -> Dict:
    """
    Prepare a single dataset (train or validation).
    
    Args:
        config: Application configuration
        symbols: List of symbols
        start_date: Dataset start date
        end_date: Dataset end date
        dataset_name: Name for logging
        
    Returns:
        Dataset dictionary with features and targets
    """
    logger.info(f"Preparing {dataset_name} dataset: {start_date} to {end_date}")
    
    # Get feature data
    feature_store = FeatureStore(config)
    features_df = feature_store.get_feature_matrix(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get target data
    horizons = config.get("models", {}).get("prediction_horizons", [1, 5, 20])
    targets_df = create_targets_dataset(
        symbols or _get_all_symbols(config),
        start_date,
        end_date,
        horizons,
        config
    )
    
    # Align features and targets
    aligned_data = align_features_and_targets(features_df, targets_df)
    
    logger.info(f"{dataset_name} dataset prepared: {len(aligned_data)} samples")
    
    return {
        "features": aligned_data.get("features", pd.DataFrame()),
        "targets": aligned_data.get("targets", pd.DataFrame()),
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols,
        "dataset_name": dataset_name
    }


def create_targets_dataset(
    symbols: List[str],
    start_date: date,
    end_date: date,
    horizons: List[int],
    config: Dict
) -> pd.DataFrame:
    """
    Create target variables for all symbols and horizons.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date
        end_date: End date
        horizons: Prediction horizons
        config: Configuration
        
    Returns:
        DataFrame with target variables
    """
    logger.info(f"Creating targets for {len(symbols)} symbols and {len(horizons)} horizons")
    
    db_manager = get_db_manager(config)
    all_targets = []
    
    for symbol in symbols:
        try:
            # Get price data with buffer for forward returns
            buffer_days = max(horizons) + 30
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
                logger.warning(f"No price data for {symbol}")
                continue
            
            # Calculate forward returns
            symbol_targets = calculate_forward_returns(
                price_df, symbol, horizons, start_date, end_date
            )
            all_targets.append(symbol_targets)
            
        except Exception as e:
            logger.error(f"Error creating targets for {symbol}: {e}")
            continue
    
    if all_targets:
        targets_df = pd.concat(all_targets, ignore_index=True)
        logger.info(f"Created {len(targets_df)} target records")
        return targets_df
    else:
        return pd.DataFrame()


def calculate_forward_returns(
    price_df: pd.DataFrame,
    symbol: str,
    horizons: List[int],
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Calculate forward returns for multiple horizons.
    
    Args:
        price_df: Price data DataFrame
        symbol: Stock symbol
        horizons: List of forward return horizons
        start_date: Valid start date
        end_date: Valid end date
        
    Returns:
        DataFrame with forward returns
    """
    price_df['date'] = pd.to_datetime(price_df['date'])
    price_df = price_df.sort_values('date').set_index('date')
    
    targets_list = []
    
    for horizon in horizons:
        # Calculate forward returns
        future_prices = price_df['adjusted_close'].shift(-horizon)
        forward_returns = (future_prices / price_df['adjusted_close']) - 1
        
        # Filter to valid date range
        valid_returns = forward_returns.loc[
            (forward_returns.index.date >= start_date) & 
            (forward_returns.index.date <= end_date)
        ].dropna()
        
        for date_idx, return_value in valid_returns.items():
            targets_list.append({
                'symbol': symbol,
                'date': date_idx.date(),
                'horizon': horizon,
                'target_return': return_value
            })
    
    return pd.DataFrame(targets_list)


def align_features_and_targets(
    features_df: pd.DataFrame,
    targets_df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Align features and targets by symbol and date.
    
    Args:
        features_df: Features DataFrame (MultiIndex: symbol, date)
        targets_df: Targets DataFrame
        
    Returns:
        Dictionary with aligned features and targets
    """
    if features_df.empty or targets_df.empty:
        return {"features": pd.DataFrame(), "targets": pd.DataFrame()}
    
    # Reset index if features_df has MultiIndex
    if isinstance(features_df.index, pd.MultiIndex):
        features_df = features_df.reset_index()
    
    # Merge features and targets
    merged_df = pd.merge(
        features_df,
        targets_df,
        on=['symbol', 'date'],
        how='inner'
    )
    
    if merged_df.empty:
        logger.warning("No aligned features and targets found")
        return {"features": pd.DataFrame(), "targets": pd.DataFrame()}
    
    # Separate features and targets
    feature_columns = [col for col in merged_df.columns 
                      if col not in ['symbol', 'date', 'horizon', 'target_return']]
    
    aligned_features = merged_df[['symbol', 'date'] + feature_columns]
    aligned_targets = merged_df[['symbol', 'date', 'horizon', 'target_return']]
    
    logger.info(f"Aligned {len(aligned_features)} feature-target pairs")
    
    return {
        "features": aligned_features,
        "targets": aligned_targets
    }


def create_windowed_dataset(
    features_df: pd.DataFrame,
    targets_df: pd.DataFrame,
    window_size: int = 20,
    horizon: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create windowed dataset for sequence models.
    
    Args:
        features_df: Features DataFrame
        targets_df: Targets DataFrame
        window_size: Number of time steps in each window
        horizon: Target horizon
        
    Returns:
        Tuple of (X, y) arrays for sequence modeling
    """
    logger.info(f"Creating windowed dataset: window={window_size}, horizon={horizon}")
    
    # Filter targets for specific horizon
    horizon_targets = targets_df[targets_df['horizon'] == horizon]
    
    if horizon_targets.empty:
        return np.array([]), np.array([])
    
    X_windows = []
    y_values = []
    
    # Group by symbol
    symbols = features_df['symbol'].unique()
    
    for symbol in symbols:
        try:
            # Get symbol data
            symbol_features = features_df[features_df['symbol'] == symbol].sort_values('date')
            symbol_targets = horizon_targets[horizon_targets['symbol'] == symbol].sort_values('date')
            
            if len(symbol_features) < window_size:
                continue
            
            # Create windowed sequences
            feature_columns = [col for col in symbol_features.columns 
                             if col not in ['symbol', 'date']]
            feature_values = symbol_features[feature_columns].values
            
            # Create sliding windows
            for i in range(window_size, len(symbol_features)):
                window_features = feature_values[i-window_size:i]
                
                # Find corresponding target
                current_date = symbol_features.iloc[i]['date']
                target_row = symbol_targets[symbol_targets['date'] == current_date]
                
                if not target_row.empty:
                    X_windows.append(window_features)
                    y_values.append(target_row.iloc[0]['target_return'])
        
        except Exception as e:
            logger.error(f"Error creating windows for {symbol}: {e}")
            continue
    
    if X_windows:
        X = np.array(X_windows)
        y = np.array(y_values)
        logger.info(f"Created {len(X)} windowed samples")
        return X, y
    else:
        return np.array([]), np.array([])


def split_by_time(
    dataset: Dict,
    test_split: float = 0.2
) -> Tuple[Dict, Dict]:
    """
    Split dataset by time (temporal split).
    
    Args:
        dataset: Dataset dictionary
        test_split: Fraction for test set
        
    Returns:
        Tuple of (train_dataset, test_dataset)
    """
    features_df = dataset["features"]
    targets_df = dataset["targets"]
    
    if features_df.empty:
        return dataset, {"features": pd.DataFrame(), "targets": pd.DataFrame()}
    
    # Find split date
    all_dates = sorted(features_df['date'].unique())
    split_idx = int(len(all_dates) * (1 - test_split))
    split_date = all_dates[split_idx]
    
    # Split features
    train_features = features_df[features_df['date'] < split_date]
    test_features = features_df[features_df['date'] >= split_date]
    
    # Split targets
    train_targets = targets_df[targets_df['date'] < split_date]
    test_targets = targets_df[targets_df['date'] >= split_date]
    
    train_dataset = {
        **dataset,
        "features": train_features,
        "targets": train_targets
    }
    
    test_dataset = {
        **dataset,
        "features": test_features,
        "targets": test_targets
    }
    
    logger.info(f"Time split: train={len(train_features)}, test={len(test_features)}")
    
    return train_dataset, test_dataset


def get_dataset_stats(dataset: Dict) -> Dict:
    """
    Get statistics about a dataset.
    
    Args:
        dataset: Dataset dictionary
        
    Returns:
        Dictionary with dataset statistics
    """
    features_df = dataset.get("features", pd.DataFrame())
    targets_df = dataset.get("targets", pd.DataFrame())
    
    if features_df.empty:
        return {"num_samples": 0}
    
    stats = {
        "num_samples": len(features_df),
        "num_features": len([col for col in features_df.columns 
                           if col not in ['symbol', 'date']]),
        "num_symbols": features_df['symbol'].nunique(),
        "date_range": {
            "start": features_df['date'].min(),
            "end": features_df['date'].max()
        }
    }
    
    if not targets_df.empty:
        stats.update({
            "num_targets": len(targets_df),
            "horizons": sorted(targets_df['horizon'].unique()),
            "target_stats": {
                "mean": targets_df['target_return'].mean(),
                "std": targets_df['target_return'].std(),
                "min": targets_df['target_return'].min(),
                "max": targets_df['target_return'].max()
            }
        })
    
    return stats


def _get_all_symbols(config: Dict) -> List[str]:
    """Get all available symbols from database."""
    db_manager = get_db_manager(config)
    
    sql = "SELECT DISTINCT symbol FROM companies WHERE status = 'active'"
    
    with db_manager.get_session() as session:
        result = session.execute(sql)
        symbols = [row[0] for row in result.fetchall()]
    
    return symbols