from typing import Any, Dict

from fastapi import FastAPI, Request
from loguru import logger
from telegram import Update

from server import telegram_app, BOT_WEBHOOK_URL


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize the shared Telegram application and set the webhook."""
    await telegram_app.initialize()
    await telegram_app.start()

    webhook_url = BOT_WEBHOOK_URL
    if webhook_url:
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.warning("BOT_WEBHOOK_URL is not set; skipping set_webhook")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Shutdown the shared Telegram application."""
    await telegram_app.stop()
    await telegram_app.shutdown()


@app.post("/")
@app.post("/api/webhook")
async def telegram_webhook(request: Request) -> Dict[str, Any]:
    """Telegram webhook endpoint (POST-only)."""
    data = await request.json()
    logger.debug(f"Webhook received raw JSON: {data}")
    update = Update.de_json(data, telegram_app.bot)
    try:
        logger.debug(f"Webhook Update.to_dict: {update.to_dict() if isinstance(update, Update) else update}")
    except Exception as e:
        logger.error(f"Failed to serialize Update in webhook debug logging: {e}")
    await telegram_app.process_update(update)
    logger.debug("Webhook update processed successfully")
    return {"ok": True}
