#!/usr/bin/env python3
"""
Verification Script - Test All Fixes
"""
import asyncio
import sys
import os

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

async def test_database_connection():
    """Test 1: Database Connection with Retry Logic"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection with Retry Logic")
    print("="*60)
    
    try:
        from database.connection import Database
        result = await Database.connect()
        if result:
            logger.info("[OK] Database connection successful with retry logic")
            return True
        else:
            logger.error("[ERROR] Database connection failed")
            return False
    except Exception as e:
        logger.error("[ERROR] Database connection test failed: " + repr(e))
        return False

async def test_error_logging():
    """Test 2: Error Logging in Handlers"""
    print("\n" + "="*60)
    print("TEST 2: Error Logging in Handlers")
    print("="*60)
    
    try:
        # Check if error handling is in place
        import inspect
        from bot.handlers import courses, materials, content
        
        handlers = [
            ("courses.show_course_details", courses.show_course_details),
            ("materials.show_material_details", materials.show_material_details),
            ("content.show_videos", content.show_videos),
        ]
        
        all_good = True
        for name, handler in handlers:
            source = inspect.getsource(handler)
            if "except Exception" in source and "logger.error" in source:
                logger.info(f"[OK] {name}: Error handling + logging present")
            else:
                logger.warning(f"[WARN] {name}: Error handling might be incomplete")
                all_good = False
        
        return all_good
    except Exception as e:
        logger.error(f"[ERROR] Error logging test failed: {repr(e)}")
        return False

async def test_dashboard_error_handling():
    """Test 3: Dashboard Error Handling"""
    print("\n" + "="*60)
    print("TEST 3: Dashboard Error Handling")
    print("="*60)
    
    try:
        import inspect
        from admin_dashboard import app as dashboard_app
        
        # Check dashboard function
        source = inspect.getsource(dashboard_app.dashboard)
        
        checks = {
            "try-catch blocks": "try:" in source,
            "fallback values": "pending_approvals = 0" in source or "recent_users = []" in source,
            "error logging": "logger.error" in source,
        }
        
        all_good = True
        for check_name, result in checks.items():
            if result:
                logger.info(f"[OK] Dashboard: {check_name} present")
            else:
                logger.warning(f"[WARN] Dashboard: {check_name} missing")
                all_good = False
        
        return all_good
    except Exception as e:
        logger.error(f"[ERROR] Dashboard error handling test failed: {repr(e)}")
        return False

async def test_connection_retry_logic():
    """Test 4: Connection Retry Logic"""
    print("\n" + "="*60)
    print("TEST 4: Connection Retry Logic")
    print("="*60)
    
    try:
        import inspect
        from database.connection import Database
        
        source = inspect.getsource(Database.connect)
        
        checks = {
            "retry loop": "for attempt in range" in source,
            "retry delay": "asyncio.sleep" in source,
            "connection timeout": "serverSelectionTimeoutMS" in source,
            "connection verification": "ping" in source,
        }
        
        all_good = True
        for check_name, result in checks.items():
            if result:
                logger.info(f"[OK] Connection retry: {check_name} present")
            else:
                logger.warning(f"[WARN] Connection retry: {check_name} missing")
                all_good = False
        
        return all_good
    except Exception as e:
        logger.error(f"[ERROR] Connection retry logic test failed: {repr(e)}")
        return False

async def test_environment_variables():
    """Test 5: Environment Variables"""
    print("\n" + "="*60)
    print("TEST 5: Environment Variables")
    print("="*60)
    
    try:
        from config.settings import settings
        
        required_vars = {
            "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_ADMIN_ID": settings.TELEGRAM_ADMIN_ID,
            "MONGODB_URL": settings.MONGODB_URL,
            "MONGODB_DB_NAME": settings.MONGODB_DB_NAME,
            "SECRET_KEY": settings.SECRET_KEY,
            "ADMIN_PASSWORD": settings.ADMIN_PASSWORD,
        }
        
        all_good = True
        for var_name, var_value in required_vars.items():
            if var_value:
                logger.info(f"[OK] {var_name}: Set")
            else:
                logger.error(f"[ERROR] {var_name}: Not set")
                all_good = False
        
        return all_good
    except Exception as e:
        logger.error(f"[ERROR] Environment variables test failed: {repr(e)}")
        return False

async def test_documentation():
    """Test 6: Documentation Files"""
    print("\n" + "="*60)
    print("TEST 6: Documentation Files")
    print("="*60)
    
    try:
        from pathlib import Path
        
        docs = [
            "DEBUGGING_GUIDE.md",
            "FIXES_SUMMARY.md",
            "QUICK_START_AFTER_FIXES.md",
            "COMPLETE_ANALYSIS_AND_FIXES.md",
        ]
        
        all_good = True
        for doc in docs:
            doc_path = Path(f"d:\\bot_telegram\\Educational_Platform\\{doc}")
            if doc_path.exists():
                logger.info(f"[OK] {doc}: Present")
            else:
                logger.warning(f"[WARN] {doc}: Missing")
                all_good = False
        
        return all_good
    except Exception as e:
        logger.error(f"[ERROR] Documentation test failed: {repr(e)}")
        return False

async def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("VERIFICATION SCRIPT - ALL FIXES")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["Database Connection"] = await test_database_connection()
    results["Error Logging"] = await test_error_logging()
    results["Dashboard Error Handling"] = await test_dashboard_error_handling()
    results["Connection Retry Logic"] = await test_connection_retry_logic()
    results["Environment Variables"] = await test_environment_variables()
    results["Documentation"] = await test_documentation()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} | {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        logger.info("All fixes verified successfully!")
        return 0
    else:
        logger.warning(f"{total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
