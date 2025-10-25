from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, chat
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

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "FindYourDate backend is running."}