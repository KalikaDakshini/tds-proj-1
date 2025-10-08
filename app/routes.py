"""App routes module"""

import time
import requests
from requests.exceptions import RequestException
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse
from github.Repository import Repository

from .models import Payload
from .services.gh_actions import create_repo, push_code, enable_pages
from .services.llm import generate_app
from .config import Environ

router = APIRouter()


def finalize(request: Payload, repo: Repository):
    """Send a POST request to evaluation URL with repository details."""
    # Build data
    owner, repo_name = repo.full_name.split("/")
    data = {
        "email": request.email,
        "task": request.task,
        "round": 1,
        "nonce": request.nonce,
        "repo_url": f"https://github.com/{owner}/{repo_name}",
        "commit_sha": repo.get_commits()[0].sha,
        "pages_url": "https://{owner}.github.io/{repo_name}/",
    }
    # Build header
    headers = {
        "Content-Type": "application/json",
    }
    # Send POST requests till successful
    delay = 1
    while True:
        try:
            response = requests.post(
                url=request.evaluation_url,
                json=data,
                headers=headers,
                timeout=5,
            )
            # Break if succesful
            if response.ok:
                print("Posted to evaluation URL")
                break
            print(f"POST request failed. Retrying in {delay} seconds...")
        except RequestException as err:
            print(
                f"POST request failed with {err.errno}. Retrying in {delay} seconds..."
            )

        # Retry POST
        time.sleep(delay)
        delay = delay * 2 if delay < 16 else 16


def process_request(request: Payload):
    """Process the incoming request in the background."""
    # 4 - Parse the attachments

    # 4 - Use LLM to generate app
    checks = "\n".join(f"- {check}" for check in request.checks)
    llm_response = generate_app(request.brief, checks)

    # 5 - Create Github repo
    repo = create_repo(request.task)
    print(f"Repository '{repo.name}' created at {repo.html_url}")

    # 5 - Push code to repo
    push_code(llm_response, repo)

    # 6 - Enable Github pages
    enable_pages(repo)

    # 7. Post to evaluation url
    finalize(request, repo)
    print("Process completed.")


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
