# -*- coding: utf-8 -*-
"""Simple backend test without database"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Testing backend imports (without database)...")
print("=" * 60)

try:
    from app.config import settings
    print(f"OK Config: MongoDB={settings.mongo_database}, CORS={len(settings.cors_origins_list)} origins")
except Exception as e:
    print(f"ERROR Config: {e}")
    sys.exit(1)

try:
    from app.api.v1 import api_router
    print(f"OK API Router: {len(api_router.routes)} routes")
except Exception as e:
    print(f"ERROR API Router: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.main import app
    print(f"OK FastAPI App: {app.title} v{app.version}")
    print(f"   Total routes: {len(app.routes)}")
except Exception as e:
    print(f"ERROR FastAPI App: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.algorithms.resp_rr_estimator import estimate_from_records
    print("OK Algorithm module imported")
except Exception as e:
    print(f"ERROR Algorithm: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.services.signal_processor import SignalProcessor
    from app.services.feedback_generator import FeedbackGenerator
    from app.services.stream_manager import StreamManager
    print("OK Services imported")
except Exception as e:
    print(f"ERROR Services: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS: All imports successful!")
print("\nNote: Database connection not tested (requires MongoDB)")
print("To start server: uvicorn app.main:app --reload")
print("=" * 60)
