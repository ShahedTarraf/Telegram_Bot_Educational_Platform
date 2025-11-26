"""
Test Admin ID Configuration
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings

print("\n" + "="*60)
print("🔍 فحص إعدادات الأدمن")
print("="*60)
print(f"📋 TELEGRAM_ADMIN_ID من الإعدادات: {settings.TELEGRAM_ADMIN_ID}")
print(f"📋 نوع البيانات: {type(settings.TELEGRAM_ADMIN_ID)}")
print(f"📋 BOT_TOKEN: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
print("="*60)

# Test comparison
test_id = 982441452
print(f"\n🧪 اختبار المقارنة:")
print(f"   test_id = {test_id}")
print(f"   settings.TELEGRAM_ADMIN_ID = {settings.TELEGRAM_ADMIN_ID}")
print(f"   test_id == settings.TELEGRAM_ADMIN_ID: {test_id == settings.TELEGRAM_ADMIN_ID}")
print("="*60 + "\n")
