# Vercel MongoDB Connection Debugging Guide

## Overview
This guide explains the fixes applied to resolve MongoDB connection failures in the Vercel serverless environment and how to debug issues using the enhanced logging.

---

## Critical Fixes Applied

### 1. **Explicit Database Initialization on Server Startup**

**Problem:** Database connection was only triggered when the bot's `_post_init` was called, which could happen after webhook requests arrived.

**Solution:** Added explicit database initialization in `server.py` startup event:

```python
@app.on_event("startup")
async def on_startup() -> None:
    # Initialize database connection FIRST
    from database.connection import Database
    await Database.connect()
    # Then initialize bot and other services
```

**Why it matters:** Vercel may route requests to your function before all initialization is complete. This ensures MongoDB is ready before any requests arrive.

---

### 2. **Connection Locking for Concurrent Requests**

**Problem:** Multiple simultaneous requests could trigger multiple connection attempts, causing race conditions.

**Solution:** Added `asyncio.Lock` to prevent concurrent connection attempts:

```python
class Database:
    connection_lock: asyncio.Lock = None
    
    @classmethod
    async def connect(cls):
        if cls.connection_lock is None:
            cls.connection_lock = asyncio.Lock()
        
        async with cls.connection_lock:
            # Connection logic here
```

**Why it matters:** In serverless environments, multiple function instances may start simultaneously.

---

### 3. **Comprehensive Error Logging**

**Problem:** Generic error messages like "❌ حدث خطأ" made debugging impossible.

**Solution:** Added detailed logging at every step:

```python
# In registration handler
logger.debug(f"[REGISTRATION] Creating new user: telegram_id={telegram_id}, email={email}")
print(f"[REGISTRATION] Creating new user: telegram_id={telegram_id}, email={email}", flush=True)

# Before save
logger.debug(f"[REGISTRATION] Inserting user into MongoDB...")
await user.insert()

# On error
error_type = type(e).__name__
error_str = str(e)
logger.error(f"[REGISTRATION] FAILED: {error_type}: {error_str}", exc_info=True)
```

**Why it matters:** Vercel logs are your only debugging tool. Every step must be logged.

---

### 4. **Database Health Check Endpoint**

**Problem:** No way to verify database connectivity from outside the application.

**Solution:** Added `/health/db` endpoint:

```python
@app.get("/health/db")
async def db_health_check() -> dict:
    """Database health check endpoint for monitoring."""
    is_connected = await Database.is_connected()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "database": "MongoDB",
        "connected": is_connected,
    }
```

**How to use:**
```bash
curl https://your-vercel-app.vercel.app/health/db
```

---

### 5. **Pre-Connection Verification in Registration**

**Problem:** Errors during `.insert()` were unclear about whether it was a connection issue or validation issue.

**Solution:** Check connection before attempting save:

```python
from database.connection import Database
is_connected = await Database.is_connected()
if not is_connected:
    logger.error(f"Database not connected for user {telegram_id}")
    await update.message.reply_text("❌ خطأ في الاتصال بقاعدة البيانات!")
    return ConversationHandler.END
```

---

## How to Debug Using Vercel Logs

### 1. **Access Vercel Function Logs**

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# View logs in real-time
vercel logs your-project-name --follow
```

### 2. **Look for These Key Log Messages**

**Successful startup:**
```
✅ MongoDB connection established
✅ Beanie ODM initialized successfully
✅ Telegram bot initialized
✅ Server startup completed successfully
```

**Connection failure:**
```
❌ Failed to initialize database: [Error details]
ERROR: [Attempt 1/3] MongoDB connection failed: [Error type]: [Error message]
```

**Registration success:**
```
✅ [REGISTRATION] New user registered: Ahmed Mohamed (ID: 123456789)
```

**Registration failure:**
```
[REGISTRATION] ❌ FAILED for telegram_id=123456789, email=user@example.com
Error Type: ValidationError
Error Message: [Specific validation error]
[REGISTRATION] Traceback: [Full Python traceback]
```

---

## Common Issues and Solutions

### Issue 1: `beanie.exceptions.CollectionWasNotInitialized`

**Cause:** Beanie models are being used before `init_beanie()` is called.

**Check:**
1. Verify database initialization in startup logs
2. Check if `✅ Beanie ODM initialized successfully` appears

**Fix:**
- Ensure `await Database.connect()` is called in `server.py` startup
- Verify all Document models are in the `document_models` list in `connection.py`

---

### Issue 2: `pymongo.errors.ServerSelectionTimeoutError`

**Cause:** Cannot reach MongoDB server (network, credentials, or IP whitelist issue).

**Check:**
1. Verify `MONGODB_URL` environment variable is set in Vercel
2. Check MongoDB Atlas Network Access: should be `0.0.0.0/0` for Vercel
3. Verify credentials in the connection string

**Fix:**
```bash
# Test connection locally
python -c "from database.connection import Database; import asyncio; asyncio.run(Database.connect())"
```

---

### Issue 3: `pymongo.errors.OperationFailure: authentication failed`

**Cause:** MongoDB credentials are incorrect or special characters aren't encoded.

**Check:**
1. Verify username and password in `MONGODB_URL`
2. Special characters (like `$`) must be URL-encoded (`%24`)

**Example:**
```
# Wrong (if password contains $)
mongodb+srv://user:pass$word@cluster.mongodb.net/db

