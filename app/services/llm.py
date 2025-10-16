"""Service to interact with LLMs like OpenAI."""

import asyncio
from pathlib import Path

import aiofiles
from openai import AsyncOpenAI

from app.models import LLMResponse

from .config import Environ


async def load_prompt(template: str) -> str:
    """Load a prompt from template file."""
    template_path = Path(__file__).parent / "prompts" / template
    async with aiofiles.open(template_path, encoding="utf-8") as tf:
        return await tf.read()


async def generate_app(brief: str, checks: str) -> LLMResponse:
    """Generate an app based on brief using OpenAI."""
    # Initiate client and query the OpenAI model
    print("Querying LLM...")
    async with AsyncOpenAI(
        api_key=Environ.OPENAI_API_KEY, base_url="https://aipipe.org/openai/v1"
    ) as client:
        # Get user input
        texts = ["instructions.txt", "input.txt"]
        read_tasks = await asyncio.gather(*[load_prompt(text) for text in texts])

        # TODO(kalika): Change this to structured output
        instructions = read_tasks[0].format(checks=checks)
        user_input = read_tasks[1].format(brief=brief)

        # Query the model
        response = await client.responses.create(
            model="gpt-4.1-nano",
            instructions=instructions,
            input=user_input,
        )

    # Return response as pydantic model
    return LLMResponse.model_validate_json(response.output_text)
