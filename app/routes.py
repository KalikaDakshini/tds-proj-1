"""App routes."""

import asyncio

from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from .helpers import process_round
from .models import Payload
from .services import Environ

router = APIRouter()


@router.post("/build")
async def build(request: Payload, tasks: BackgroundTasks) -> JSONResponse:
    """App build endpoint."""
    # Get and validate secret key
    secret_key = Environ.API_SECRET
    if not secret_key:
        raise ValueError("API_SECRET environment variable not set")

    if request.secret != secret_key:
        return JSONResponse(
            content={"message": "Unauthorized: Invalid secret key."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Select the appropriate function based on round call
    tasks.add_task(lambda: asyncio.run(process_round(request)))

    # Return a JSON response confirming receipt
    return JSONResponse(
        content={"message": "Request received. Buildling Application..."},
        status_code=status.HTTP_200_OK,
    )
