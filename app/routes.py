"""App routes module"""

import os
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from .models import Payload
from .services.gh_actions import create_repo

router = APIRouter()


def process_request(request: Payload):
    """Process the incoming request in the background."""
    # 4 - Parse the request and attachments

    # 4 - Use LLM to generate app

    # 5 - Create Github repo
    repo = create_repo(request.task)
    print(f"Repository '{repo.name}' created at {repo.html_url}")

    # 5 - Push code to repo

    # 6 - Enable Github pages

    # 7. Post to evaluation url


@router.post("/build")
async def build(request: Payload, tasks: BackgroundTasks):
    """App build endpoint"""

    # Get and validate secret key
    secret_key = os.getenv("API_SECRET")
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
