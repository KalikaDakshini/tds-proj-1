"""Main file of the application."""

from fastapi import FastAPI

from app.routes import router
from app.services.llm import generate_app


app = FastAPI()
app.include_router(router)


@app.get("/")
async def index():
    """Home page"""
    return {"message": "Welcome to Kalika's App Builder"}
