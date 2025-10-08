# LLM App Builder — FastAPI

This repository contains a small FastAPI application that exposes an API to **build** application artifacts using large language models (LLMs). The service accepts build requests that include a brief and a round identifier, and delegates orchestration to components under `app/` (models, prompts, services, routes).

This README explains the project layout, how to run the app locally, how to call the `/build` endpoint, and tips for development and deployment.

## Quick summary

- Framework: FastAPI
- Entry point: `main.py`
- App package: `app/` (contains `models.py`, `routes/`, `services/`, `prompts/`)
- Config: `config.py`
- Container: `Dockerfile`

## Repository layout

Top-level files

- `main.py` — application bootstrap (exports the ASGI `app` used by uvicorn)
- `config.py` — configuration and environment helpers
- `requirements.txt` — Python dependencies
- `Dockerfile` — container recipe
- `README.md` — this file

App package (`app/`)

- `models.py` — Pydantic models for request/response validation (e.g. `Payload` used by `/build`).
- `routes/` — API routes; `api/routes.py` includes the `/build` endpoint.
- `services/` — business logic, LLM client wrappers, builders, and helpers.
- `prompts/` — prompt templates for guiding LLMs.

## Requirements

- Python 3.10+ is recommended.
- Install dependencies from `requirements.txt`.

## Environment variables

Set at least the following environment variable before running the app:

- `API_SECRET` — shared secret used to authorize `POST /build` requests.

Other environment variables (LLM API keys, storage credentials) should be set as required by services under `app/services`.

Example:

```bash
export API_SECRET="your-secret-key"
```

## Install and run locally

Create and activate a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server with uvicorn (reload enabled for development):

```bash
export API_SECRET="your-secret-key"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive Swagger UI at: http://127.0.0.1:8000/docs

## POST /build — endpoint

This endpoint accepts a JSON payload describing the build request. The exact Pydantic model lives in `app/models.py` (commonly named `Payload`) and will contain fields like `secret`, `round`, and `brief`.

Example request (curl):

```bash
curl -X POST http://127.0.0.1:8000/build \
	-H "Content-Type: application/json" \
	-d '{"secret":"your-secret-key", "round": 1, "brief": "Create a TODO app with Flask"}'
```

Expected responses:

- 200 OK — request accepted; returns a JSON body (for example echoing `round` and `brief` or a build result).
- 403 Forbidden — when the provided `secret` does not match `API_SECRET`.

Notes: The route has been implemented to explicitly return HTTP 200 on success and raise HTTP 403 on secret mismatch.

## Docker

Build and run the container:

```bash
docker build -t app-builder .
docker run -e API_SECRET="your-secret-key" -p 8000:8000 llm-app-builder
```

Adjust the Dockerfile or docker run flags to provide any LLM API keys or other secrets needed by `app/services`.

## Development notes and best practices

- Keep route handlers thin; move orchestration into `app/services` so it's easy to unit test.
- Store prompt templates in `app/prompts` and load them from services.
- Use environment variables for all credentials and avoid checking secrets into source control.
- Add unit tests for services and integration tests for routes.
