"""
Feature store for managing engineered features.

Provides high-level interface for storing, retrieving, and managing
feature data for machine learning models in the CSE prediction platform.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db_manager

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    High-level interface for feature storage and retrieval.
    
    Manages feature engineering results, feature metadata, and provides
    efficient access patterns for model training and inference.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize feature store.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.db_manager = get_db_manager(config)
    
    def store_features(
        self,
        features_df: pd.DataFrame,
        feature_group: str,
        overwrite: bool = False
    ) -> None:
        """
        Store engineered features in the database.
        
        Args:
            features_df: DataFrame with columns ['symbol', 'date', feature_names...]
            feature_group: Feature group identifier ('technical', 'fundamental', etc.)
            overwrite: Whether to overwrite existing features
        """
        if features_df.empty:
            logger.warning("Empty features DataFrame provided")
            return
        
        required_cols = ['symbol', 'date']
        missing_cols = [col for col in required_cols if col not in features_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        feature_cols = [col for col in features_df.columns if col not in required_cols]
        
        logger.info(f"Storing {len(features_df)} feature records for group: {feature_group}")
        
        with self.db_manager.get_session() as session:
            try:
                for _, row in features_df.iterrows():
                    symbol = row['symbol']
                    feature_date = row['date']
                    
                    for feature_name in feature_cols:
                        feature_value = row[feature_name]
                        
                        # Skip NaN values
                        if pd.isna(feature_value):
                            continue
                        
                        # Check if feature already exists
                        if not overwrite:
                            existing = session.execute(
                                text("""
                                    SELECT id FROM features 
                                    WHERE symbol = :symbol 
                                    AND date = :date 
                                    AND feature_name = :feature_name
                                """),
                                {
                                    "symbol": symbol,
                                    "date": feature_date,
                                    "feature_name": feature_name
                                }
                            ).fetchone()
                            
                            if existing:
                                continue
                        
                        # Insert or update feature
                        session.execute(
                            text("""
                                INSERT OR REPLACE INTO features 
                                (symbol, date, feature_name, feature_value, feature_group)
                                VALUES (:symbol, :date, :feature_name, :feature_value, :feature_group)
                            """),
                            {
                                "symbol": symbol,
                                "date": feature_date,
                                "feature_name": feature_name,
                                "feature_value": float(feature_value),
                                "feature_group": feature_group
                            }
                        )
                
                session.commit()
                logger.info(f"Successfully stored features for group: {feature_group}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error storing features: {e}")
                raise
    
    def get_features(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        feature_groups: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve features from the database.
        
        Args:
            symbols: List of stock symbols to filter by
            start_date: Start date for feature retrieval
            end_date: End date for feature retrieval
            feature_groups: List of feature groups to include
            feature_names: Specific feature names to retrieve
            
        Returns:
            DataFrame with features in long format
        """
        conditions = []
        params = {}
        
        if symbols:
            placeholders = [f":symbol_{i}" for i in range(len(symbols))]
            conditions.append(f"symbol IN ({','.join(placeholders)})")
            for i, symbol in enumerate(symbols):
                params[f"symbol_{i}"] = symbol
        
        if start_date:
            conditions.append("date >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("date <= :end_date")
            params["end_date"] = end_date
        
        if feature_groups:
            placeholders = [f":group_{i}" for i in range(len(feature_groups))]
            conditions.append(f"feature_group IN ({','.join(placeholders)})")
            for i, group in enumerate(feature_groups):
                params[f"group_{i}"] = group
        
        if feature_names:
            placeholders = [f":name_{i}" for i in range(len(feature_names))]
            conditions.append(f"feature_name IN ({','.join(placeholders)})")
            for i, name in enumerate(feature_names):
                params[f"name_{i}"] = name
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT symbol, date, feature_name, feature_value, feature_group
            FROM features
            WHERE {where_clause}
            ORDER BY symbol, date, feature_name
        """
        
        with self.db_manager.get_session() as session:
            result = session.execute(text(sql), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        return df
    
    def get_feature_matrix(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        feature_groups: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get features in wide format suitable for model training.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for features
            end_date: End date for features
            feature_groups: Feature groups to include
            
        Returns:
            DataFrame with MultiIndex (symbol, date) and feature columns
        """
        features_df = self.get_features(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            feature_groups=feature_groups
        )
        
        if features_df.empty:
            logger.warning("No features found for the specified criteria")
            return pd.DataFrame()
        
        # Pivot to wide format
        pivot_df = features_df.pivot_table(
            index=['symbol', 'date'],
            columns='feature_name',
            values='feature_value',
            aggfunc='first'
        )
        
        return pivot_df
    
    def get_available_features(
        self,
        feature_group: Optional[str] = None
    ) -> List[str]:
        """
        Get list of available feature names.
        
        Args:
            feature_group: Optional feature group filter
            
        Returns:
            List of unique feature names
        """
        conditions = []
        params = {}
        
        if feature_group:
            conditions.append("feature_group = :feature_group")
            params["feature_group"] = feature_group
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT DISTINCT feature_name
            FROM features
            WHERE {where_clause}
            ORDER BY feature_name
        """
        
        with self.db_manager.get_session() as session:
            result = session.execute(text(sql), params)
            return [row[0] for row in result.fetchall()]
    
    def get_feature_coverage(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get feature coverage statistics.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            DataFrame with coverage statistics by feature
        """
        conditions = []
        params = {}
        
        if symbols:
            placeholders = [f":symbol_{i}" for i in range(len(symbols))]
            conditions.append(f"symbol IN ({','.join(placeholders)})")
            for i, symbol in enumerate(symbols):
                params[f"symbol_{i}"] = symbol
        
        if start_date:
            conditions.append("date >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT 
                feature_name,
                feature_group,
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as symbols_covered,
                COUNT(DISTINCT date) as dates_covered,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM features
            WHERE {where_clause}
            GROUP BY feature_name, feature_group
            ORDER BY feature_group, feature_name
        """
        
        with self.db_manager.get_session() as session:
            result = session.execute(text(sql), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        return df
    
    def delete_features(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        feature_groups: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None
    ) -> int:
        """
        Delete features based on criteria.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for deletion
            end_date: End date for deletion
            feature_groups: Feature groups to delete
            feature_names: Specific feature names to delete
            
        Returns:
            Number of deleted records
        """
        conditions = []
        params = {}
        
        if symbols:
            placeholders = [f":symbol_{i}" for i in range(len(symbols))]
            conditions.append(f"symbol IN ({','.join(placeholders)})")
            for i, symbol in enumerate(symbols):
                params[f"symbol_{i}"] = symbol
        
        if start_date:
            conditions.append("date >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("date <= :end_date")
            params["end_date"] = end_date
        
        if feature_groups:
            placeholders = [f":group_{i}" for i in range(len(feature_groups))]
            conditions.append(f"feature_group IN ({','.join(placeholders)})")
            for i, group in enumerate(feature_groups):
                params[f"group_{i}"] = group
        
        if feature_names:
            placeholders = [f":name_{i}" for i in range(len(feature_names))]
            conditions.append(f"feature_name IN ({','.join(placeholders)})")
            for i, name in enumerate(feature_names):
                params[f"name_{i}"] = name
        
        if not conditions:
            raise ValueError("At least one deletion criteria must be specified")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"DELETE FROM features WHERE {where_clause}"
        
        with self.db_manager.get_session() as session:
            try:
                result = session.execute(text(sql), params)
                session.commit()
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} feature records")
                return deleted_count
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting features: {e}")
                raise