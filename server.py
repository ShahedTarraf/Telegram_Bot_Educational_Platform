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


# Create Telegram bot application
telegram_app = create_application()

# Main FastAPI application
app = FastAPI(title="Educational Platform - Unified Server")

# Mount admin dashboard under /admin
app.mount("/admin", dashboard_app)


@app.on_event("startup")
async def on_startup() -> None:
    """Startup logic for unified server."""
    # Start Telegram bot (webhook mode)
    await telegram_app.initialize()
    await telegram_app.start()

    webhook_url = settings.BOT_WEBHOOK_URL
    if webhook_url:
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.warning("BOT_WEBHOOK_URL is not set; skipping set_webhook")

    # Start background notification scheduler
    app.state.notification_scheduler_task = asyncio.create_task(
        NotificationScheduler.start_notification_scheduler()
    )
    logger.info("Notification scheduler started")


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
    return {
        "status": "ok",
        "service": "Educational Platform",
        "bot_webhook": True,
        "admin_dashboard": True,
    }


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """Telegram webhook endpoint."""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("server:app", host=settings.HOST, port=port, reload=settings.DEBUG)
