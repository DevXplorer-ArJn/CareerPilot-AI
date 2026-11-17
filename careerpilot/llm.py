import json

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from .config import get_settings
from .models import JobPreferences


def _extraction_prompt(message: str) -> str:
    return f"""Extract job-search preferences from the user's message.
Return only valid JSON with exactly these keys:
skills (array of strings), location (string or null),
min_experience_years (integer or null), max_salary (integer or null),
salary_currency (three-letter string, default USD),
remote (one of remote, hybrid, onsite, or null),
job_type (one of all, internship, part-time, full-time, contract, temporary).
Do not invent values that are not stated. Convert salary values such as
"25 LPA" to 2500000 INR when the location or wording indicates India.
Use job_type "all" when the user does not specify a job type.

User message:
{message}"""


async def extract_preferences(message: str) -> JobPreferences:
    settings = get_settings()
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You extract structured job preferences reliably.",
            },
            {"role": "user", "content": _extraction_prompt(message)},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return JobPreferences.model_validate(json.loads(content))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="The language model rejected the preference extraction request.",
        ) from exc
    except (httpx.RequestError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The language model returned an invalid extraction response.",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail="The language model returned preferences with an invalid schema.",
        ) from exc
