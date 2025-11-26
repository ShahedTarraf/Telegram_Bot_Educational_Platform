"""
Test MongoDB Connection
اختبار اتصال MongoDB
"""
import asyncio
import sys
import io
from pathlib import Path

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mongodb():
    """Test MongoDB connection"""
    print("\n" + "="*60)
    print("🔍 اختبار اتصال MongoDB - Testing MongoDB Connection")
    print("="*60)
    
    try:
        print("\n1️⃣ تحميل الإعدادات...")
        from config.settings import settings
        print(f"✅ MongoDB URL: {settings.MONGODB_URL}")
        print(f"✅ Database: {settings.MONGODB_DB_NAME}")
        
        print("\n2️⃣ الاتصال بـ MongoDB...")
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import init_beanie
        
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test connection
        print("⏳ اختبار الاتصال...")
        await client.admin.command('ping')
        print("✅ نجح الاتصال بـ MongoDB!")
        
        print("\n3️⃣ تهيئة Beanie...")
        from database.models.user import User
        from database.models.quiz import Quiz
        from database.models.video import Video
        from database.models.assignment import Assignment
        from database.models.notification import Notification
        
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=[User, Quiz, Video, Assignment, Notification]
        )
        print("✅ تم تهيئة Beanie بنجاح!")
        
        print("\n4️⃣ اختبار قاعدة البيانات...")
        user_count = await User.count()
        print(f"📊 عدد المستخدمين: {user_count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاتصال!")
        print(f"🔴 الخطأ: {type(e).__name__}")
        print(f"📝 الوصف: {str(e)}")
        
        print("\n💡 نصائح:")
        print("1. تأكد من تشغيل MongoDB:")
        print("   - Windows: تحقق من Services")
        print("   - أو شغّل: mongod")
        print("2. تأكد من المنفذ: 27017")
        print("3. تأكد من .env file")
        
        return False
    
    finally:
        print("\n" + "="*60)

if __name__ == "__main__":
    result = asyncio.run(test_mongodb())
    sys.exit(0 if result else 1)
