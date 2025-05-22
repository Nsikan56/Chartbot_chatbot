"""
Monkey patch to fix PyTorch/Streamlit compatibility issue.
This should be imported before any other imports in your main app.
"""

import sys
import warnings

def fix_torch_classes():
    """Fix the torch.classes path issue with Streamlit's file watcher."""
    try:
        import torch
        
        # Create a mock _path attribute if it doesn't exist
        if hasattr(torch, '_classes') and hasattr(torch._classes, '__path__'):
            if not hasattr(torch._classes.__path__, '_path'):
                torch._classes.__path__._path = []
        
        # Alternative approach: Mock the problematic attribute
        if 'torch._classes' in sys.modules:
            torch_classes = sys.modules['torch._classes']
            if hasattr(torch_classes, '__path__') and not hasattr(torch_classes.__path__, '_path'):
                torch_classes.__path__._path = []
                
    except ImportError:
        pass  # PyTorch not installed
    except Exception as e:
        warnings.warn(f"Could not apply PyTorch fix: {e}")

def suppress_warnings():
    """Suppress various warnings that clutter the output."""
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    # Suppress specific TensorFlow warnings
    warnings.filterwarnings('ignore', message='.*deprecated.*')
    warnings.filterwarnings('ignore', message='.*oneDNN custom operations.*')

# Apply fixes immediately when imported
suppress_warnings()
fix_torch_classes()

print("🔧 Applied PyTorch/Streamlit compatibility fixes")