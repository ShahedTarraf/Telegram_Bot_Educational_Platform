#!/usr/bin/env python
"""
Railway Deployment Readiness Check
يتحقق من أن المشروع جاهز للنشر على Railway
"""

import os
import sys
from pathlib import Path

def check_file_exists(filename):
    """التحقق من وجود ملف"""
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"{status} {filename}")
    return exists

def check_env_variables():
    """التحقق من متغيرات البيئة المطلوبة"""
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_ADMIN_ID",
        "MONGODB_URL",
        "MONGODB_DB_NAME",
        "SECRET_KEY",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ADMIN_EMAIL",
        "SHAP_CASH_NUMBER",
        "HARAM_NUMBER",
    ]
    
    print("\n📋 متغيرات البيئة المطلوبة:")
    missing = []
    for var in required_vars:
        if var in os.environ:
            print(f"✅ {var}")
        else:
            print(f"⚠️  {var} (غير محدد محلياً، يجب تحديده في Railway)")
            missing.append(var)
    
    return missing

def check_requirements():
    """التحقق من ملف requirements.txt"""
    required_packages = [
        "python-telegram-bot",
        "fastapi",
        "uvicorn",
        "motor",
        "beanie",
        "pydantic",
        "pydantic-settings",
        "python-dotenv",
        "loguru",
    ]
    
    print("\n📦 المكتبات المطلوبة:")
    with open("requirements.txt", "r") as f:
        requirements = f.read().lower()
    
    all_present = True
    for package in required_packages:
        if package.lower() in requirements:
            print(f"✅ {package}")
        else:
            print(f"❌ {package} (مفقود)")
            all_present = False
    
    return all_present

def check_docker_files():
    """التحقق من ملفات Docker"""
    print("\n🐳 ملفات Docker:")
    files = [
        "Dockerfile",
        ".dockerignore",
    ]
    
    all_exist = True
    for file in files:
        if not check_file_exists(file):
            all_exist = False
    
    return all_exist

def check_railway_files():
    """التحقق من ملفات Railway"""
    print("\n🚂 ملفات Railway:")
    files = [
        "Procfile",
        "railway.json",
        "railway.yaml",
        ".env.railway",
    ]
    
    all_exist = True
    for file in files:
        if not check_file_exists(file):
            all_exist = False
    
    return all_exist

def check_documentation():
    """التحقق من ملفات التوثيق"""
    print("\n📚 ملفات التوثيق:")
    files = [
        "RAILWAY_DEPLOYMENT_GUIDE.md",
        "RAILWAY_SETUP_CHECKLIST.md",
        "RAILWAY_COMMANDS.md",
    ]
    
    all_exist = True
    for file in files:
        if not check_file_exists(file):
            all_exist = False
    
    return all_exist

def check_git():
    """التحقق من Git"""
    print("\n🔧 Git Configuration:")
    if os.path.exists(".git"):
        print("✅ Repository initialized")
        return True
    else:
        print("❌ Repository not initialized")
        print("   Run: git init")
        return False

def main():
    """البرنامج الرئيسي"""
    print("=" * 50)
    print("🚀 Railway Deployment Readiness Check")
    print("=" * 50)
    
    checks = {
        "Docker Files": check_docker_files(),
        "Railway Files": check_railway_files(),
        "Requirements": check_requirements(),
        "Documentation": check_documentation(),
        "Git": check_git(),
    }
    
    missing_vars = check_env_variables()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print("=" * 50)
    
    all_passed = all(checks.values())
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
    
    if missing_vars:
        print(f"\n⚠️  {len(missing_vars)} متغيرات بيئة غير محددة محلياً")
        print("   (هذا طبيعي - يجب تحديدها في Railway dashboard)")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ المشروع جاهز للنشر على Railway!")
        print("\nالخطوات التالية:")
        print("1. ادفع الكود إلى GitHub:")
        print("   git add .")
        print("   git commit -m 'Prepare for Railway deployment'")
        print("   git push origin main")
        print("\n2. اذهب إلى railway.app وأنشئ مشروعاً جديداً")
        print("3. اختر 'Deploy from GitHub'")
        print("4. أضف متغيرات البيئة من .env.railway")
        print("5. حدّث webhook الـ Telegram")
        return 0
    else:
        print("❌ هناك مشاكل يجب حلها قبل النشر")
        return 1

if __name__ == "__main__":
    sys.exit(main())
