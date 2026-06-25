import asyncio
import time
import logging
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load env variables first
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from my_agent.auth.database import init_db
from my_agent.auth.router import router

# Set up logging for auth server
auth_log_path = os.getenv(
    "AUTH_SERVER_LOG_FILE",
    os.path.join(os.path.dirname(__file__), "auth_server.log"),
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(auth_log_path, encoding="utf-8")
    ]
)
logger = logging.getLogger("auth_server")

app = FastAPI(
    title="X-Agent Authentication Server",
    description="Microservice handling Email OTP (via Brevo) and Google OAuth authentications.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(router, prefix="/auth")

@app.get("/")
async def root():
    return {"status": "online", "service": "X-Agent Auth Server"}

async def guest_cleanup_loop():
    """Background loop that cleans up guest session artifact folders that haven't been updated in 24 hours"""
    logger.info("Guest session background cleanup worker started.")
    while True:
        try:
            users_dir = Path(__file__).parent / ".adk" / "artifacts" / "users"
            if users_dir.exists():
                logger.info(f"Scanning guest session directories in: {users_dir}")
                now = time.time()
                cleaned_count = 0
                for guest_dir in users_dir.iterdir():
                    if guest_dir.is_dir() and guest_dir.name.startswith("guest_"):
                        # Get modified time of the guest directory
                        mtime = guest_dir.stat().st_mtime
                        age_seconds = now - mtime
                        age_hours = age_seconds / 3600
                        
                        # Clean if older than 24 hours
                        if age_hours > 24:
                            logger.info(f"Deleting idle guest directory (age: {age_hours:.1f} hours): {guest_dir}")
                            shutil.rmtree(guest_dir)
                            cleaned_count += 1
                if cleaned_count > 0:
                    logger.info(f"Guest session cleanup done. Removed {cleaned_count} guest directory/directories.")
            else:
                logger.debug(f"Guest artifact directory {users_dir} does not exist yet. Skipping scan.")
        except Exception as e:
            logger.error(f"Error in guest cleanup background task: {str(e)}")
            
        # Run scan every 1 hour (3600 seconds)
        await asyncio.sleep(3600)

@app.on_event("startup")
async def on_startup():
    # 1. Initialize SQLite tables and index
    logger.info("Initializing SQLite database...")
    init_db()
    logger.info("Database initialized successfully.")
    
    # 2. Run guest cleanup background loop task
    asyncio.create_task(guest_cleanup_loop())

if __name__ == "__main__":
    import uvicorn
    # When running directly: python auth_server.py
    logger.info("Starting uvicorn server on port 8001...")
    uvicorn.run("auth_server:app", host="127.0.0.1", port=8001, reload=True)
