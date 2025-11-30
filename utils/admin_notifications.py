"""
Admin Notification Utilities
"""
from loguru import logger
from config.settings import settings


async def send_admin_error(bot, error_msg: str, error_type: str = "ERROR", user_id: int = None):
    """
    Send error notification to admin
    
    Args:
        bot: Telegram bot instance
        error_msg: Error message to send
        error_type: Type of error (ERROR, WARNING, CRITICAL)
        user_id: User ID that caused the error (optional)
    """
    try:
        # Format the message
        emoji = {
            "ERROR": "❌",
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
        }.get(error_type, "❌")
        
        message = f"{emoji} **{error_type}**\n\n"
        message += f"{error_msg}\n\n"
        
        if user_id:
            message += f"👤 User ID: `{user_id}`\n"
        
        message += f"⏰ Time: `{logger._core.handlers[0].formatter.format(logger.make_record('', 0, '', 0, '', (), None))}`"
        
        # Send to admin
        await bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_ID,
            text=message,
            parse_mode="Markdown"
        )
        logger.debug(f"Admin notification sent: {error_type}")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {repr(e)}")
        print(f"ERROR: Failed to send admin notification: {repr(e)}", flush=True)


async def send_admin_info(bot, info_msg: str, title: str = "INFO"):
    """
    Send info notification to admin
    
    Args:
        bot: Telegram bot instance
        info_msg: Info message to send
        title: Title of the message
    """
    try:
        message = f"ℹ️ **{title}**\n\n{info_msg}"
        
        await bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_ID,
            text=message,
            parse_mode="Markdown"
        )
        logger.debug(f"Admin info sent: {title}")
    except Exception as e:
        logger.error(f"Failed to send admin info: {repr(e)}")
        print(f"ERROR: Failed to send admin info: {repr(e)}", flush=True)
