"""
Test Bot Connection
اختبار اتصال البوت
"""
import asyncio
import sys
import io
from pathlib import Path

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Bot
from config.settings import settings

async def test_connection():
    """Test bot connection"""
    print("\n" + "="*60)
    print("🔍 اختبار اتصال البوت - Testing Bot Connection")
    print("="*60)
    
    try:
        print("\n1️⃣ تحميل Token...")
        token = settings.TELEGRAM_BOT_TOKEN
        print(f"✅ Token: {token[:10]}...{token[-10:]}")
        
        print("\n2️⃣ إنشاء Bot...")
        bot = Bot(token=token)
        print("✅ تم إنشاء Bot")
        
        print("\n3️⃣ محاولة الاتصال بـ Telegram...")
        print("⏳ يرجى الانتظار...")
        
        # Try with longer timeout
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
        )
        bot = Bot(token=token, request=request)
        
        async with bot:
            me = await bot.get_me()
            print("\n✅ نجح الاتصال!")
            print(f"📱 اسم البوت: @{me.username}")
            print(f"🤖 Bot ID: {me.id}")
            print(f"👤 الاسم: {me.first_name}")
            return True
            
    except Exception as e:
        print(f"\n❌ فشل الاتصال!")
        print(f"🔴 الخطأ: {type(e).__name__}")
        print(f"📝 الوصف: {str(e)}")
        
        if "Timed out" in str(e) or "timeout" in str(e).lower():
            print("\n💡 نصائح:")
            print("1. تأكد من اتصال الإنترنت")
            print("2. قد يكون Telegram محظوراً في بلدك")
            print("3. جرب استخدام VPN")
            print("4. تأكد من Token صحيح")
        
        return False
    
    finally:
        print("\n" + "="*60)

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
