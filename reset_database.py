"""
Reset Database Script
سكريبت إعادة تهيئة قاعدة البيانات
"""
import asyncio
from loguru import logger
from database.connection import init_db, close_db
from database.models.user import User
from database.models.video import Video
from database.models.assignment import Assignment
from database.models.notification import Notification


async def reset_database():
    """Reset database to fresh state"""
    print("\n" + "="*60)
    print("⚠️  إعادة تهيئة قاعدة البيانات")
    print("="*60)
    
    # Initialize database
    await init_db()
    
    # Ask for confirmation
    confirm = input("\n⚠️  هل أنت متأكد من حذف جميع البيانات؟ (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ تم الإلغاء")
        await close_db()
        return
    
    try:
        # Delete all users
        users_count = await User.find().count()
        await User.find().delete()
        logger.info(f"Deleted {users_count} users")
        print(f"✅ تم حذف {users_count} مستخدم")
        
        # Delete all videos from MongoDB
        videos_count = await Video.find().count()
        await Video.find().delete()
        logger.info(f"Deleted {videos_count} videos from MongoDB")
        print(f"✅ تم حذف {videos_count} فيديو من MongoDB")
        
        # Delete all assignments from MongoDB
        assignments_count = await Assignment.find().count()
        await Assignment.find().delete()
        logger.info(f"Deleted {assignments_count} assignments from MongoDB")
        print(f"✅ تم حذف {assignments_count} واجب/اختبار من MongoDB")
        
        # Delete all notifications
        notifications_count = await Notification.find().count()
        await Notification.find().delete()
        logger.info(f"Deleted {notifications_count} notifications")
        print(f"✅ تم حذف {notifications_count} إشعار")
        
        # Delete JSON files
        import json
        from pathlib import Path
        
        # Clear videos.json
        videos_file = Path('data/videos.json')
        if videos_file.exists():
            with open(videos_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"✅ تم تنظيف ملف videos.json")
        
        # Clear assignments.json
        assignments_file = Path('data/assignments.json')
        if assignments_file.exists():
            with open(assignments_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"✅ تم تنظيف ملف assignments.json")
        
        # Clear exams.json
        exams_file = Path('data/exams.json')
        if exams_file.exists():
            with open(exams_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"✅ تم تنظيف ملف exams.json")
        
        print("\n" + "="*60)
        print("✅ تم إعادة تهيئة قاعدة البيانات بنجاح!")
        print("✅ تم حذف جميع الفيديوهات والواجبات!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        print(f"❌ خطأ: {e}")
    
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(reset_database())
