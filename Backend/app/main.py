import logging
import os
from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, round1_results, status, users
from app.db.database import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if engine:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed: {e}")
        logger.warning("⚠️  App will run without database. Auth endpoints will still work.")
else:
    logger.warning("⚠️  DATABASE_URL not configured. Running without database.")

# Every handler that talks to Postgres, Supabase or OpenAI is a sync `def`, so
# FastAPI runs it on the anyio worker threads. That pool is the request
# concurrency limit; anything past it queues, which is what we want under load.
THREADPOOL_SIZE = int(os.getenv("THREADPOOL_SIZE", "60"))

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://findyourdate.snioe.dev,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    anyio.to_thread.current_default_thread_limiter().total_tokens = THREADPOOL_SIZE
    logger.info(f"✅ Worker threadpool sized to {THREADPOOL_SIZE}")
    yield


app = FastAPI(title="FindYourDate API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without additional prefix (prefix already in router definition)
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(round1_results.router, prefix="/api/round1", tags=["Round 1 Results"])


@app.get("/")
def root():
    return {"message": "FindYourDate backend is running."}
