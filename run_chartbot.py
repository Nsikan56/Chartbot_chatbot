#!/usr/bin/env python3
"""
Startup script for ChartBot that handles PyTorch/Streamlit compatibility issues.
"""

import os
import sys
import subprocess
import warnings

def setup_environment():
    """Set up environment variables to prevent conflicts."""
    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    
    # Suppress Python warnings
    os.environ['PYTHONWARNINGS'] = 'ignore'
    
    # PyTorch settings
    os.environ['TORCH_SHOW_CPP_STACKTRACES'] = '0'
    
    # Streamlit settings
    os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
    os.environ['STREAMLIT_GLOBAL_SHOW_WARNING_ON_DIRECT_EXECUTION'] = 'false'
    
    print("🔧 Environment configured for ChartBot")

def run_streamlit():
    """Run Streamlit with proper configuration."""
    try:
        # Setup environment
        setup_environment()
        
        # Suppress warnings
        warnings.filterwarnings('ignore')
        
        print("🚀 Starting ChartBot...")
        
        # Run Streamlit with specific arguments
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.fileWatcherType", "none",
            "--global.showWarningOnDirectExecution", "false"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 ChartBot stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    run_streamlit()