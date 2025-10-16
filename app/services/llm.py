"""Service to interact with LLMs like OpenAI."""

import asyncio
from pathlib import Path

import aiofiles
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.models import LLMResponse

from .config import Environ


async def load_prompt(template: str, **kwargs: str) -> str:
    """Load a prompt from template file."""
    template_path = Path(__file__).parent / "prompts" / template
    async with aiofiles.open(template_path, encoding="utf-8") as tf:
        return (await tf.read()).format(**kwargs)


async def generate_app(brief: str, checks: str) -> LLMResponse:
    """Generate an app based on brief using OpenAI."""
    # Initiate client and query the OpenAI model
    print("Querying LLM...")
    async with AsyncOpenAI(
        api_key=Environ.OPENAI_API_KEY, base_url="https://aipipe.org/openai/v1"
    ) as client:
        # Get user input
        instructions, user_input = await asyncio.gather(
            *(
                load_prompt("instructions.txt", checks=checks),
                load_prompt("input.txt", brief=brief),
            )
        )

        response = await client.responses.parse(
            model="gpt-4o-mini",
            instructions=instructions,
            input=user_input,
            text_format=LLMResponse,
            temperature=0.0,
        )

    # Return response as pydantic model
    if not response.output_parsed:
        raise ValidationError("Empty Response")

    return response.output_parsed
