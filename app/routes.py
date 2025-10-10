"""App routes module"""

from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from .models import Payload
from .helpers import process_request
from .services import Environ

router = APIRouter()


@router.post("/build")
async def build(request: Payload, tasks: BackgroundTasks):
    """App build endpoint"""

    # Get and validate secret key
    secret_key = Environ.API_SECRET
    if not secret_key:
        raise ValueError("API_SECRET environment variable not set")

    if request.secret != secret_key:
        return JSONResponse(
            content={"message": "Unauthorized: Invalid secret key."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Process task in the background
    tasks.add_task(process_request, request)

    # Return a JSON response confirming receipt
    return JSONResponse(
        content={"message": "Request received. Buildling Application..."},
        status_code=status.HTTP_200_OK,
    )
