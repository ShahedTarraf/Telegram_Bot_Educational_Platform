"""Unified server entrypoint for Educational Platform.

Runs:
- Telegram bot in webhook mode
- Admin dashboard
- Background notification scheduler

Provides a health check at root path "/".
"""

import os
import asyncio

from fastapi import FastAPI, Request
from loguru import logger
from telegram import Update

from config.settings import settings
from bot.main import create_application
from admin_dashboard.app import app as dashboard_app
from utils.notifications import NotificationScheduler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or settings.TELEGRAM_BOT_TOKEN
MONGODB_URL = os.environ.get("MONGODB_URL") or settings.MONGODB_URL
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME") or settings.MONGODB_DB_NAME
BOT_WEBHOOK_URL = os.environ.get("BOT_WEBHOOK_URL") or settings.BOT_WEBHOOK_URL


# Create Telegram bot application
telegram_app = create_application()

# Main FastAPI application
app = FastAPI(title="Educational Platform - Unified Server")

# Mount admin dashboard under /admin
app.mount("/admin", dashboard_app)


@app.on_event("startup")
async def on_startup() -> None:
    """Startup logic for unified server."""
    logger.info("🚀 Starting Educational Platform server...")
    print("🚀 Starting Educational Platform server...", flush=True)
    
    # Initialize database connection FIRST
    try:
        from database.connection import Database
        logger.info("📡 Initializing MongoDB connection...")
        print("📡 Initializing MongoDB connection...", flush=True)
        await Database.connect()
        logger.info("✅ MongoDB connection established")
        print("✅ MongoDB connection established", flush=True)
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {repr(e)}", exc_info=True)
        print(f"❌ Failed to initialize database: {repr(e)}", flush=True)
        raise
    
    # Start Telegram bot (webhook mode)
    try:
        logger.info("🤖 Initializing Telegram bot...")
        print("🤖 Initializing Telegram bot...", flush=True)
        await telegram_app.initialize()
        await telegram_app.start()
        logger.info("✅ Telegram bot initialized")
        print("✅ Telegram bot initialized", flush=True)

        webhook_url = BOT_WEBHOOK_URL
        if webhook_url:
            await telegram_app.bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Webhook set to {webhook_url}")
            print(f"✅ Webhook set to {webhook_url}", flush=True)
        else:
            logger.warning("⚠️ BOT_WEBHOOK_URL is not set; skipping set_webhook")
            print("⚠️ BOT_WEBHOOK_URL is not set; skipping set_webhook", flush=True)
    except Exception as e:
        logger.error(f"❌ Failed to initialize Telegram bot: {repr(e)}", exc_info=True)
        print(f"❌ Failed to initialize Telegram bot: {repr(e)}", flush=True)
        raise

    # Start background notification scheduler
    try:
        logger.info("📬 Starting notification scheduler...")
        print("📬 Starting notification scheduler...", flush=True)
        app.state.notification_scheduler_task = asyncio.create_task(
            NotificationScheduler.start_notification_scheduler()
        )
        logger.info("✅ Notification scheduler started")
        print("✅ Notification scheduler started", flush=True)
    except Exception as e:
        logger.error(f"❌ Failed to start notification scheduler: {repr(e)}", exc_info=True)
        print(f"❌ Failed to start notification scheduler: {repr(e)}", flush=True)
    
    logger.info("✅ Server startup completed successfully")
    print("✅ Server startup completed successfully", flush=True)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Shutdown logic for unified server."""
    # Stop background scheduler
    task = getattr(app.state, "notification_scheduler_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Stop Telegram bot
    await telegram_app.stop()
    await telegram_app.shutdown()


@app.get("/")
async def health_check() -> dict:
    """Health check endpoint."""
    from database.connection import Database
    db_connected = await Database.is_connected()
    return {
        "status": "healthy",
        "service": "Educational Platform",
        "bot_webhook": True,
        "admin_dashboard": True,
        "database": "connected" if db_connected else "disconnected",
    }


@app.get("/health/db")
async def db_health_check() -> dict:
    """Database health check endpoint for monitoring."""
    from database.connection import Database
    try:
        is_connected = await Database.is_connected()
        if is_connected:
            return {
                "status": "healthy",
                "database": "MongoDB",
                "connected": True,
            }
        else:
            return {
                "status": "unhealthy",
                "database": "MongoDB",
                "connected": False,
                "error": "Database not initialized",
            }
    except Exception as e:
        logger.error(f"Database health check failed: {repr(e)}")
        return {
            "status": "unhealthy",
            "database": "MongoDB",
            "connected": False,
            "error": str(e),
        }


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """Telegram webhook endpoint."""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        # Log to both logger and stdout for Vercel visibility
        logger.error(f"Webhook processing error: {repr(e)}", exc_info=True)
        print(f"ERROR: Webhook processing failed: {repr(e)}", flush=True)
        import traceback
        traceback.print_exc()
        # Return 200 OK to Telegram (so it doesn't retry)
        # but log the error for debugging
        return {"ok": True, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("server:app", host=settings.HOST, port=port, reload=settings.DEBUG)
