"""Github Actions"""

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


def push_code(llm_response: LLMResponse, repo: Repository):
    """Push code files to Github Repo"""
    print("Pushing code to repository...")
    for field_name, field in type(llm_response).model_fields.items():
        file_content = getattr(llm_response, field_name)
        file_name = field.title if field.title else field_name
        repo.create_file(
            file_name, f"Add {file_name}", file_content, branch="main"
        )
