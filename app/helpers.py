"""Helper functions."""

import asyncio
import base64
import time

import httpx
from github.Repository import Repository

from .models import Attachment, Payload
from .services import (
    create_repo,
    enable_pages,
    generate_app,
    get_repo,
    push_code,
    redeploy_pages,
    update_code,
)


def finalize(request: Payload, repo: Repository) -> None:
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
            response = httpx.post(
                url=request.evaluation_url,
                json=data,
                headers=headers,
                timeout=10,
            )
            # Break if succesful
            if response.status_code == httpx.codes.OK:
                print("Posted to evaluation URL")
                break
            print(f"POST request failed. Retrying in {delay} seconds...")
        except httpx.RequestError as err:
            print(f"POST request failed with: {err}. Retrying in {delay} seconds...")

        # Retry POST
        max_delay: int = 64
        time.sleep(delay)
        delay = delay * 2 if delay < max_delay else max_delay


def parse_attachments(attachments: list[Attachment]) -> dict[str, bytes]:
    """Parse attachments from the request."""
    return {a.name: base64.b64decode(a.data.split(",")[-1]) for a in attachments}


async def process_round(request: Payload) -> None:
    """Process the incoming request in the background."""
    # 4 - Parse the attachments
    attachments = parse_attachments(request.attachments)

    # 4 - Use LLM to generate app
    checks = "\n".join(f"- {check}" for check in request.checks)

    # Generate LLM response
    llm_task = asyncio.create_task(generate_app(request.brief, checks))

    if request.round_ == 1:
        # 5 - Create Github repo
        github_task = asyncio.create_task(create_repo(request.task))
    else:
        # Get the repo from task name
        github_task = asyncio.create_task(get_repo(request.task))

    # Await tasks
    llm_response = await llm_task
    repo = await github_task

    # 5 - Push code to repo
    if request.round_ == 1:
        push_code(llm_response, repo, attachments)
    else:
        update_code(llm_response, repo, attachments)

    # 6 - Enable Github pages on round 1
    if request.round_ == 1:
        enable_pages(repo)
    else:
        redeploy_pages(repo)

    # 7. Post to evaluation url
    finalize(request, repo)
    print("Process completed.")
