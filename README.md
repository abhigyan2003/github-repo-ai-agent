# GitHub Repository Analyzer

A LangGraph-powered AI agent that analyzes GitHub repositories and provides quality scores, recommendations, and detailed insights.

## 🚀 Features

### Core Analysis
- **README Quality Check**: Evaluates documentation completeness and structure
- **Repository Health Score**: Analyzes stars, forks, contributors, and CI presence
- **Activity Score**: Measures recent commits and pull request activity
- **Engagement Score**: Tracks open issues and PRs for community health
- **User Level Assessment**: Provides Beginner/Intermediate/Advanced recommendations
- **Overall Rating**: Generates a 0-10 composite score

### Technical Features
- **LangGraph Agent**: Modular, state-driven analysis pipeline
- **GitHub API Integration**: REST API calls for comprehensive repo data
- **Async Processing**: Efficient concurrent data fetching
- **Fallback Handling**: Graceful degradation if graph execution fails
- **CORS Support**: Ready for frontend integration

## 🏗️ Architecture

```
Input → Process URL → Doc Verify → Health Check → Activity Score → Issues/PRs → User Level → Final Report
```

Each node in the LangGraph pipeline processes specific aspects of the repository and updates the shared state.

## 📋 Prerequisites

- Python 3.11+
- GitHub Personal Access Token (recommended)
- FastAPI & Uvicorn (for web API)

## 🛠️ Installation

### Option 1: Using uv (Recommended)
```bash
pip install uv
uv sync
```

### Option 2: Using pip
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the project root:
```ini
# GitHub API token (optional but recommended)
GITHUB_TOKEN=ghp_your_personal_access_token_here

# API server configuration (optional)
HOST=127.0.0.1
PORT=8080
```


