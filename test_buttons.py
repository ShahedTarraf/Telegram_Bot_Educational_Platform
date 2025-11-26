"""Test if buttons are sent correctly"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Create test keyboard
keyboard = [
    [InlineKeyboardButton("📚 الدورات الاحترافية", callback_data="admin_type_courses")],
    [InlineKeyboardButton("🎓 المواد الجامعية", callback_data="admin_type_materials")],
    [InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")]
]

markup = InlineKeyboardMarkup(keyboard)

print("Keyboard created successfully!")
print(f"Keyboard: {markup}")
print(f"Inline keyboard: {markup.inline_keyboard}")
