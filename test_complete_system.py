"""
Complete System Test
اختبار النظام الكامل
"""
import asyncio
import sys
import io
from pathlib import Path
import json

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

async def test_mongodb():
    """Test MongoDB connection"""
    print_header("1️⃣  اختبار MongoDB")
    
    try:
        from config.settings import settings
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import init_beanie
        from database.models.user import User
        
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await client.admin.command('ping')
        print_success("MongoDB متصل")
        
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=[User]
        )
        
        user_count = await User.count()
        print_success(f"عدد المستخدمين: {user_count}")
        
        client.close()
        return True
    except Exception as e:
        print_error(f"فشل اتصال MongoDB: {e}")
        return False

async def test_telegram_bot():
    """Test Telegram Bot connection"""
    print_header("2️⃣  اختبار Telegram Bot")
    
    try:
        from telegram import Bot
        from telegram.request import HTTPXRequest
        from config.settings import settings
        
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
        )
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, request=request)
        
        async with bot:
            me = await bot.get_me()
            print_success(f"البوت متصل: @{me.username}")
            print_info(f"Bot ID: {me.id}")
            print_info(f"الاسم: {me.first_name}")
        
        return True
    except Exception as e:
        print_error(f"فشل اتصال البوت: {e}")
        return False

def test_courses_config():
    """Test courses configuration"""
    print_header("3️⃣  اختبار تكوين الدورات")
    
    try:
        from config.courses_config import get_all_courses
        
        courses = get_all_courses()
        print_success(f"عدد الدورات: {len(courses)}")
        
        for course in courses:
            print_info(f"  - {course['name']} (ID: {course['id']})")
        
        return True
    except Exception as e:
        print_error(f"فشل تحميل الدورات: {e}")
        return False

def test_exams_file():
    """Test exams file"""
    print_header("4️⃣  اختبار ملف الاختبارات")
    
    exams_path = Path("data/exams.json")
    
    if not exams_path.exists():
        print_info("ملف exams.json غير موجود - سيتم إنشاؤه عند إنشاء أول اختبار")
        return True
    
    try:
        with open(exams_path, 'r', encoding='utf-8') as f:
            exams = json.load(f)
        
        print_success(f"عدد الاختبارات: {len(exams)}")
        
        # Group by course
        by_course = {}
        for exam in exams:
            course_id = exam.get('course_id', 'unknown')
            if course_id not in by_course:
                by_course[course_id] = []
            by_course[course_id].append(exam)
        
        for course_id, course_exams in by_course.items():
            print_info(f"  - {course_id}: {len(course_exams)} اختبار")
        
        return True
    except Exception as e:
        print_error(f"خطأ في ملف الاختبارات: {e}")
        return False

def test_exam_creator():
    """Test exam creator module"""
    print_header("5️⃣  اختبار وحدة إنشاء الاختبارات")
    
    try:
        from bot.handlers.exam_creator import (
            start_create_exam,
            select_exam_course,
            enter_exam_title,
            enter_exam_link,
            enter_exam_max_grade
        )
        
        print_success("تم استيراد جميع الوظائف")
        print_info("  - start_create_exam")
        print_info("  - select_exam_course")
        print_info("  - enter_exam_title")
        print_info("  - enter_exam_link")
        print_info("  - enter_exam_max_grade")
        
        return True
    except Exception as e:
        print_error(f"فشل استيراد exam_creator: {e}")
        return False

def test_exam_grading():
    """Test exam grading module"""
    print_header("6️⃣  اختبار وحدة تقييم الاختبارات")
    
    try:
        from bot.handlers.exam_grading import (
            start_exam_grading_menu,
            select_exam_for_grading,
            select_student_for_exam_grading,
            enter_exam_grade,
            enter_exam_feedback_and_save
        )
        
        print_success("تم استيراد جميع الوظائف")
        print_info("  - start_exam_grading_menu")
        print_info("  - select_exam_for_grading")
        print_info("  - select_student_for_exam_grading")
        print_info("  - enter_exam_grade")
        print_info("  - enter_exam_feedback_and_save")
        
        return True
    except Exception as e:
        print_error(f"فشل استيراد exam_grading: {e}")
        return False

def test_content_handler():
    """Test content handler"""
    print_header("7️⃣  اختبار معالج المحتوى")
    
    try:
        from bot.handlers.content import show_exams
        
        print_success("تم استيراد show_exams")
        print_info("  - الطلاب يمكنهم رؤية الاختبارات")
        
        return True
    except Exception as e:
        print_error(f"فشل استيراد content handler: {e}")
        return False

def test_grades_file():
    """Test exam grades file"""
    print_header("8️⃣  اختبار ملف الدرجات")
    
    grades_path = Path("data/exam_grades.json")
    
    if not grades_path.exists():
        print_info("ملف exam_grades.json غير موجود - سيتم إنشاؤه عند أول تقييم")
        return True
    
    try:
        with open(grades_path, 'r', encoding='utf-8') as f:
            grades = json.load(f)
        
        print_success(f"عدد التقييمات: {len(grades)}")
        
        if grades:
            print_info("آخر 3 تقييمات:")
            for grade in grades[-3:]:
                student = grade.get('student_name', 'غير معروف')
                exam = grade.get('exam_title', 'غير معروف')
                score = grade.get('grade', 0)
                max_score = grade.get('max_grade', 100)
                print_info(f"  - {student}: {score}/{max_score} في {exam}")
        
        return True
    except Exception as e:
        print_error(f"خطأ في ملف الدرجات: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "اختبار النظام الكامل" + " " * 24 + "║")
    print("║" + " " * 16 + "Complete System Test" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Run tests
    print_info("بدء الاختبارات...\n")
    
    results.append(("MongoDB", await test_mongodb()))
    results.append(("Telegram Bot", await test_telegram_bot()))
    results.append(("تكوين الدورات", test_courses_config()))
    results.append(("ملف الاختبارات", test_exams_file()))
    results.append(("إنشاء الاختبارات", test_exam_creator()))
    results.append(("تقييم الاختبارات", test_exam_grading()))
    results.append(("معالج المحتوى", test_content_handler()))
    results.append(("ملف الدرجات", test_grades_file()))
    
    # Summary
    print_header("📊 ملخص النتائج")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print("\n" + "-" * 60)
    percentage = int(passed/total*100)
    print(f"النتيجة النهائية: {passed}/{total} ({percentage}%)")
    
    if passed == total:
        print("\n🎉 رائع! جميع الاختبارات نجحت!")
        print("✅ النظام جاهز للاستخدام بالكامل")
        print("\n📋 الخطوات التالية:")
        print("   1. تأكد أن Dashboard يعمل: http://localhost:8000")
        print("   2. تأكد أن البوت يعمل: @shahdai_bot")
        print("   3. جرب إنشاء اختبار: /createexam")
        print("   4. جرب تقييم اختبار: 📊 تقييم الاختبارات")
    else:
        print("\n⚠️  بعض الاختبارات فشلت")
        print("💡 راجع الأخطاء أعلاه وقم بإصلاحها")
    
    print("=" * 60)
    print()
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
