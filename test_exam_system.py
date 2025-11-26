"""
Test Exam System
اختبار نظام الاختبارات
"""
import json
from pathlib import Path
import sys
import io

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_courses_config():
    """Test courses configuration"""
    print("=" * 50)
    print("🧪 اختبار تكوين الدورات")
    print("=" * 50)
    
    try:
        # Import courses
        sys.path.insert(0, str(Path(__file__).parent))
        from config.courses_config import get_all_courses, get_course
        
        courses = get_all_courses()
        print(f"✅ عدد الدورات المتاحة: {len(courses)}")
        
        for course in courses:
            print(f"\n📚 {course['name']}")
            print(f"   - ID: {course['id']}")
            print(f"   - المستوى: {course['level']}")
            print(f"   - المدة: {course['duration']}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_exams_data():
    """Test exams data file"""
    print("\n" + "=" * 50)
    print("🧪 اختبار ملف الاختبارات")
    print("=" * 50)
    
    exams_path = Path("data/exams.json")
    
    if not exams_path.exists():
        print("⚠️  ملف exams.json غير موجود")
        print("💡 سيتم إنشاؤه عند إنشاء أول اختبار")
        return True
    
    try:
        with open(exams_path, 'r', encoding='utf-8') as f:
            exams = json.load(f)
        
        print(f"✅ عدد الاختبارات المحفوظة: {len(exams)}")
        
        # Group by course
        by_course = {}
        for exam in exams:
            course_id = exam.get('course_id', 'unknown')
            if course_id not in by_course:
                by_course[course_id] = []
            by_course[course_id].append(exam)
        
        print("\n📊 توزيع الاختبارات حسب الدورة:")
        for course_id, course_exams in by_course.items():
            print(f"   - {course_id}: {len(course_exams)} اختبار")
            for exam in course_exams:
                print(f"      • {exam.get('title', 'بدون عنوان')}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_exam_grades():
    """Test exam grades data file"""
    print("\n" + "=" * 50)
    print("🧪 اختبار ملف الدرجات")
    print("=" * 50)
    
    grades_path = Path("data/exam_grades.json")
    
    if not grades_path.exists():
        print("⚠️  ملف exam_grades.json غير موجود")
        print("💡 سيتم إنشاؤه عند تقييم أول اختبار")
        return True
    
    try:
        with open(grades_path, 'r', encoding='utf-8') as f:
            grades = json.load(f)
        
        print(f"✅ عدد التقييمات المحفوظة: {len(grades)}")
        
        if grades:
            print("\n📊 آخر 5 تقييمات:")
            for grade in grades[-5:]:
                print(f"   - الطالب: {grade.get('student_name', 'غير معروف')}")
                print(f"     الاختبار: {grade.get('exam_title', 'غير معروف')}")
                print(f"     الدرجة: {grade.get('grade', 0)}/{grade.get('max_grade', 100)}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_exam_creator_imports():
    """Test exam creator imports"""
    print("\n" + "=" * 50)
    print("🧪 اختبار استيراد وحدة إنشاء الاختبارات")
    print("=" * 50)
    
    try:
        from bot.handlers.exam_creator import (
            start_create_exam,
            select_exam_course,
            enter_exam_title,
            enter_exam_link,
            enter_exam_max_grade,
            cancel_exam_creation
        )
        
        print("✅ تم استيراد جميع الوظائف بنجاح:")
        print("   - start_create_exam")
        print("   - select_exam_course")
        print("   - enter_exam_title")
        print("   - enter_exam_link")
        print("   - enter_exam_max_grade")
        print("   - cancel_exam_creation")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_content_handler():
    """Test content handler show_exams"""
    print("\n" + "=" * 50)
    print("🧪 اختبار معالج عرض الاختبارات")
    print("=" * 50)
    
    try:
        from bot.handlers.content import show_exams
        
        print("✅ تم استيراد show_exams بنجاح")
        print("   - يمكن عرض الاختبارات للطلاب")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 50)
    print("         Exam System Test")
    print("=" * 50)
    print()
    
    results = []
    
    # Run tests
    results.append(("تكوين الدورات", test_courses_config()))
    results.append(("ملف الاختبارات", test_exams_data()))
    results.append(("ملف الدرجات", test_exam_grades()))
    results.append(("استيراد إنشاء الاختبارات", test_exam_creator_imports()))
    results.append(("معالج عرض الاختبارات", test_content_handler()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ملخص النتائج")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{status} - {test_name}")
    
    print("\n" + "-" * 50)
    print(f"النتيجة النهائية: {passed}/{total} ({int(passed/total*100)}%)")
    
    if passed == total:
        print("\n🎉 رائع! جميع الاختبارات نجحت!")
        print("✅ النظام جاهز للاستخدام")
    else:
        print("\n⚠️  بعض الاختبارات فشلت")
        print("💡 راجع الأخطاء أعلاه وقم بإصلاحها")
    
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
