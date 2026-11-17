# CareerPilot AI

A FastAPI MVP for natural-language job search using Tavily.

## Run locally

1. Create a virtual environment and install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set `TAVILY_API_KEY` and `LLM_API_KEY`.
   The default LLM configuration uses Meta Llama 3.3 70B through OpenRouter's
   OpenAI-compatible API. Set `LLM_BASE_URL` to another compatible provider if
   needed.

3. Start the API:

   ```powershell
   uvicorn careerpilot.main:app --reload
   ```

Open `http://127.0.0.1:8000/docs` for the interactive API.

## Run the web app

In a second terminal:

```powershell
Set-Location web
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. Set `FRONTEND_URL` in the backend `.env` to the
deployed frontend URL when using Vercel.

## Search example

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/jobs/search `
  -ContentType "application/json" `
  -Body '{"query":"Python backend developer in Bangalore with 3 years experience","max_results":5}'
```

The API keeps the Tavily key server-side and returns validated job listing objects.

## Structured preferences

The same endpoint accepts optional structured preferences:

```json
{
  "query": "backend developer",
  "max_results": 5,
  "preferences": {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "location": "Bangalore",
    "min_experience_years": 3,
    "max_salary": 2500000,
    "salary_currency": "INR",
    "remote": "hybrid"
  }
}
```

Preferences are validated with Pydantic and converted into a more precise Tavily search query.
Supported job types are `all`, `internship`, `part-time`, `full-time`,
`contract`, and `temporary`. Results are sorted newest-first when Tavily
provides a publication date; searches also request recently posted jobs by
default and restrict Tavily results to the last month via `TAVILY_TIME_RANGE`.

## Natural-language search

`POST /api/jobs/search/natural` extracts preferences with Llama 3.3 70B and
then searches Tavily:

```json
{
  "message": "Find remote Python jobs in Bangalore for 3+ years experience under 25 LPA"
}
```

Use `POST /api/preferences/extract` when the extracted preferences are needed
without running a search.

## Accounts and saved jobs

The API includes:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/me`
- `GET /api/saved-jobs`
- `POST /api/saved-jobs`

Use PostgreSQL in production by setting `DATABASE_URL`; SQLite remains the
default for local development.
