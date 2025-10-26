import os
import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import auth
from dotenv import load_dotenv
load_dotenv()

HOST = os.environ.get('HOST', "0.0.0.0")
PORT = os.environ.get('PORT', 3000)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "FindYourDate"}


uvicorn.run(app, host=HOST, port=PORT)
