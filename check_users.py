"""
Check Users in Database
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from database.connection import init_db, close_db
from database.models.user import User

async def check_users():
    # Connect to database
    await init_db()
    
    print("\n" + "="*60)
    print("👥 فحص المستخدمين في قاعدة البيانات")
    print("="*60)
    
    # Get all users
    users = await User.find_all().to_list()
    
    print(f"📊 عدد المستخدمين: {len(users)}\n")
    
    for user in users:
        is_admin = user.telegram_id == settings.TELEGRAM_ADMIN_ID
        print(f"👤 المستخدم: {user.full_name}")
        print(f"   🔢 Telegram ID: {user.telegram_id}")
        print(f"   🔑 Admin: {'✅ نعم' if is_admin else '❌ لا'}")
        print(f"   📧 Email: {user.email}")
        print(f"   📞 Phone: {user.phone}")
        print(f"   📅 تاريخ التسجيل: {user.registered_at}")
        print("-" * 60)
    
    print(f"\n🔑 ADMIN_ID المتوقع: {settings.TELEGRAM_ADMIN_ID}")
    print("="*60 + "\n")
    
    await close_db()

if __name__ == "__main__":
    asyncio.run(check_users())
