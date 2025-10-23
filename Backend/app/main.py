from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, chat, match, auth
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FindYourDate API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_users.router, prefix="/users", tags=["Users"])
app.include_router(routes_chat.router, prefix="/chat", tags=["Chat"])
app.include_router(routes_match.router, prefix="/match", tags=["Matchmaking"])
app.include_router(routes_auth.router, prefix="/auth", tags=["Auth"])

@app.get("/")
def root():
    return {"message": "FindYourDate backend is running."}