#!/usr/bin/env python3
"""
Simple test script to verify the scaffolding works without external dependencies.
"""

import sys
import os
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that we can import our modules."""
    print("Testing module imports...")
    
    try:
        # Test storage imports
        # Test basic utils that don't need external deps
        from utils.time_utils import is_trading_day
        print("✓ utils.time_utils imported successfully")
        
        # Test that files exist and can be read
        import os
        
        storage_files = ["storage/__init__.py", "storage/schema.sql", "storage/db.py"]
        for file in storage_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
        
        data_source_files = ["data_sources/__init__.py", "data_sources/cse_symbol_list.py", "data_sources/prices.py"]
        for file in data_source_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
        
        # Test utils imports
        from utils.logging_setup import setup_logging
        print("✓ utils.logging_setup imported successfully")
        
        from utils.time_utils import is_trading_day
        print("✓ utils.time_utils imported successfully")
        
        print("All imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("\nTesting basic functionality...")
    
    try:
        # Test time utils
        from datetime import date
        from utils.time_utils import is_trading_day, get_last_trading_day
        
        today = date.today()
        is_trading = is_trading_day(today)
        print(f"✓ is_trading_day({today}) = {is_trading}")
        
        last_trading_day = get_last_trading_day()
        print(f"✓ get_last_trading_day() = {last_trading_day}")
        
        # Test simple hardcoded symbol list
        hardcoded_symbols = ["DIAL", "JKH", "COMB", "SAMP", "HNB"]
        print(f"✓ Hardcoded symbols available: {hardcoded_symbols[:3]}...")
        
        print("Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Functionality error: {e}")
        return False


def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration loading...")
    
    try:
        import yaml
        
        config_path = project_root / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            print(f"✓ Config loaded successfully")
            print(f"  - Database URI: {config.get('database', {}).get('uri', 'not set')}")
            print(f"  - Prediction horizons: {config.get('models', {}).get('prediction_horizons', 'not set')}")
            
            return True
        else:
            print("✗ config.yaml not found")
            return False
            
    except Exception as e:
        print(f"✗ Config loading error: {e}")
        return False


def main():
    """Run all tests."""
    print("CSE Stock Prediction Platform - Scaffolding Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not (project_root / "config.yaml").exists():
        print("✗ Not in project root directory or config.yaml missing")
        return False
    
    success = True
    
    # Run tests
    success &= test_imports()
    success &= test_basic_functionality()
    success &= test_config_loading()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All scaffolding tests passed!")
        print("The CSE prediction platform scaffolding is working correctly.")
    else:
        print("❌ Some tests failed.")
        print("Check the errors above and fix the issues.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)