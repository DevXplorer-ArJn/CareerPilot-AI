from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from .config import get_settings
from .models import JobListing, JobPreferences


def _source_name(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def _published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def build_search_query(query: str, preferences: JobPreferences | None) -> str:
    terms = [query]
    if preferences is None:
        return " ".join(terms + ["recently posted jobs across all job types"])
    if preferences.skills:
        terms.append(f"skills: {', '.join(preferences.skills)}")
    if preferences.location:
        terms.append(f"location: {preferences.location}")
    if preferences.min_experience_years is not None:
        terms.append(f"{preferences.min_experience_years}+ years experience")
    if preferences.max_salary is not None:
        terms.append(
            f"salary up to {preferences.max_salary} {preferences.salary_currency}"
        )
    if preferences.remote:
        terms.append(preferences.remote)
    if preferences.job_type != "all":
        terms.append(preferences.job_type)
    terms.append("recently posted")
    return " ".join(terms)


async def search_jobs(
    query: str,
    max_results: int,
    preferences: JobPreferences | None = None,
) -> list[JobListing]:
    settings = get_settings()
    payload = {
        "api_key": settings.tavily_api_key,
        "query": f"job openings {build_search_query(query, preferences)}",
        "topic": settings.tavily_topic,
        "search_depth": settings.tavily_search_depth,
        "time_range": settings.tavily_time_range,
        "max_results": max_results,
        "include_answer": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Tavily rejected the job search request.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Tavily could not be reached.",
        ) from exc

    listings: list[JobListing] = []
    for result in response.json().get("results", []):
        published_at = _published_at(result.get("published_date"))
        listings.append(
            JobListing(
                title=result.get("title", "Untitled job"),
                description=result.get("content", ""),
                url=result["url"],
                source=_source_name(result["url"]),
                published_at=published_at,
            )
        )
    return sorted(
        listings,
        key=lambda listing: listing.published_at
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
