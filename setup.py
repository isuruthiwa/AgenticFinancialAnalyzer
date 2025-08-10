"""
Setup script for the Agentic Financial Analyzer.
"""
import os
import sys
from pathlib import Path
import subprocess

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/vector_db",
        "logs",
        "uploads",
        "exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import streamlit
        import langchain
        import PyPDF2
        import docx
        import PIL
        import plotly
        import pandas
        print("✓ All core dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")
    if not env_file.exists():
        # Copy from example
        example_env = Path(".env.example")
        if example_env.exists():
            env_file.write_text(example_env.read_text())
            print("✓ Created .env file from template")
            print("📝 Please edit .env file with your API keys")
        else:
            print("❌ .env.example file not found")
    else:
        print("✓ .env file already exists")

def main():
    """Main setup function."""
    print("🚀 Setting up Agentic Financial Analyzer...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("❌ Setup failed due to dependency installation error")
            return False
    
    # Setup environment
    setup_environment()
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("")
    print("Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: streamlit run src/main.py")
    print("3. Upload financial documents and start analyzing!")
    
    return True

if __name__ == "__main__":
    main()
