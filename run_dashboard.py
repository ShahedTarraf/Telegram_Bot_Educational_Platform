"""
Run Admin Dashboard
تشغيل لوحة التحكم
"""
import sys
import uvicorn
from pathlib import Path
import io

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 تشغيل لوحة التحكم - Admin Dashboard")
    print("="*60)
    print(f"📍 URL: http://{settings.HOST}:{settings.PORT}")
    print(f"👤 Username: {settings.ADMIN_USERNAME}")
    print(f"🔑 Password: {settings.ADMIN_PASSWORD}")
    print("="*60 + "\n")
    
    uvicorn.run(
        "admin_dashboard.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
