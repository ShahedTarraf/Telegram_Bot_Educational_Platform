"""
Check pending approval requests in database
التحقق من طلبات الموافقة المعلقة
"""
import asyncio
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import init_db, close_db
from database.models.user import User

async def check_pending():
    """Check for pending approval requests"""
    try:
        # Connect to database
        await init_db()
        print("\n✅ متصل بقاعدة البيانات")
        print("="*60)
        
        # Get all users
        users = await User.find().to_list()
        print(f"📊 عدد المستخدمين الكلي: {len(users)}\n")
        
        # Check for pending course enrollments
        pending_count = 0
        for user in users:
            for enrollment in user.courses:
                if enrollment.approval_status == "pending":
                    pending_count += 1
                    print(f"⏳ طلب معلق:")
                    print(f"   👤 الطالب: {user.full_name}")
                    print(f"   📱 Telegram ID: {user.telegram_id}")
                    print(f"   📧 البريد: {user.email}")
                    print(f"   📚 الدورة: {enrollment.course_id}")
                    print(f"   💰 المبلغ: {enrollment.payment_amount}")
                    print(f"   💳 طريقة الدفع: {enrollment.payment_method}")
                    print(f"   📅 تاريخ التسجيل: {enrollment.enrolled_at}")
                    print(f"   📄 إثبات الدفع: {enrollment.payment_proof_file_id}")
                    print("-"*60)
            
            for enrollment in user.materials:
                if enrollment.approval_status == "pending":
                    pending_count += 1
                    print(f"⏳ طلب معلق (مادة جامعية):")
                    print(f"   👤 الطالب: {user.full_name}")
                    print(f"   📱 Telegram ID: {user.telegram_id}")
                    print(f"   📧 البريد: {user.email}")
                    print(f"   📚 المادة: {enrollment.material_id}")
                    print(f"   📅 السنة: {enrollment.year}")
                    print(f"   📅 الفصل: {enrollment.semester}")
                    print(f"   💰 المبلغ: {enrollment.payment_amount}")
                    print(f"   💳 طريقة الدفع: {enrollment.payment_method}")
                    print(f"   📅 تاريخ التسجيل: {enrollment.enrolled_at}")
                    print("-"*60)
        
        print(f"\n📊 إجمالي الطلبات المعلقة: {pending_count}")
        
        if pending_count == 0:
            print("\n✅ لا توجد طلبات معلقة")
        else:
            print(f"\n⚠️ يوجد {pending_count} طلب معلق يحتاج للموافقة!")
            print(f"🌐 افتح لوحة التحكم: http://localhost:8000/pending-approvals")
        
        # Close database
        await close_db()
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_pending())
