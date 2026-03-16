import sys
import os
from pathlib import Path

# Tambahkan root folder ke path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run import app

# Vercel serverless handler
def handler(request):
    return app(request)
