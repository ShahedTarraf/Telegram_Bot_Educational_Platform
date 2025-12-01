"""
MongoDB Connection - Optimized for Vercel Serverless
"""
import asyncio
import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from config.settings import settings
from database.models.user import User
from database.models.video import Video
from database.models.assignment import Assignment, AssignmentSubmission
from database.models.notification import Notification
from database.models.quiz import Quiz


class Database:
    """Database connection manager - Serverless optimized"""
    client: AsyncIOMotorClient = None
    beanie_initialized: bool = False
    connection_lock: asyncio.Lock = None
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB with retry logic and caching for serverless"""
        # Initialize lock if needed
        if cls.connection_lock is None:
            cls.connection_lock = asyncio.Lock()
        
        # Use lock to prevent multiple simultaneous connection attempts
        async with cls.connection_lock:
            # Return cached connection if already initialized
            if cls.client is not None and cls.beanie_initialized:
                logger.debug("Reusing cached MongoDB connection")
                return True
            
            for attempt in range(1, cls.MAX_RETRIES + 1):
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
                        print(f"ERROR: Failed to mask MongoDB URI: {mask_error}", flush=True)
                    
                    db_name = os.getenv("MONGODB_DB_NAME") or settings.MONGODB_DB_NAME
                    logger.info(f"[Attempt {attempt}/{cls.MAX_RETRIES}] Connecting to MongoDB: {masked_uri}, db={db_name}")
                    print(f"[Attempt {attempt}/{cls.MAX_RETRIES}] Connecting to MongoDB: {masked_uri}, db={db_name}", flush=True)
                    
                    # Create client with optimized timeouts for Vercel
                    # Increased timeouts to handle cold starts
                    cls.client = AsyncIOMotorClient(
                        settings.MONGODB_URL,
                        serverSelectionTimeoutMS=15000,  # 15s for cold start
                        connectTimeoutMS=20000,          # 20s for cold start
                        socketTimeoutMS=20000,           # 20s for operations
                        maxPoolSize=10,                  # Connection pooling
                        minPoolSize=1,                   # Minimum connections
                        maxIdleTimeMS=45000,             # Close idle connections after 45s
                        tlsCAFile=certifi.where(),       # Use certifi CA bundle for reliable TLS
                    )
                    
                    # Test the connection with ping
                    logger.debug("Testing MongoDB connection with ping...")
                    await cls.client.admin.command('ping')
                    logger.info("✅ MongoDB ping successful")
                    print("✅ MongoDB ping successful", flush=True)
                    
                    # Initialize Beanie only once
                    if not cls.beanie_initialized:
                        logger.debug(f"Initializing Beanie with database: {db_name}")
                        await init_beanie(
                            database=cls.client[db_name],
                            document_models=[
                                User,
                                Video,
                                Assignment,
                                AssignmentSubmission,
                                Notification,
                                Quiz,
                            ]
                        )
                        cls.beanie_initialized = True
                        logger.info("✅ Beanie ODM initialized successfully")
                        print("✅ Beanie ODM initialized successfully", flush=True)
                    
                    logger.info("✅ MongoDB connected successfully and Beanie initialized")
                    print("✅ MongoDB connected successfully and Beanie initialized", flush=True)
                    return True
                    
                except Exception as e:
                    error_msg = f"[Attempt {attempt}/{cls.MAX_RETRIES}] MongoDB connection failed: {type(e).__name__}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    print(f"ERROR: {error_msg}", flush=True)
                    import traceback
                    traceback.print_exc()
                    
                    if attempt < cls.MAX_RETRIES:
                        logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                        print(f"Retrying in {cls.RETRY_DELAY} seconds...", flush=True)
                        await asyncio.sleep(cls.RETRY_DELAY)
                    else:
                        error_msg = "❌ Max retries reached. Could not connect to MongoDB."
                        logger.error(error_msg)
                        print(f"ERROR: {error_msg}", flush=True)
                        raise
    
    @classmethod
    async def is_connected(cls) -> bool:
        """Check if database is connected and healthy"""
        # If client is None, try to initialize
        if cls.client is None:
            logger.debug("Database client is None, attempting to initialize")
            try:
                await cls.connect()
            except Exception as e:
                logger.error(f"Failed to initialize database: {repr(e)}")
                return False
        
        # If still not initialized, return False
        if cls.client is None or not cls.beanie_initialized:
            logger.debug(f"Database not ready: client={cls.client is not None}, beanie_initialized={cls.beanie_initialized}")
            return False
        
        try:
            await cls.client.admin.command('ping')
            logger.debug("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {repr(e)}", exc_info=True)
            print(f"ERROR: Health check failed: {repr(e)}", flush=True)
            return False
    
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
