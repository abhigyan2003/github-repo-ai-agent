import asyncio
import os
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from repo_agent import analyze_repo


class AnalyzeResponse(BaseModel):
    owner: str
    repo: str
    score: float
    readme_quality: float
    health_score: float
    activity_score: float
    engagement_score: float
    level: str
    recommendations: list[str]
    details: dict


app = FastAPI(title="Repo Analysis Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/analyze", response_model=AnalyzeResponse)
async def analyze(repo: str = Query(..., description="GitHub repository URL")):
    load_dotenv()
    result = await analyze_repo(repo)
    # Optional: compute overall score from existing normalized 0-1 scores
    overall = round((
        result.scores.readme_quality * 0.15
        + result.scores.health_score * 0.30
        + result.scores.activity_score * 0.30
        + result.scores.engagement_score * 0.25
    ) * 10, 2)
    return AnalyzeResponse(
        owner=result.owner,
        repo=result.repo,
        score=overall,
        readme_quality=result.scores.readme_quality,
        health_score=result.scores.health_score,
        activity_score=result.scores.activity_score,
        engagement_score=result.scores.engagement_score,
        level=result.level,
        recommendations=result.recommendations,
        details=result.details,
    )

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>GitHub Repo Analyzer</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
  </head>
  <body class=\"bg-slate-950 text-slate-100 min-h-screen\">
    <div class=\"max-w-5xl mx-auto p-6\">
      <header class=\"mb-6\">
        <h1 class=\"text-2xl font-semibold\">GitHub Repo Analyzer</h1>
        <p class=\"text-slate-400\">Paste a repository URL to get a quality snapshot.</p>
      </header>

      <div class=\"rounded-xl border border-slate-800 bg-slate-900/60 p-4\">
        <div class=\"flex gap-2\">
          <input id=\"repo\" type=\"url\" placeholder=\"https://github.com/owner/repo\" class=\"flex-1 rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500\" />
          <button id=\"go\" class=\"rounded-lg bg-indigo-600 px-4 py-2 hover:bg-indigo-500 disabled:opacity-50\">Analyze</button>
        </div>
        <p id=\"error\" class=\"text-sm text-rose-400 mt-2 hidden\"></p>
      </div>

      <div id=\"loading\" class=\"mt-6 hidden\">
        <div class=\"flex items-center gap-3 text-slate-400\">
          <svg class=\"animate-spin h-5 w-5 text-indigo-400\" viewBox=\"0 0 24 24\"><circle class=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" stroke-width=\"4\"></circle><path class=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z\"></path></svg>
          <span>Analyzing repository…</span>
        </div>
      </div>

      <section id=\"out\" class=\"mt-6 space-y-4\"></section>
    </div>

    <script>
      const btn = document.getElementById('go');
      const input = document.getElementById('repo');
      const out = document.getElementById('out');
      const loading = document.getElementById('loading');
      const err = document.getElementById('error');

      function card(title, value){
        return `<div class=\"rounded-lg border border-slate-800 bg-slate-900/60 p-3\"><div class=\"text-xs text-slate-400\">${title}</div><div class=\"text-lg font-medium\">${value}</div></div>`
      }

      btn.onclick = async () => {
        const url = input.value.trim();
        err.classList.add('hidden');
        if (!url) { err.textContent = 'Please paste a GitHub repository URL'; err.classList.remove('hidden'); return; }
        btn.disabled = true; loading.classList.remove('hidden'); out.innerHTML = '';
        try {
          const q = encodeURIComponent(url);
          const resp = await fetch(`/analyze?repo=${q}`);
          if (!resp.ok) throw new Error('Request failed');
          const data = await resp.json();
          out.innerHTML = `
            <div class=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3\">
              ${card('Owner', data.owner)}
              ${card('Repo', data.repo)}
              ${card('Score', data.score)}
              ${card('Level', data.level)}
              ${card('README', data.readme_quality)}
              ${card('Health', data.health_score)}
              ${card('Activity', data.activity_score)}
              ${card('Engagement', data.engagement_score)}
            </div>
            <div class=\"rounded-xl border border-slate-800 bg-slate-900/60 p-4\">
              <h3 class=\"font-semibold mb-2\">Recommendations</h3>
              <ul class=\"list-disc pl-6 space-y-1 text-slate-300\">${data.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
            </div>
            <div class=\"rounded-xl border border-slate-800 bg-slate-900/60 p-4\">
              <h3 class=\"font-semibold mb-2\">Details</h3>
              <pre class=\"text-sm text-slate-300\">${JSON.stringify(data.details, null, 2)}</pre>
              <a class=\"inline-block mt-2 text-indigo-400 hover:underline\" href=\"https://github.com/${data.owner}/${data.repo}\" target=\"_blank\">Open repository →</a>
            </div>
          `;
        } catch (e) {
          err.textContent = 'Error: ' + (e?.message || e);
          err.classList.remove('hidden');
        } finally {
          btn.disabled = false; loading.classList.add('hidden');
        }
      };
    </script>
  </body>
 </html>
    """


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("api:app", host=host, port=port, reload=False)


