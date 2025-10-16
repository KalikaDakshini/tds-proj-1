"""Github Actions."""

import asyncio
import time

import httpx
from github import Auth, Github, GithubException, UnknownObjectException
from github.Repository import Repository

from app.models import LLMResponse

from .config import Environ


async def get_repo(name: str) -> Repository:
    """Get the repository from name."""
    print(f"Getting repository: {name}")
    return await asyncio.to_thread(_get_repo_async, name)


def _get_repo_async(name: str) -> Repository:
    # Authenticate to GitHub
    token = Environ.GITHUB_TOKEN
    auth = Auth.Token(token)
    with Github(auth=auth) as git:
        user = git.get_user()
        # Search for the repository and return it
        return user.get_repo(name)  # type: ignore[attr-access]


async def create_repo(name: str) -> Repository:
    """Create a new GitHub repository if it doesn't exist."""
    print(f"Creating repository: {name}")
    return await asyncio.to_thread(_create_repo_async, name)


def _create_repo_async(name: str) -> Repository:
    # Authenticate to GitHub
    token = Environ.GITHUB_TOKEN
    auth = Auth.Token(token)
    with Github(auth=auth) as git:
        user = git.get_user()

        # Delete repo if it exists
        try:
            repo = user.get_repo(name)
            repo.delete()
        except UnknownObjectException:
            pass

        # Create a new repository and return it
        return user.create_repo(name)  # type: ignore[attr-access]


def push_code(
    llm_response: LLMResponse,
    repo: Repository,
    attachments: dict[str, bytes],
) -> None:
    """Create (push) new code files to GitHub Repo."""
    print("Pushing new files to repository...")

    # Add all files generate to repo
    for field_name, field in type(llm_response).model_fields.items():
        file_content = getattr(llm_response, field_name)
        file_name = field.title if field.title else field_name
        if file_content:
            try:
                repo.create_file(
                    file_name, f"Add {file_name}", file_content, branch="main"
                )
            except GithubException as e:
                print(f"Failed to create {file_name}: {e}")

    # Add all attachments
    for file_name, file_data in attachments.items():
        try:
            repo.create_file(file_name, f"Add {file_name}", file_data, branch="main")
        except GithubException as e:
            print(f"Failed to create {file_name}: {e}")


def update_code(
    llm_response: LLMResponse,
    repo: Repository,
    attachments: dict[str, bytes],
) -> None:
    """Update or create code files in GitHub Repo if they exist."""
    print("Updating files in repository...")

    def update_or_create_file(file_name: str, content: bytes | str) -> None:
        """Create file if it doesn't exist, else update it."""
        # Try updating file
        try:
            existing_file = repo.get_contents(file_name, ref="main")
            if isinstance(existing_file, list):
                existing_file = existing_file[0]

            repo.update_file(
                existing_file.path,
                f"Updated {file_name}",
                content,
                existing_file.sha,
                branch="main",
            )

        # Create file if not present
        except GithubException as e:
            if e.status == httpx.codes.NOT_FOUND:
                repo.create_file(file_name, f"Add {file_name}", content, branch="main")
            else:
                print(f"Error updating {file_name}: {e}")

    # Add all files generated to repository
    for field_name, field in type(llm_response).model_fields.items():
        file_content = getattr(llm_response, field_name)
        file_name = field.title if field.title else field_name
        if file_content:
            update_or_create_file(file_name, file_content)

    # Add all attachments
    for file_name, file_data in attachments.items():
        update_or_create_file(file_name, file_data)


def enable_pages(repo: Repository) -> None:
    """Enable Github Pages for the repository."""
    # Push a request to enable Github Pages
    owner, repo_name = repo.full_name.split("/")
    post_url = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
    headers = {
        "Authorization": f"Bearer {Environ.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    data = {"source": {"branch": "main", "path": "/"}, "build_type": "legacy"}

    # Enable Github Pages
    try:
        response = httpx.post(post_url, json=data, headers=headers, timeout=10)
        if response.status_code == httpx.codes.CREATED:
            print("Pages enabled successfully")
        else:
            print(f"Github API responsed with {response.status_code}: {response.text}")
    except httpx.RequestError as e:
        print(f"Network error enabling Pages {e}")

    # Check if pages is live
    pages_url = f"https://{owner}.github.io/{repo_name}/"
    print("Waiting for GitHub Pages to go live...")

    # Try for 150 seconds
    for _ in range(30):
        try:
            r = httpx.get(pages_url, timeout=5)
            if r.status_code == httpx.codes.OK:
                print(f"GitHub Pages is live at {pages_url}")
                return
        except httpx.RequestError:
            pass
        time.sleep(5)

    print("Timed out waiting for GitHub Pages to go live.")


def redeploy_pages(repo: Repository) -> dict:
    """Trigger a GitHub Pages build and wait for it to finish."""
    owner = repo.owner.login.lower()
    name = repo.name.lower()
    token = Environ.GITHUB_TOKEN

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    base_url = f"https://api.github.com/repos/{owner}/{name}/pages"

    # Check if a build is already running
    r = httpx.get(f"{base_url}/builds/latest", headers=headers, timeout=10)
    if r.status_code == httpx.codes.OK:
        status = r.json().get("status")
        if status in ("queued", "building"):
            print(f"A Pages build is already in progress (status={status}). Waiting...")
            while status in ("queued", "building"):
                time.sleep(5)
                r = httpx.get(f"{base_url}/builds/latest", headers=headers, timeout=10)
                status = r.json().get("status")

    # Trigger a new build
    resp = httpx.post(f"{base_url}/builds", headers=headers, timeout=10)
    try:
        resp.raise_for_status()
        pages_url = f"https://{owner}.github.io/{name}"
        print(f"Redeploying GitHub Pages at {pages_url}")
    except httpx.HTTPError as err:
        print(f"Failed to trigger Pages build: {err}")
        return {}

    # Wait for the new build to finish
    while True:
        r = httpx.get(f"{base_url}/builds/latest", headers=headers, timeout=10)
        status = r.json().get("status", "unknown")
        if status in ("built", "errored"):
            break
        time.sleep(10)

    print("Deployment finished." if status == "built" else "Deployment failed.")
    return resp.json()
