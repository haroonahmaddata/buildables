# Travel Agent

FastAPI backend derived from the `shtabi-backend` project. It exposes a
single `/health` endpoint and can be served with Uvicorn.

## Quick start

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
uvicorn --app-dir src travel_agent.main:app --reload
```

Then visit <http://localhost:8000/health>.
