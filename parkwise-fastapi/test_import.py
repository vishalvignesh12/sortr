import os
import sys

# Set environment variables for testing
os.environ['DATABASE_URL'] = 'postgresql://postgres:Vishal1234@_1234@db.gukutngzdnamdlfcgquv.supabase.co:5432/postgres'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

os.environ['JWT_SECRET_KEY'] = 'test_secret'

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from backend.app.main import app
    print("Application imports successfully!")
    print("App title:", app.title)
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Other error: {e}")