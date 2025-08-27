import os
import re
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END


# -----------------------------
# Data structures
# -----------------------------

@dataclass
class RepoScores:
    readme_quality: float
    health_score: float
    activity_score: float
    engagement_score: float


@dataclass
class AnalysisResult:
    owner: str
    repo: str
    scores: RepoScores
    level: str
    recommendations: List[str]
    summary: str
    details: Dict[str, Any]


class AgentState(dict):
    pass


# -----------------------------
# Helpers
# -----------------------------

GITHUB_API = "https://api.github.com"


def get_auth_headers() -> Dict[str, str]:
    # Note: Set GITHUB_TOKEN in your environment or .env
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_repo_url(url: str) -> Tuple[str, str]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)(?:\.git)?", url)
    if not match:
        raise ValueError("Invalid GitHub URL")
    owner, repo = match.group(1), match.group(2)
    return owner, repo


async def http_get(client: httpx.AsyncClient, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    resp = await client.get(f"{GITHUB_API}{path}", params=params, headers=get_auth_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


# -----------------------------
# Node implementations
# -----------------------------

async def node_process_input(state: AgentState) -> AgentState:
    # Accept multiple invocation styles:
    # - state["repo_url"]
    # - state["input"]["repo_url"]
    # - state["input"] as a plain string URL
    repo_url: str = ""
    if isinstance(state, dict):
        if isinstance(state.get("repo_url"), str):
            repo_url = state.get("repo_url", "").strip()
        inp = state.get("input")
        if not repo_url and isinstance(inp, dict):
            val = inp.get("repo_url") or inp.get("url") or ""
            if isinstance(val, str):
                repo_url = val.strip()
        if not repo_url and isinstance(inp, str):
            repo_url = inp.strip()
    if not repo_url:
        raise ValueError("repo_url is required")
    owner, repo = parse_repo_url(repo_url)
    state.update({"owner": owner, "repo": repo})
    return state


async def node_doc_verify(state: AgentState) -> AgentState:
    owner, repo = state["owner"], state["repo"]
    async with httpx.AsyncClient() as client:
        readme = None
        # Try both API and raw content endpoint paths
        for path in (f"/repos/{owner}/{repo}/readme", f"/repos/{owner}/{repo}/contents/README.md"):
            try:
                data = await http_get(client, path)
                if "content" in data:
                    import base64
                    readme = base64.b64decode(data["content"]).decode(errors="ignore")
                    break
            except Exception:
                continue

    score = 0.0
    if readme:
        checks = [
            bool(re.search(r"# ", readme)),
            len(readme) > 400,
            "Installation" in readme or "Getting Started" in readme,
            "License" in readme or "MIT" in readme,
            "Contributing" in readme or "Contribution" in readme,
        ]
        score = sum(checks) / len(checks)
    state.update({"readme": readme or "", "readme_quality": score})
    return state


async def node_repo_health(state: AgentState) -> AgentState:
    owner, repo = state["owner"], state["repo"]
    async with httpx.AsyncClient() as client:
        repo_data = await http_get(client, f"/repos/{owner}/{repo}")
        contribs = 0
        try:
            contributors = await http_get(client, f"/repos/{owner}/{repo}/contributors")
            contribs = len(contributors)
        except Exception:
            contribs = 0

    stargazers = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    open_issues = repo_data.get("open_issues_count", 0)
    has_ci = any(k in (repo_data.get("topics") or []) for k in ["ci", "github-actions", "tests"]) or bool(repo_data.get("has_pages"))

    # Heuristic health: stars, forks, contributors, inverse open_issues, CI presence
    health = min(1.0, (
        (stargazers / 5000) * 0.35 +
        (forks / 1000) * 0.2 +
        (min(contribs, 50) / 50) * 0.25 +
        (0.2 if has_ci else 0.0)
    ))
    state.update({
        "repo_data": repo_data,
        "contributors_count": contribs,
        "health_score": round(health, 3),
    })
    return state


async def node_activity_score(state: AgentState) -> AgentState:
    owner, repo = state["owner"], state["repo"]
    async with httpx.AsyncClient() as client:
        try:
            commits = await http_get(client, f"/repos/{owner}/{repo}/commits", params={"per_page": 100})
        except Exception:
            commits = []
        try:
            prs = await http_get(client, f"/repos/{owner}/{repo}/pulls", params={"state": "all", "per_page": 100})
        except Exception:
            prs = []

    commit_score = min(1.0, (len(commits) / 100))
    pr_score = min(1.0, (len(prs) / 100))
    activity = round((commit_score * 0.6 + pr_score * 0.4), 3)
    state.update({"activity_score": activity, "commits_sample": len(commits), "prs_sample": len(prs)})
    return state


async def node_filter_issues_prs(state: AgentState) -> AgentState:
    owner, repo = state["owner"], state["repo"]
    async with httpx.AsyncClient() as client:
        try:
            issues = await http_get(client, f"/repos/{owner}/{repo}/issues", params={"state": "open", "per_page": 100})
        except Exception:
            issues = []
        try:
            open_prs = await http_get(client, f"/repos/{owner}/{repo}/pulls", params={"state": "open", "per_page": 100})
        except Exception:
            open_prs = []

    recent_issues = [i for i in issues if "pull_request" not in i]
    engagement = min(1.0, (len(recent_issues) + len(open_prs)) / 200)
    state.update({
        "recent_issues_count": len(recent_issues),
        "open_prs_count": len(open_prs),
        "engagement_score": round(engagement, 3),
    })
    return state


async def node_user_level(state: AgentState) -> AgentState:
    # Use combined score to infer level
    readme_q = state.get("readme_quality", 0.0)
    health = state.get("health_score", 0.0)
    activity = state.get("activity_score", 0.0)
    engagement = state.get("engagement_score", 0.0)
    composite = (readme_q * 0.2 + health * 0.35 + activity * 0.3 + engagement * 0.15)

    if composite < 0.33:
        level = "Beginner"
    elif composite < 0.66:
        level = "Intermediate"
    else:
        level = "Advanced"

    recs: List[str] = []
    if level == "Beginner":
        recs = [
            "Start with README and Installation steps",
            "Try a small good-first-issue",
            "Run tests locally and read contribution guide",
        ]
    elif level == "Intermediate":
        recs = [
            "Review open PRs to understand project conventions",
            "Pick medium-complexity issues with clear repro",
            "Consider improving docs or tests",
        ]
    else:
        recs = [
            "Propose architectural improvements or refactors",
            "Review and mentor on PRs",
            "Optimize CI/CD, performance, or reliability",
        ]

    state.update({"level": level, "recommendations": recs})
    return state


async def node_finalize(state: AgentState) -> AgentState:
    scores = RepoScores(
        readme_quality=round(state.get("readme_quality", 0.0), 3),
        health_score=round(state.get("health_score", 0.0), 3),
        activity_score=round(state.get("activity_score", 0.0), 3),
        engagement_score=round(state.get("engagement_score", 0.0), 3),
    )
    summary = (
        f"Repo {state['owner']}/{state['repo']}\n"
        f"README quality: {scores.readme_quality}\n"
        f"Health score: {scores.health_score}\n"
        f"Activity score: {scores.activity_score}\n"
        f"Engagement score: {scores.engagement_score}\n"
        f"Level: {state.get('level')}"
    )
    state.update({
        "result": AnalysisResult(
            owner=state["owner"],
            repo=state["repo"],
            scores=scores,
            level=state.get("level", "Unknown"),
            recommendations=state.get("recommendations", []),
            summary=summary,
            details={
                "readme_present": bool(state.get("readme")),
                "contributors_count": state.get("contributors_count"),
                "commits_sample": state.get("commits_sample"),
                "prs_sample": state.get("prs_sample"),
                "recent_issues_count": state.get("recent_issues_count"),
                "open_prs_count": state.get("open_prs_count"),
            },
        )
    })
    return state


# -----------------------------
# Graph assembly
# -----------------------------

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("process_input", node_process_input)
    graph.add_node("doc_verify", node_doc_verify)
    graph.add_node("repo_health", node_repo_health)
    graph.add_node("activity", node_activity_score)
    graph.add_node("issues_prs", node_filter_issues_prs)
    graph.add_node("user_level", node_user_level)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("process_input")
    graph.add_edge("process_input", "doc_verify")
    graph.add_edge("doc_verify", "repo_health")
    graph.add_edge("repo_health", "activity")
    graph.add_edge("activity", "issues_prs")
    graph.add_edge("issues_prs", "user_level")
    graph.add_edge("user_level", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


# -----------------------------
# CLI
# -----------------------------

async def analyze_repo(repo_url: str) -> AnalysisResult:
    load_dotenv()
    graph = build_graph()
    # Provide input in common forms for compatibility across versions
    try:
        final_state: AgentState = await graph.ainvoke({
            "repo_url": repo_url,
            "input": repo_url,
        })
        return final_state["result"]
    except Exception:
        # Fallback: run nodes sequentially if graph input handling differs
        state: AgentState = {"repo_url": repo_url}
        for fn in (
            node_process_input,
            node_doc_verify,
            node_repo_health,
            node_activity_score,
            node_filter_issues_prs,
            node_user_level,
            node_finalize,
        ):
            state = await fn(state)
        return state["result"]


def _print_result(result: AnalysisResult) -> None:
    print(result.summary)
    print("\nRecommendations:")
    for r in result.recommendations:
        print(f"- {r}")
    print("\nDetails:")
    print(f"- README present: {result.details.get('readme_present')}")
    print(f"- Contributors: {result.details.get('contributors_count')}")
    print(f"- Commits (sampled): {result.details.get('commits_sample')}")
    print(f"- PRs (sampled total): {result.details.get('prs_sample')}")
    print(f"- Open issues (recent page): {result.details.get('recent_issues_count')}")
    print(f"- Open PRs (page): {result.details.get('open_prs_count')}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python repo_agent.py <github_repo_url>")
        raise SystemExit(2)
    url = sys.argv[1]
    res = asyncio.run(analyze_repo(url))
    _print_result(res)


