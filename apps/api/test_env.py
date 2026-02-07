from app.core.config import get_settings
import os

print("=== Environment Variable Test ===")
print(f"GROQ_API_KEY from os.getenv: {os.getenv('GROQ_API_KEY')}")

print("\n=== Settings Test ===")
settings = get_settings()
print(f"GROQ_API_KEY from settings: {settings.GROQ_API_KEY}")
print(f"API Key is set: {bool(settings.GROQ_API_KEY)}")

if settings.GROQ_API_KEY:
    print(f"First 20 chars: {settings.GROQ_API_KEY[:20]}...")
else:
    print("❌ API Key not loaded!")
    
print("\n=== .env File Check ===")
from pathlib import Path
env_path = Path(".env")
print(f".env exists: {env_path.exists()}")
if env_path.exists():
    content = env_path.read_text()
    print(f".env content:\n{content}")
