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
