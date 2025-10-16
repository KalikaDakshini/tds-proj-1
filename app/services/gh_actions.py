"""Github Actions."""

import asyncio
import time

import httpx
from github import Auth, Github, UnknownObjectException
from github.Repository import Repository

from app.models import LLMResponse

from .config import Environ


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
    llm_response: LLMResponse, repo: Repository, attachments: dict[str, bytes]
) -> None:
    """Push code files to Github Repo."""
    # Push files to repository
    print("Pushing files to repository...")
    for field_name, field in type(llm_response).model_fields.items():
        file_content = getattr(llm_response, field_name)
        file_name = field.title if field.title else field_name
        if file_content:
            repo.create_file(file_name, f"Add {file_name}", file_content, branch="main")

    # PUsh attachments to repository
    for file_name, file_data in attachments.items():
        repo.create_file(file_name, f"Add {file_name}", file_data, branch="main")


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
