"""Main file of the application."""

from dotenv import load_dotenv
from fastapi import FastAPI

from app.routes import router


app = FastAPI()
app.include_router(router)

load_dotenv()


@app.get("/")
async def index():
    """Home page"""
    return {"message": "Welcome to Kalika's App Builder"}
