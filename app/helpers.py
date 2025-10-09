"""Helper functions"""

import base64
import time
import requests

from requests.exceptions import RequestException
from github.Repository import Repository
from .services.gh_actions import create_repo, push_code, enable_pages
from .services.llm import generate_app
from .models import Payload, Attachment


def finalize(request: Payload, repo: Repository):
    """Send a POST request to evaluation URL with repository details."""
    # Build data
    owner, repo_name = repo.full_name.split("/")
    data = {
        "email": request.email,
        "task": request.task,
        "round": request.round_,
        "nonce": request.nonce,
        "repo_url": f"https://github.com/{owner}/{repo_name}",
        "commit_sha": repo.get_commits()[0].sha,
        "pages_url": f"https://{owner}.github.io/{repo_name}/",
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
        delay = delay * 2 if delay < 64 else 64


def parse_attachments(attachments: list[Attachment]) -> dict[str, bytes]:
    """Parse attachments from the request."""
    return {
        a.name: base64.b64decode(a.data.split(",")[-1]) for a in attachments
    }


def process_request(request: Payload):
    """Process the incoming request in the background."""
    # 4 - Parse the attachments
    attachments = parse_attachments(request.attachments)

    # 4 - Use LLM to generate app
    checks = "\n".join(f"- {check}" for check in request.checks)
    llm_response = generate_app(request.brief, checks)

    # 5 - Create Github repo
    repo = create_repo(request.task)
    print(f"Repository '{repo.name}' created at {repo.html_url}")

    # 5 - Push code to repo
    push_code(llm_response, repo, attachments)

    # 6 - Enable Github pages
    enable_pages(repo)

    # 7. Post to evaluation url
    finalize(request, repo)
    print("Process completed.")
