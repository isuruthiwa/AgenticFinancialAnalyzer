#!/usr/bin/env python3
"""
CSE Stock Prediction Pipeline CLI

Main entry point for the agentic Colombo Stock Exchange stock prediction platform.
Provides a command-line interface for data ingestion, feature engineering, 
model training, and prediction tasks.

Usage:
    python run_pipeline.py --tasks ingest
    python run_pipeline.py --tasks features,train
    python run_pipeline.py --tasks predict --symbols DIAL,JKH
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.logging_setup import setup_logging

app = typer.Typer(
    name="cse-pipeline",
    help="CSE Stock Prediction Pipeline - Agentic Financial Analysis Platform",
    add_completion=False,
)
console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing config file: {e}[/red]")
        raise typer.Exit(1)


def ensure_directories(config: dict) -> None:
    """Ensure required directories exist."""
    paths = config.get("paths", {})
    for path_name, path_value in paths.items():
        Path(path_value).mkdir(parents=True, exist_ok=True)


@app.command()
def main(
    tasks: str = typer.Option(
        "ingest",
        "--tasks",
        help="Comma-separated list of tasks: ingest,features,train,predict"
    ),
    symbols: Optional[str] = typer.Option(
        None,
        "--symbols", 
        help="Comma-separated list of stock symbols (for predict task)"
    ),
    config_file: str = typer.Option(
        "config.yaml",
        "--config",
        help="Path to configuration file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging"
    )
) -> None:
    """
    Run the CSE stock prediction pipeline.
    
    Available tasks:
    - ingest: Fetch and store market data
    - features: Generate features for modeling
    - train: Train prediction models
    - predict: Generate predictions for specified symbols
    """
    # Load configuration
    config = load_config(config_file)
    
    # Setup logging
    log_level = "DEBUG" if verbose else config.get("logging", {}).get("level", "INFO")
    setup_logging(level=log_level, config=config)
    logger = logging.getLogger(__name__)
    
    # Ensure directories exist
    ensure_directories(config)
    
    # Parse tasks
    task_list = [task.strip() for task in tasks.split(",")]
    
    console.print(f"[green]Starting CSE Pipeline with tasks: {task_list}[/green]")
    logger.info(f"Pipeline started with tasks: {task_list}")
    
    try:
        for task in task_list:
            console.print(f"\n[blue]Executing task: {task}[/blue]")
            
            if task == "ingest":
                run_ingestion_task(config)
            elif task == "features":
                run_feature_engineering_task(config)
            elif task == "train":
                run_training_task(config)
            elif task == "predict":
                symbol_list = symbols.split(",") if symbols else None
                run_prediction_task(config, symbol_list)
            else:
                console.print(f"[red]Unknown task: {task}[/red]")
                logger.error(f"Unknown task: {task}")
                raise typer.Exit(1)
                
        console.print("\n[green]Pipeline completed successfully![/green]")
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        console.print(f"\n[red]Pipeline failed: {e}[/red]")
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise typer.Exit(1)


def run_ingestion_task(config: dict) -> None:
    """Run data ingestion task."""
    from data_sources.cse_symbol_list import fetch_symbol_list
    from data_sources.prices import fetch_price_data
    from data_sources.corporate_actions import fetch_corporate_actions
    from data_sources.dividends import fetch_dividends
    from data_sources.indices import fetch_indices
    
    logger = logging.getLogger(__name__)
    
    logger.info("Starting data ingestion...")
    console.print("  • Fetching symbol list...")
    
    try:
        # Fetch symbol list (this will log warnings about unimplemented fetchers)
        symbols = fetch_symbol_list()
        console.print(f"    Found {len(symbols)} symbols")
        
        # Fetch sample data for demonstration
        console.print("  • Fetching price data (sample)...")
        fetch_price_data(symbols[:5])  # Sample first 5 symbols
        
        console.print("  • Fetching corporate actions...")
        fetch_corporate_actions(symbols[:5])
        
        console.print("  • Fetching dividends...")
        fetch_dividends(symbols[:5])
        
        console.print("  • Fetching indices...")
        fetch_indices()
        
        console.print("  [green]Ingestion task completed[/green]")
        
    except Exception as e:
        logger.error(f"Ingestion task failed: {e}")
        raise


def run_feature_engineering_task(config: dict) -> None:
    """Run feature engineering task."""
    from processing.feature_engineering import FeatureEngineer
    
    logger = logging.getLogger(__name__)
    logger.info("Starting feature engineering...")
    
    console.print("  • Initializing feature engineer...")
    engineer = FeatureEngineer(config)
    
    console.print("  • Generating features...")
    engineer.generate_features()
    
    console.print("  [green]Feature engineering completed[/green]")


def run_training_task(config: dict) -> None:
    """Run model training task."""
    from models.datasets import prepare_datasets
    from models.lgbm_regressor import LGBMPredictor
    from models.baseline_naive import NaivePredictor
    
    logger = logging.getLogger(__name__)
    logger.info("Starting model training...")
    
    console.print("  • Preparing datasets...")
    datasets = prepare_datasets(config)
    
    console.print("  • Training baseline naive model...")
    naive_model = NaivePredictor(config)
    naive_model.train(datasets["train"])
    
    console.print("  • Training LightGBM model...")
    lgbm_model = LGBMPredictor(config)
    lgbm_model.train(datasets["train"], datasets["validation"])
    
    console.print("  [green]Model training completed[/green]")


def run_prediction_task(config: dict, symbols: Optional[List[str]] = None) -> None:
    """Run prediction task."""
    from models.ensemble import EnsemblePredictor
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting predictions for symbols: {symbols}")
    
    if not symbols:
        console.print("  [yellow]No symbols specified, using default set[/yellow]")
        symbols = ["DIAL", "JKH", "COMB"]  # Default CSE symbols
    
    console.print(f"  • Generating predictions for: {', '.join(symbols)}")
    
    ensemble = EnsemblePredictor(config)
    predictions = ensemble.predict(symbols)
    
    console.print("  • Predictions generated:")
    for symbol, pred in predictions.items():
        console.print(f"    {symbol}: {pred}")
    
    console.print("  [green]Prediction task completed[/green]")


if __name__ == "__main__":
    app()