"""Service to interact with LLMs like OpenAI"""

from pathlib import Path
from openai import OpenAI

from app.models import LLMResponse
from app.config import Environ


def load_prompt(template: str) -> str:
    """Load a prompt from template file"""
    template_path = Path(__file__).parent / "prompts" / template
    with open(template_path, "r", encoding="utf-8") as tf:
        return tf.read()


def generate_app(brief: str, checks: str) -> LLMResponse:
    """Generate an app based on brief using OpenAI"""
    # Initiate client and query the OpenAI model
    print("Querying LLM...")
    client = OpenAI(
        api_key=Environ.OPENAI_API_KEY, base_url="https://aipipe.org/openai/v1"
    )
    instructions = load_prompt("instructions.txt").format(checks=checks)
    user_input = load_prompt("input.txt").format(brief=brief)
    response = client.responses.create(
        model="gpt-4.1-nano",
        instructions=instructions,
        input=user_input,
    )

    # Return response as pydantic model
    return LLMResponse.model_validate_json(response.output_text)
