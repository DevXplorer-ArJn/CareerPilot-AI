from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class JobPreferences(BaseModel):
    skills: list[str] = Field(default_factory=list, max_length=20)
    location: str | None = Field(default=None, max_length=100)
    min_experience_years: int | None = Field(default=None, ge=0, le=50)
    max_salary: int | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="USD", min_length=3, max_length=3)
    remote: Literal["remote", "hybrid", "onsite"] | None = None
    job_type: Literal[
        "all", "internship", "part-time", "full-time", "contract", "temporary"
    ] = "all"


class JobSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=10, ge=1, le=20)
    preferences: JobPreferences | None = None


class JobListing(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    url: HttpUrl
    description: str
    source: str
    published_at: datetime | None = None


class JobSearchResponse(BaseModel):
    query: str
    results: list[JobListing]


class PreferenceExtractionRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)


class PreferenceExtractionResponse(BaseModel):
    message: str
    preferences: JobPreferences


class AuthRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


class SavedJobResponse(JobListing):
    id: int


class HealthResponse(BaseModel):
    status: str
