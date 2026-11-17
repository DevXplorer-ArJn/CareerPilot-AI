"use client";

import { FormEvent, useEffect, useState } from "react";

type Job = {
  id?: number;
  title: string;
  company?: string | null;
  location?: string | null;
  url: string;
  description: string;
  source: string;
  published_at?: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Something went wrong.");
  }
  return response.json();
}

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [query, setQuery] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedToken = window.localStorage.getItem("careerpilot_token");
    if (storedToken) {
      setToken(storedToken);
      loadSavedJobs(storedToken);
    }
  }, []);

  async function loadSavedJobs(authToken: string) {
    try {
      setSavedJobs(await apiRequest<Job[]>("/api/saved-jobs", {}, authToken));
    } catch {
      window.localStorage.removeItem("careerpilot_token");
      setToken(null);
    }
  }

  async function authenticate(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = await apiRequest<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      window.localStorage.setItem("careerpilot_token", result.access_token);
      setToken(result.access_token);
      await loadSavedJobs(result.access_token);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  async function register() {
    setError("");
    setBusy(true);
    try {
      const result = await apiRequest<{ access_token: string }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      window.localStorage.setItem("careerpilot_token", result.access_token);
      setToken(result.access_token);
    } catch (registrationError) {
      setError(
        registrationError instanceof Error
          ? registrationError.message
          : "Registration failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setError("");
    setBusy(true);
    try {
      const result = await apiRequest<{ results: Job[] }>("/api/jobs/search/natural", {
        method: "POST",
        body: JSON.stringify({ message: query }),
      });
      setJobs(result.results);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Search failed.");
    } finally {
      setBusy(false);
    }
  }

  async function saveJob(job: Job) {
    if (!token) {
      setError("Create an account or log in to save jobs.");
      return;
    }
    try {
      const saved = await apiRequest<Job>(
        "/api/saved-jobs",
        { method: "POST", body: JSON.stringify(job) },
        token,
      );
      setSavedJobs((current) =>
        current.some((item) => item.url === saved.url) ? current : [saved, ...current],
      );
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save job.");
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <p className="eyebrow">CAREERPILOT AI</p>
        <h1>Find work that fits your next move.</h1>
        <p className="subtitle">
          Tell us what you want in plain English. CareerPilot extracts your
          preferences and finds relevant opportunities.
        </p>
      </header>

      <section className="search-card">
        <form onSubmit={search}>
          <label htmlFor="query">What are you looking for?</label>
          <div className="search-row">
            <input
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Remote Python jobs in Bangalore under 25 LPA"
            />
            <button disabled={busy} type="submit">
              {busy ? "Searching..." : "Search jobs"}
            </button>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <div className="columns">
        <section>
          <h2>Recommended jobs</h2>
          {jobs.length === 0 && <p className="muted">Your search results will appear here.</p>}
          <div className="job-list">
            {jobs.map((job) => (
              <article className="job-card" key={job.url}>
                <div>
                  <p className="source">{job.source}</p>
                  <h3>{job.title}</h3>
                  <p className="meta">
                    {[job.company, job.location].filter(Boolean).join(" - ") || "Details online"}
                  </p>
                  <p className="meta">
                    {job.published_at
                      ? `Posted ${new Date(job.published_at).toLocaleDateString()}`
                      : "Recently found"}
                  </p>
                  <p>{job.description.slice(0, 260)}...</p>
                </div>
                <div className="actions">
                  <a href={job.url} target="_blank" rel="noreferrer">View job</a>
                  <button onClick={() => saveJob(job)} type="button">Save</button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="account-card">
          {token ? (
            <>
              <h2>Saved jobs</h2>
              {savedJobs.length === 0 && <p className="muted">Jobs you save will appear here.</p>}
              {savedJobs.map((job) => (
                <a className="saved-item" href={job.url} key={job.url} target="_blank" rel="noreferrer">
                  <strong>{job.title}</strong>
                  <span>{job.company ?? job.source}</span>
                </a>
              ))}
            </>
          ) : (
            <>
              <h2>Save your shortlist</h2>
              <p className="muted">Create an account to keep your favorite opportunities.</p>
              <form onSubmit={authenticate} className="auth-form">
                <input type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} required />
                <input type="password" placeholder="Password (8+ characters)" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
                <button disabled={busy} type="submit">Log in</button>
                <button className="secondary" disabled={busy} onClick={register} type="button">Create account</button>
              </form>
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