# Correct
mongodb+srv://user:pass%24word@cluster.mongodb.net/db
```

**Fix:**
- Go to MongoDB Atlas → Database Access
- Reset password and copy the connection string
- Ensure it's URL-encoded

---

### Issue 4: `pymongo.errors.DuplicateKeyError`

**Cause:** Trying to insert a document with a duplicate unique field (email or telegram_id).

**Check:**
- Look for log: `[REGISTRATION] Duplicate key error for email=...`
- Check MongoDB Atlas → Collections → users for existing documents

**Fix:**
- User should use a different email
- Or admin should delete the duplicate document from MongoDB

---

### Issue 5: `ValidationError` on User creation

**Cause:** Data doesn't match the User schema.

**Check:**
- Look for log: `[REGISTRATION] Validation error: [error details]`
- Verify User model schema in `database/models/user.py`

**Required fields:**
- `telegram_id` (int, unique)
- `full_name` (str)
- `phone` (str)
- `email` (EmailStr, unique)

**Fix:**
- Ensure all required fields are provided
- Verify data types match schema

---

## Monitoring Checklist

### Before Deploying to Vercel

- [ ] Test locally: `python server.py`
- [ ] Check logs for `✅ MongoDB connected successfully`
- [ ] Test registration: `/start` → provide name, phone, email
- [ ] Verify user appears in MongoDB Atlas

### After Deploying to Vercel

- [ ] Check Vercel deployment logs for startup messages
- [ ] Test health endpoint: `curl https://your-app.vercel.app/health/db`
- [ ] Test registration via Telegram bot
- [ ] Check Vercel function logs for registration logs
- [ ] Verify user appears in MongoDB Atlas

---

## Environment Variables Required in Vercel

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_ID=your_admin_id
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/db?retryWrites=true&w=majority
MONGODB_DB_NAME=educational_platform
BOT_WEBHOOK_URL=https://your-app.vercel.app/webhook
SECRET_KEY=your_secret_key
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAIL=admin@example.com
SHAP_CASH_NUMBER=your_number
HARAM_NUMBER=your_number
```

---

## Log Filtering in Vercel

### View only errors:
```bash
vercel logs your-project-name --follow | grep ERROR
```

### View only registration logs:
```bash
vercel logs your-project-name --follow | grep REGISTRATION
```

### View only database logs:
```bash
vercel logs your-project-name --follow | grep "MongoDB\|Beanie"
```

---

## Performance Tips for Vercel

1. **Connection Caching:** The database connection is cached globally, so subsequent requests reuse it
2. **Timeouts:** Set to 20 seconds to handle cold starts
3. **Connection Pool:** Max 10 connections to avoid exhausting Vercel limits
4. **Idle Timeout:** 45 seconds to close stale connections

---

## Testing Database Operations

### Test User Registration
```python
import asyncio
from database.connection import Database
from database.models.user import User

async def test_registration():
    await Database.connect()
    
    user = User(
        telegram_id=123456789,
        full_name="Test User",
        phone="+963999999999",
        email="test@example.com"
    )
    
    await user.insert()
    print(f"✅ User created: {user.id}")

asyncio.run(test_registration())
```

### Test User Fetch
```python
async def test_fetch():
    await Database.connect()
    
    user = await User.find_one(User.telegram_id == 123456789)
    print(f"✅ User found: {user.full_name if user else 'Not found'}")

asyncio.run(test_fetch())
```

---

## Support & Next Steps

If you still encounter issues:

1. **Collect logs:** Run `vercel logs your-project-name > logs.txt`
2. **Check error type:** Look for the specific error message
3. **Verify environment:** Ensure all env vars are set in Vercel
4. **Test locally:** Reproduce the issue locally first
5. **Check MongoDB Atlas:** Verify database, collections, and network access

---

## Summary of Changes

| File | Changes |
|------|---------|
| `database/connection.py` | Added connection lock, enhanced logging, health check method |
| `bot/handlers/start.py` | Added pre-connection verification, comprehensive error logging |
| `server.py` | Added explicit DB initialization on startup, health check endpoints |

All changes maintain backward compatibility and don't affect existing bot logic.
