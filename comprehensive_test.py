"""
Comprehensive Test Script for Educational Platform Bot
اختبار شامل لجميع وظائف البوت
"""
import asyncio
from loguru import logger

# Test results tracker
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


async def test_imports():
    """Test all imports"""
    print("\n" + "="*50)
    print("🔍 اختبار الاستيرادات...")
    print("="*50)
    
    try:
        from config.settings import settings
        test_results["passed"].append("✅ config.settings")
        print("✅ config.settings - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ config.settings: {e}")
        print(f"❌ config.settings: {e}")
    
    try:
        from database.connection import init_db, close_db
        test_results["passed"].append("✅ database.connection")
        print("✅ database.connection - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ database.connection: {e}")
        print(f"❌ database.connection: {e}")
    
    try:
        from database.models.user import User
        test_results["passed"].append("✅ database.models.user")
        print("✅ database.models.user - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ database.models.user: {e}")
        print(f"❌ database.models.user: {e}")
    
    try:
        from bot.keyboards.main_keyboards import (
            get_main_menu_keyboard,
            get_admin_menu_keyboard,
            get_courses_keyboard,
            get_years_keyboard
        )
        test_results["passed"].append("✅ bot.keyboards.main_keyboards")
        print("✅ bot.keyboards.main_keyboards - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.keyboards: {e}")
        print(f"❌ bot.keyboards: {e}")
    
    try:
        from bot.handlers.start import start_command, asking_name, asking_phone, asking_email
        test_results["passed"].append("✅ bot.handlers.start")
        print("✅ bot.handlers.start - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.start: {e}")
        print(f"❌ bot.handlers.start: {e}")
    
    try:
        from bot.handlers.courses import show_courses, show_course_details
        test_results["passed"].append("✅ bot.handlers.courses")
        print("✅ bot.handlers.courses - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.courses: {e}")
        print(f"❌ bot.handlers.courses: {e}")
    
    try:
        from bot.handlers.materials import show_materials, show_semesters
        test_results["passed"].append("✅ bot.handlers.materials")
        print("✅ bot.handlers.materials - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.materials: {e}")
        print(f"❌ bot.handlers.materials: {e}")
    
    try:
        from bot.handlers.content import show_lectures, show_videos, watch_video
        test_results["passed"].append("✅ bot.handlers.content")
        print("✅ bot.handlers.content - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.content: {e}")
        print(f"❌ bot.handlers.content: {e}")
    
    try:
        from bot.handlers.admin import admin_help, admin_show_videos
        test_results["passed"].append("✅ bot.handlers.admin")
        print("✅ bot.handlers.admin - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.admin: {e}")
        print(f"❌ bot.handlers.admin: {e}")
    
    try:
        from bot.handlers.assignments import create_assignment, create_exam
        test_results["passed"].append("✅ bot.handlers.assignments")
        print("✅ bot.handlers.assignments - OK")
    except Exception as e:
        test_results["failed"].append(f"❌ bot.handlers.assignments: {e}")
        print(f"❌ bot.handlers.assignments: {e}")


async def test_database_connection():
    """Test database connection"""
    print("\n" + "="*50)
    print("🗄️ اختبار الاتصال بقاعدة البيانات...")
    print("="*50)
    
    try:
        from database.connection import init_db, close_db
        await init_db()
        test_results["passed"].append("✅ MongoDB Connection")
        print("✅ MongoDB متصل بنجاح")
        
        # Test database operations
        from database.models.user import User
        
        # Count users
        count = await User.count()
        print(f"📊 عدد المستخدمين: {count}")
        test_results["passed"].append(f"✅ Database Query (Users: {count})")
        
        await close_db()
        
    except Exception as e:
        test_results["failed"].append(f"❌ Database Connection: {e}")
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")


