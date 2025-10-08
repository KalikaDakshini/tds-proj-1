"""Github Actions"""

from github import Github, Auth, UnknownObjectException
from github.Repository import Repository

from app.config import Environ


def create_repo(name: str) -> Repository:
    """Create a new GitHub repository if it doesn't exist"""
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
