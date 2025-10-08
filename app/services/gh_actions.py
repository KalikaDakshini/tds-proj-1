"""Github Actions"""

import os
import openai
from github import Github, Auth, UnknownObjectException
from github.Repository import Repository


def create_repo(name: str) -> Repository:
    """Create a new GitHub repository if it doesn't exist"""
    # Authenticate to GitHub
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
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


def generate_app(brief: str):
    """Generate an app based on brief using OpenAI"""
