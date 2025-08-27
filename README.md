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

## 🚀 Usage

### Command Line Interface
Analyze a repository directly from the command line:
```bash
python repo_agent.py https://github.com/langchain-ai/langgraph
```

### Web API
Start the FastAPI server:
```bash
python api.py
```

The server will be available at `http://127.0.0.1:8080`

#### API Endpoints
- `GET /` - Web UI for repository analysis
- `GET /health` - Health check endpoint
- `GET /analyze?repo=<url>` - Analyze a GitHub repository

#### Example API Call
```bash
curl "http://127.0.0.1:8080/analyze?repo=https://github.com/langchain-ai/langgraph"
```

### Programmatic Usage
```python
from repo_agent import analyze_repo

async def main():
    result = await analyze_repo("https://github.com/owner/repo")
    print(f"Score: {result.scores}")
    print(f"Level: {result.level}")
    print(f"Recommendations: {result.recommendations}")

# Run with asyncio
import asyncio
asyncio.run(main())
```

## 🎯 Analysis Breakdown

### README Quality (15% weight)
- Presence and length
- Installation instructions
- Getting started guide
- License information
- Contributing guidelines

### Repository Health (30% weight)
- Star count (normalized to 5000)
- Fork count (normalized to 1000)
- Contributor count (normalized to 50)
- CI/CD presence (topics, GitHub Actions)

### Activity Score (30% weight)
- Recent commit frequency
- Pull request activity
- Development momentum

### Engagement Score (25% weight)
- Open issues count
- Open PRs count
- Community responsiveness

## 🔧 Configuration

### GitHub API Rate Limits
- **Without token**: 60 requests/hour
- **With token**: 5000 requests/hour

### Custom Scoring Weights
Modify the scoring logic in `scoring.py`:
```python
w_readme = 0.15      # README quality weight
w_health = 0.30      # Repository health weight
w_activity = 0.30    # Activity score weight
w_engagement = 0.25  # Engagement score weight
```

## 🚀 Frontend Integration

### Next.js Setup
```bash
# Create Next.js app in a separate directory
npx create-next-app@latest gh-repo-analyzer --ts --eslint --app --src-dir --tailwind
cd gh-repo-analyzer

# Start frontend
npm run dev
```

The API already has CORS enabled for `http://localhost:3000`.

## 📊 Sample Output

```
Repo langchain-ai/langgraph
README quality: 0.8
Health score: 0.75
Activity score: 0.9
Engagement score: 0.6
Level: Advanced

Recommendations:
- Propose architectural improvements or refactors
- Review and mentor on PRs
- Optimize CI/CD, performance, or reliability

Details:
- README present: True
- Contributors: 45
- Commits (sampled): 89
- PRs (sampled total): 67
- Open issues (recent page): 23
- Open PRs (page): 12
```

## 🔍 Troubleshooting

### Common Issues
1. **Rate Limit Errors**: Set `GITHUB_TOKEN` in your `.env` file
2. **Import Errors**: Ensure all dependencies are installed
3. **API Connection**: Verify the server is running on the correct port

### Debug Mode
Enable verbose logging by setting environment variables:
```bash
export PYTHONPATH=.
python -u repo_agent.py https://github.com/owner/repo
```

## 🚀 Deployment

### Backend (FastAPI)
- **Railway**: Easy deployment with automatic HTTPS
- **Fly.io**: Global edge deployment
- **Render**: Simple container deployment

### Frontend (Next.js)
- **Vercel**: Zero-config deployment
- **Netlify**: Static site hosting

### Environment Variables for Production
```bash
GITHUB_TOKEN=your_production_token
HOST=0.0.0.0
PORT=8080
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by GitHub's REST API
- Styled with Tailwind CSS

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section
2. Review the GitHub API documentation
3. Open an issue with detailed error information

---

**Happy analyzing! 🎉**
