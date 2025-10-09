"""Main file of the application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router


app = FastAPI()
app.include_router(router)

# Add CORS. Allow all origins (for testing / public API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def index():
    """Home page"""
    return {"message": "Welcome to Kalika's App Builder"}
