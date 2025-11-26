"""
Run Telegram Bot
تشغيل بوت التليجرام
"""
import sys
from pathlib import Path
import io

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the bot
from bot.main import main

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 تشغيل بوت التليجرام - Telegram Bot")
    print("="*60)
    print("📱 Bot is starting...")
    print("="*60 + "\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
