"""
MongoDB Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from config.settings import settings
from database.models.user import User
from database.models.video import Video
from database.models.assignment import Assignment
from database.models.notification import Notification


class Database:
    """Database connection manager"""
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        try:
            # Debug: log MongoDB URI (masked) and DB name
            masked_uri = settings.MONGODB_URL
            try:
                if "@" in settings.MONGODB_URL and "://" in settings.MONGODB_URL:
                    prefix, rest = settings.MONGODB_URL.split("://", 1)
                    creds_and_host = rest.split("@", 1)
                    if len(creds_and_host) == 2:
                        _, host_part = creds_and_host
                        masked_uri = f"{prefix}://***:***@{host_part}"
            except Exception as mask_error:
                logger.error(f"Failed to mask MongoDB URI for debug logging: {mask_error}")
            logger.debug(f"MongoDB debug config -> uri={masked_uri}, db={settings.MONGODB_DB_NAME}")
            logger.info(f"Connecting to MongoDB: {settings.MONGODB_URL}")
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            
            # Initialize Beanie
            await init_beanie(
                database=cls.client[settings.MONGODB_DB_NAME],
                document_models=[
                    User,
                    Video,
                    Assignment,
                    Notification,
                ]
            )
            
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")


# Convenience function
async def init_db():
    """Initialize database"""
    await Database.connect()


async def close_db():
    """Close database"""
    await Database.close()
