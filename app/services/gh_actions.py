"""Github Actions"""

import time
import requests
from github import Github, Auth, UnknownObjectException
from github.Repository import Repository

from app.config import Environ
from app.models import LLMResponse


def create_repo(name: str) -> Repository:
    """Create a new GitHub repository if it doesn't exist"""
    print(f"Creating repository: {name}")
    # Authenticate to GitHub
    token = Environ.GITHUB_TOKEN
    auth = Auth.Token(token)
    git = Github(auth=auth)
    user = git.get_user()

    # Delete repo if it exists
    try:
        repo = user.get_repo(name)
        repo.delete()
    except UnknownObjectException:
        pass

    # Create a new repository and return it
    repo = user.create_repo(name)  # type: ignore
    return repo


def push_code(
    llm_response: LLMResponse, repo: Repository, attachments: dict[str, bytes]
):
    """Push code files to Github Repo"""
    print("Pushing files to repository...")
    for field_name, field in type(llm_response).model_fields.items():
        file_content = getattr(llm_response, field_name)
        file_name = field.title if field.title else field_name
        if file_content:
            repo.create_file(
                file_name, f"Add {file_name}", file_content, branch="main"
            )

    # PUsh attachments to repository
    for file_name, file_data in attachments.items():
        repo.create_file(
            file_name, f"Add {file_name}", file_data, branch="main"
        )


def enable_pages(repo: Repository):
    """Enable Github Pages for the repository"""
    # Push a request to enable Github Pages
    owner, repo_name = repo.full_name.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pages"
    headers = {
        "Authorization": f"Bearer {Environ.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    data = {"source": {"branch": "main", "path": "/"}, "build_type": "legacy"}
    response = requests.post(url, json=data, headers=headers, timeout=10)

    # Check status code
    if response.status_code == 201:
        print("Github pages enabled")
    else:
        print(response.json())

    # Check if pages is live
    iter_count = 0
    pages_url = f"https://{owner}.github.io/{repo_name}/"
    while not requests.get(pages_url, timeout=5).ok:
        time.sleep(3)
        if iter_count > 30:
            print("Timed out waiting for Github Pages")
            break
        iter_count += 1
    else:
        print(f"Github Pages is live at {pages_url}")
