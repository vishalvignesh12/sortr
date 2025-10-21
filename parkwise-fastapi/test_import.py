import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('backend/.env')

# Set default test values if not already set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/parkwise_test')
if 'REDIS_URL' not in os.environ:
    os.environ['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
if 'JWT_SECRET_KEY' not in os.environ:
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
