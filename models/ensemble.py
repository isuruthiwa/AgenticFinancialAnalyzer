"""
Ensemble Model for Stock Return Prediction

Combines multiple models (naive, LightGBM, etc.) to create robust
ensemble predictions with uncertainty quantification.
"""

import logging
from datetime import date
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from .baseline_naive import NaivePredictor
from .lgbm_regressor import LGBMPredictor

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple models.
    
    Provides weighted averaging, stacking, and other ensemble methods
    for improved prediction accuracy and robustness.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize ensemble predictor.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.model_config = config.get("models", {})
        self.horizons = self.model_config.get("prediction_horizons", [1, 5, 20])
        
        # Component models
        self.models = {}
        self.weights = {}
        self.fitted = False
        
        # Ensemble configuration
        self.ensemble_method = "weighted_average"  # Default method
        self.include_uncertainty = True
    
    def add_model(self, name: str, model: object, weight: float = 1.0) -> None:
        """
        Add a model to the ensemble.
        
        Args:
            name: Model name
            model: Model instance
            weight: Model weight in ensemble
        """
        self.models[name] = model
        self.weights[name] = weight
        logger.info(f"Added model '{name}' to ensemble with weight {weight}")
    
    def set_ensemble_method(self, method: str) -> None:
        """
        Set ensemble combination method.
        
        Args:
            method: Ensemble method ('weighted_average', 'median', 'stacking')
        """
        valid_methods = ['weighted_average', 'median', 'stacking']
        if method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")
        
        self.ensemble_method = method
        logger.info(f"Ensemble method set to: {method}")
    
    def train(self, train_data: Dict, validation_data: Optional[Dict] = None) -> Dict:
        """
        Train all component models.
        
        Args:
            train_data: Training dataset
            validation_data: Optional validation dataset
            
        Returns:
            Training results from all models
        """
        logger.info("Training ensemble component models")
        
        if not self.models:
            # Create default ensemble
            self._create_default_ensemble()
        
        training_results = {}
        
        for name, model in self.models.items():
            try:
                logger.info(f"Training component model: {name}")
                
                if hasattr(model, 'train'):
                    results = model.train(train_data, validation_data)
                    training_results[name] = results
                else:
                    logger.warning(f"Model {name} does not have train method")
                    
            except Exception as e:
                logger.error(f"Error training model {name}: {e}")
                continue
        
        # Train meta-learner for stacking if needed
        if self.ensemble_method == "stacking":
            self._train_meta_learner(train_data, validation_data)
        
        self.fitted = True
        logger.info("Ensemble training completed")
        
        return training_results
    
    def _create_default_ensemble(self) -> None:
        """Create default ensemble with standard models."""
        logger.info("Creating default ensemble")
        
        # Add naive baseline
        naive_model = NaivePredictor(self.config)
        naive_model.set_strategy("momentum")
        self.add_model("naive_momentum", naive_model, weight=0.2)
        
        # Add LightGBM model
        lgbm_model = LGBMPredictor(self.config)
        self.add_model("lgbm", lgbm_model, weight=0.8)
    
    def _train_meta_learner(self, train_data: Dict, validation_data: Optional[Dict] = None) -> None:
        """
        Train meta-learner for stacking ensemble.
        
        TODO: Implement stacking meta-learner training
        """
        logger.warning("_train_meta_learner: Stub implementation")
        
        # TODO: Implement stacking ensemble training
        # Generate predictions from base models on validation set
        # Train meta-learner to combine base model predictions
    
    def predict(
        self, 
        symbols: List[str], 
        as_of_date: Optional[date] = None
    ) -> Dict[str, Dict[int, float]]:
        """
        Generate ensemble predictions for specified symbols.
        
        Args:
            symbols: List of stock symbols
            as_of_date: Date for prediction (defaults to today)
            
        Returns:
            Dictionary mapping symbols to horizon predictions
        """
        if not self.fitted:
            logger.warning("Ensemble not trained, training with default models")
            self._create_default_ensemble()
            # Use dummy training data for emergency fallback
            dummy_data = {"features": pd.DataFrame(), "targets": pd.DataFrame()}
            self.train(dummy_data)
        
        if as_of_date is None:
            as_of_date = date.today()
        
        logger.info(f"Generating ensemble predictions for {len(symbols)} symbols")
        
        # Get predictions from all component models
        model_predictions = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    predictions = model.predict(symbols, as_of_date)
                    model_predictions[name] = predictions
                else:
                    logger.warning(f"Model {name} does not have predict method")
            except Exception as e:
                logger.error(f"Error getting predictions from {name}: {e}")
                continue
        
        # Combine predictions using ensemble method
        ensemble_predictions = self._combine_predictions(model_predictions, symbols)
        
        return ensemble_predictions
    
    def _combine_predictions(
        self,
        model_predictions: Dict[str, Dict[str, Dict[int, float]]],
        symbols: List[str]
    ) -> Dict[str, Dict[int, float]]:
        """
        Combine predictions from component models.
        
        Args:
            model_predictions: Predictions from each model
            symbols: List of symbols
            
        Returns:
            Combined ensemble predictions
        """
        ensemble_predictions = {}
        
        for symbol in symbols:
            symbol_predictions = {}
            
            for horizon in self.horizons:
                # Collect predictions for this symbol and horizon
                predictions = []
                weights = []
                
                for model_name, model_preds in model_predictions.items():
                    if symbol in model_preds and horizon in model_preds[symbol]:
                        predictions.append(model_preds[symbol][horizon])
                        weights.append(self.weights.get(model_name, 1.0))
                
                if not predictions:
                    # No predictions available
                    symbol_predictions[horizon] = 0.0
                    continue
                
                # Combine predictions
                if self.ensemble_method == "weighted_average":
                    combined_pred = self._weighted_average(predictions, weights)
                elif self.ensemble_method == "median":
                    combined_pred = np.median(predictions)
                elif self.ensemble_method == "stacking":
                    combined_pred = self._stacking_predict(predictions, horizon)
                else:
                    combined_pred = np.mean(predictions)
                
                symbol_predictions[horizon] = round(combined_pred, 4)
            
            ensemble_predictions[symbol] = symbol_predictions
        
        return ensemble_predictions
    
    def _weighted_average(self, predictions: List[float], weights: List[float]) -> float:
        """Calculate weighted average of predictions."""
        if len(predictions) != len(weights):
            weights = [1.0] * len(predictions)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return np.mean(predictions)
        
        weighted_sum = sum(p * w for p, w in zip(predictions, weights))
        return weighted_sum / total_weight
    
    def _stacking_predict(self, predictions: List[float], horizon: int) -> float:
        """
        Generate stacking prediction.
        
        TODO: Implement actual stacking prediction using trained meta-learner
        """
        # For now, just return weighted average
        return np.mean(predictions)
    
    def predict_with_uncertainty(
        self,
        symbols: List[str],
        as_of_date: Optional[date] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Dict[int, Dict[str, float]]]:
        """
        Generate predictions with uncertainty estimates.
        
        Args:
            symbols: List of stock symbols
            as_of_date: Date for prediction
            confidence_level: Confidence level for intervals
            
        Returns:
            Dictionary with predictions and confidence intervals
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        logger.info(f"Generating ensemble predictions with uncertainty for {len(symbols)} symbols")
        
        # Get individual model predictions
        model_predictions = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    predictions = model.predict(symbols, as_of_date)
                    model_predictions[name] = predictions
            except Exception as e:
                logger.error(f"Error getting predictions from {name}: {e}")
                continue
        
        # Calculate ensemble predictions with uncertainty
        results = {}
        
        for symbol in symbols:
            symbol_results = {}
            
            for horizon in self.horizons:
                # Collect predictions for this symbol and horizon
                predictions = []
                
                for model_preds in model_predictions.values():
                    if symbol in model_preds and horizon in model_preds[symbol]:
                        predictions.append(model_preds[symbol][horizon])
                
                if not predictions:
                    symbol_results[horizon] = {
                        "prediction": 0.0,
                        "lower_bound": 0.0,
                        "upper_bound": 0.0,
                        "std": 0.0
                    }
                    continue
                
                # Calculate statistics
                mean_pred = np.mean(predictions)
                std_pred = np.std(predictions) if len(predictions) > 1 else 0.0
                
                # Calculate confidence intervals (assuming normal distribution)
                alpha = 1 - confidence_level
                z_score = 1.96  # For 95% confidence
                
                lower_bound = mean_pred - z_score * std_pred
                upper_bound = mean_pred + z_score * std_pred
                
                symbol_results[horizon] = {
                    "prediction": round(mean_pred, 4),
                    "lower_bound": round(lower_bound, 4),
                    "upper_bound": round(upper_bound, 4),
                    "std": round(std_pred, 4)
                }
            
            results[symbol] = symbol_results
        
        return results
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights."""
        total_weight = sum(self.weights.values())
        if total_weight == 0:
            return self.weights.copy()
        
        return {name: weight / total_weight for name, weight in self.weights.items()}
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update model weights based on performance.
        
        Args:
            new_weights: New weights for each model
        """
        for name, weight in new_weights.items():
            if name in self.models:
                self.weights[name] = weight
                logger.info(f"Updated weight for {name}: {weight}")
    
    def get_ensemble_info(self) -> Dict:
        """Get information about the ensemble configuration."""
        return {
            "num_models": len(self.models),
            "model_names": list(self.models.keys()),
            "weights": self.get_model_weights(),
            "ensemble_method": self.ensemble_method,
            "horizons": self.horizons,
            "fitted": self.fitted
        }


def create_production_ensemble(config: Dict) -> EnsemblePredictor:
    """
    Create production-ready ensemble with optimized models.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured ensemble predictor
    """
    ensemble = EnsemblePredictor(config)
    
    # Add multiple naive baselines
    momentum_model = NaivePredictor(config)
    momentum_model.set_strategy("momentum")
    ensemble.add_model("momentum", momentum_model, weight=0.1)
    
    mean_reversion_model = NaivePredictor(config)
    mean_reversion_model.set_strategy("mean_reversion")
    ensemble.add_model("mean_reversion", mean_reversion_model, weight=0.1)
    
    # Add main LightGBM model
    lgbm_model = LGBMPredictor(config)
    ensemble.add_model("lgbm_main", lgbm_model, weight=0.8)
    
    # Set ensemble method
    ensemble.set_ensemble_method("weighted_average")
    
    return ensemble