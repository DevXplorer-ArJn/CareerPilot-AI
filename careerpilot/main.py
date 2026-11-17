from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from .config import get_settings
from .database import Base, engine, get_db
from .db_models import SavedJob, User
from .jobs import search_jobs
from .llm import extract_preferences
from .models import (
    AuthRequest,
    HealthResponse,
    JobListing,
    JobSearchRequest,
    JobSearchResponse,
    PreferenceExtractionRequest,
    PreferenceExtractionResponse,
    SavedJobResponse,
    TokenResponse,
    UserResponse,
)

app = FastAPI(
    title="CareerPilot AI",
    description="Conversational job search powered by Tavily.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/jobs/search", response_model=JobSearchResponse)
async def search(request: JobSearchRequest) -> JobSearchResponse:
    results = await search_jobs(
        request.query,
        request.max_results,
        request.preferences,
    )
    return JobSearchResponse(query=request.query, results=results)


@app.post(
    "/api/preferences/extract",
    response_model=PreferenceExtractionResponse,
)
async def extract(
    request: PreferenceExtractionRequest,
) -> PreferenceExtractionResponse:
    preferences = await extract_preferences(request.message)
    return PreferenceExtractionResponse(
        message=request.message,
        preferences=preferences,
    )


@app.post("/api/jobs/search/natural", response_model=JobSearchResponse)
async def natural_search(
    request: PreferenceExtractionRequest,
) -> JobSearchResponse:
    preferences = await extract_preferences(request.message)
    results = await search_jobs(request.message, 10, preferences)
    return JobSearchResponse(query=request.message, results=results)


@app.post("/api/auth/register", response_model=TokenResponse)
def register(request: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = request.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account already exists.")
    user = User(email=email, password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(request: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@app.get("/api/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@app.get("/api/saved-jobs", response_model=list[SavedJobResponse])
def saved_jobs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SavedJobResponse]:
    jobs = db.scalars(
        select(SavedJob)
        .where(SavedJob.user_id == user.id)
        .order_by(SavedJob.created_at.desc())
    ).all()
    return [SavedJobResponse.model_validate(job, from_attributes=True) for job in jobs]


@app.post("/api/saved-jobs", response_model=SavedJobResponse, status_code=201)
def save_job(
    job: JobListing,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedJobResponse:
    existing = db.scalar(
        select(SavedJob).where(
            SavedJob.user_id == user.id,
            SavedJob.url == str(job.url),
        )
    )
    if existing is not None:
        return SavedJobResponse.model_validate(existing, from_attributes=True)
    saved = SavedJob(
        user_id=user.id,
        title=job.title,
        company=job.company,
        location=job.location,
        url=str(job.url),
        description=job.description,
        source=job.source,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedJobResponse.model_validate(saved, from_attributes=True)
