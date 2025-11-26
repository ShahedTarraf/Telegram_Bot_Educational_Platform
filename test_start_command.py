"""
اختبار أمر /start مباشرة
Test /start command directly
"""
import asyncio
import sys
import io
from pathlib import Path

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Bot, Update
from telegram.request import HTTPXRequest
from config.settings import settings

async def test_start():
    """Test /start command"""
    print("\n" + "=" * 60)
    print("🧪 اختبار أمر /start - Testing /start Command")
    print("=" * 60)
    
    try:
        # Create bot
        print("\n1️⃣ إنشاء Bot...")
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
        )
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, request=request)
        
        async with bot:
            # Get bot info
            me = await bot.get_me()
            print(f"✅ البوت: @{me.username}")
            print(f"   Bot ID: {me.id}")
            
            # Get updates
            print("\n2️⃣ جلب آخر الرسائل...")
            updates = await bot.get_updates(limit=10, timeout=5)
            
            if not updates:
                print("\n⚠️  لا توجد رسائل جديدة")
                print("\n💡 للاختبار:")
                print(f"   1. افتح Telegram")
                print(f"   2. ابحث عن: @{me.username}")
                print(f"   3. اكتب: /start")
                print(f"   4. شغّل هذا الاختبار مرة أخرى")
                return
            
            print(f"✅ عدد الرسائل الجديدة: {len(updates)}")
            
            # Show recent messages
            print("\n3️⃣ آخر الرسائل:")
            for update in updates[-5:]:
                if update.message:
                    user = update.message.from_user
                    text = update.message.text or "[لا يوجد نص]"
                    print(f"   • من: {user.first_name} (@{user.username})")
                    print(f"     ID: {user.id}")
                    print(f"     الرسالة: {text}")
                    
                    # Check if it's admin
                    is_admin = user.id == settings.TELEGRAM_ADMIN_ID
                    print(f"     {'🔑 Admin' if is_admin else '👤 Student'}")
                    print()
            
            # Check if bot is responding
            print("\n4️⃣ حالة البوت:")
            print("   ✅ البوت متصل بـ Telegram")
            print("   ✅ يمكنه استقبال الرسائل")
            
            # Get admin info
            print(f"\n5️⃣ معلومات الأدمن:")
            print(f"   Admin ID المحدد في .env: {settings.TELEGRAM_ADMIN_ID}")
            
            # Instructions
            print("\n" + "=" * 60)
            print("📋 التعليمات:")
            print("=" * 60)
            print("\n1. تأكد أن البوت يعمل:")
            print("   python run_bot.py")
            print()
            print("2. افتح Telegram وأرسل /start للبوت:")
            print(f"   @{me.username}")
            print()
            print("3. يجب أن يرد البوت خلال ثانية!")
            print()
            print("4. إذا لم يرد:")
            print("   - تحقق أن البوت يعمل (python run_bot.py)")
            print("   - تحقق من اتصال الإنترنت/VPN")
            print("   - انتظر 10 ثواني ثم جرب مرة أخرى")
            print()
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_start())