async def test_configuration():
    """Test configuration files"""
    print("\n" + "="*50)
    print("⚙️ اختبار ملفات التكوين...")
    print("="*50)
    
    try:
        from config.settings import settings
        
        # Check Bot Token
        if settings.TELEGRAM_BOT_TOKEN:
            test_results["passed"].append("✅ TELEGRAM_BOT_TOKEN configured")
            print(f"✅ Bot Token: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
        else:
            test_results["failed"].append("❌ TELEGRAM_BOT_TOKEN not configured")
            print("❌ Bot Token غير محدد!")
        
        # Check Admin ID
        if settings.TELEGRAM_ADMIN_ID:
            test_results["passed"].append(f"✅ Admin ID: {settings.TELEGRAM_ADMIN_ID}")
            print(f"✅ Admin ID: {settings.TELEGRAM_ADMIN_ID}")
        else:
            test_results["warnings"].append("⚠️ Admin ID not configured")
            print("⚠️ Admin ID غير محدد!")
        
        # Check MongoDB URL
        if settings.MONGODB_URL:
            test_results["passed"].append("✅ MongoDB URL configured")
            print(f"✅ MongoDB URL: {settings.MONGODB_URL}")
        else:
            test_results["failed"].append("❌ MongoDB URL not configured")
            print("❌ MongoDB URL غير محدد!")
        
        # Check payment methods
        if settings.SHAP_CASH_NUMBER:
            test_results["passed"].append("✅ Shap Cash configured")
            print(f"✅ Shap Cash: {settings.SHAP_CASH_NUMBER[:10]}...")
        else:
            test_results["warnings"].append("⚠️ Shap Cash not configured")
            print("⚠️ Shap Cash غير محدد!")
        
        if settings.HARAM_NUMBER:
            test_results["passed"].append(f"✅ HARAM Number: {settings.HARAM_NUMBER}")
            print(f"✅ HARAM Number: {settings.HARAM_NUMBER}")
        else:
            test_results["warnings"].append("⚠️ HARAM Number not configured")
            print("⚠️ HARAM Number غير محدد!")
        
    except Exception as e:
        test_results["failed"].append(f"❌ Configuration Error: {e}")
        print(f"❌ خطأ في التكوين: {e}")


async def test_keyboards():
    """Test keyboard structures"""
    print("\n" + "="*50)
    print("⌨️ اختبار الأزرار...")
    print("="*50)
    
    try:
        from bot.keyboards.main_keyboards import (
            get_main_menu_keyboard,
            get_admin_menu_keyboard,
            get_courses_keyboard,
            get_years_keyboard,
            get_semesters_keyboard,
            get_payment_methods_keyboard,
            get_course_content_keyboard,
            get_material_content_keyboard
        )
        
        # Test main menu
        main_kb = get_main_menu_keyboard()
        print("✅ Main Menu Keyboard:")
        for row in main_kb.keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Main Menu Keyboard")
        
        # Test admin menu
        admin_kb = get_admin_menu_keyboard()
        print("\n✅ Admin Menu Keyboard:")
        for row in admin_kb.keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Admin Menu Keyboard")
        
        # Test courses keyboard
        courses_kb = get_courses_keyboard()
        print("\n✅ Courses Keyboard:")
        for row in courses_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Courses Keyboard")
        
        # Test years keyboard
        years_kb = get_years_keyboard()
        print("\n✅ Years Keyboard:")
        for row in years_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Years Keyboard")
        
        # Test semesters keyboard
        semesters_kb = get_semesters_keyboard(3)
        print("\n✅ Semesters Keyboard (Year 3):")
        for row in semesters_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Semesters Keyboard")
        
        # Test payment keyboard
        payment_kb = get_payment_methods_keyboard("course", "test_id")
        print("\n✅ Payment Methods Keyboard:")
        for row in payment_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Payment Keyboard")
        
        # Test course content keyboard
        content_kb = get_course_content_keyboard("test_course")
        print("\n✅ Course Content Keyboard:")
        for row in content_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Course Content Keyboard")
        
        # Test material content keyboard
        material_kb = get_material_content_keyboard("test_material")
        print("\n✅ Material Content Keyboard:")
        for row in material_kb.inline_keyboard:
            buttons = " | ".join([btn.text for btn in row])
            print(f"   {buttons}")
        test_results["passed"].append("✅ Material Content Keyboard")
        
    except Exception as e:
        test_results["failed"].append(f"❌ Keyboards Error: {e}")
        print(f"❌ خطأ في الأزرار: {e}")


async def test_courses_config():
    """Test courses configuration"""
    print("\n" + "="*50)
    print("📚 اختبار تكوين الدورات...")
    print("="*50)
    
    try:
        from config.courses_config import get_all_courses, get_course
        
        courses = get_all_courses()
        print(f"✅ عدد الدورات المتاحة: {len(courses)}")
        
        for course in courses:
            print(f"\n📚 {course['name']}")
            print(f"   المدة: {course['duration']}")
            print(f"   السعر: {course['price']:,} ل.س")
            print(f"   المحتوى: {len(course['syllabus'])} عناصر")
            print(f"   المشاريع: {len(course['projects'])} مشروع")
        
        test_results["passed"].append(f"✅ Courses Config ({len(courses)} courses)")
        
    except Exception as e:
        test_results["failed"].append(f"❌ Courses Config Error: {e}")
        print(f"❌ خطأ في تكوين الدورات: {e}")


async def test_materials_config():
    """Test materials configuration"""
    print("\n" + "="*50)
    print("🎓 اختبار تكوين المواد الجامعية...")
    print("="*50)
    
    try:
        from config.materials_config import get_materials_by_year_semester, get_material
        
        # Test year 3, semester 1
        materials = get_materials_by_year_semester(3, 1)
        print(f"✅ السنة الثالثة - الفصل الأول: {len(materials)} مواد")
        
        for material in materials:
            print(f"\n🎓 {material['name']}")
            print(f"   الدكتور: {material['instructor']}")
            print(f"   السعر: {material['price']:,} ل.س")
        
        test_results["passed"].append(f"✅ Materials Config (Year 3, Sem 1: {len(materials)} materials)")
        
    except Exception as e:
        test_results["failed"].append(f"❌ Materials Config Error: {e}")
        print(f"❌ خطأ في تكوين المواد: {e}")


def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("📊 ملخص الاختبار")
    print("="*70)
    
    print(f"\n✅ النجاحات ({len(test_results['passed'])}):")
    for item in test_results['passed']:
        print(f"   {item}")
    
    if test_results['warnings']:
        print(f"\n⚠️ التحذيرات ({len(test_results['warnings'])}):")
        for item in test_results['warnings']:
            print(f"   {item}")
    
    if test_results['failed']:
        print(f"\n❌ الأخطاء ({len(test_results['failed'])}):")
        for item in test_results['failed']:
            print(f"   {item}")
    else:
        print("\n🎉 لا توجد أخطاء!")
    
    print("\n" + "="*70)
    total_tests = len(test_results['passed']) + len(test_results['failed'])
    success_rate = (len(test_results['passed']) / total_tests * 100) if total_tests > 0 else 0
    print(f"معدل النجاح: {success_rate:.1f}%")
    print("="*70)


async def main():
    """Main test function"""
    print("\n" + "="*70)
    print("🚀 بدء الاختبار الشامل للمنصة التعليمية")
    print("="*70)
    
    await test_imports()
    await test_configuration()
    await test_database_connection()
    await test_keyboards()
    await test_courses_config()
    await test_materials_config()
    
    print_summary()
    
    # Final verdict
    if not test_results['failed']:
        print("\n✅ ✅ ✅ جميع الاختبارات نجحت! البرنامج جاهز للعمل! ✅ ✅ ✅")
        return 0
    else:
        print(f"\n❌ فشل {len(test_results['failed'])} اختبار. يرجى إصلاح الأخطاء.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
