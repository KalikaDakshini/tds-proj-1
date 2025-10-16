"""Build Configuration for environment variables."""

import os
import sys

from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()


def get_env_variable(name: str) -> str:
    """Get an environment variable or raise an error if not found."""
    value = os.getenv(name)
    if value is None:
        print(f"Error: The environment variable '{name}' is not set.")
        sys.exit(1)
    return value


class Environ:
    """Environment variables required by the application."""

    API_SECRET: str = get_env_variable("API_SECRET")
    GITHUB_TOKEN: str = get_env_variable("GITHUB_TOKEN")
    OPENAI_API_KEY: str = get_env_variable("OPENAI_API_KEY")
