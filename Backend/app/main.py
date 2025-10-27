from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, chat, auth, status
from app.db.database import Base, engine
import logging

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

app = FastAPI(title="FindYourDate API", version="1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:5173",
        # "http://localhost:5174",
        # "http://Localhost:5173",  # Handle case variation
        # "http://127.0.0.1:5173",
        # "http://127.0.0.1:5174",
        "https://findyourdate.snioe.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without additional prefix (prefix already in router definition)
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])

@app.get("/")
def root():
    return {"message": "FindYourDate backend is running."}

# Add OPTIONS handler for all routes to handle CORS preflight requests
@app.options("/{full_path:path}")
async def options_handler():
    return {}