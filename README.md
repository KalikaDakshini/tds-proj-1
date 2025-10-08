# LLM App Builder — FastAPI

This repository contains a small FastAPI application that exposes an API to **build** application artifacts using large language models (LLMs). The service accepts build requests that include a task and a brief, builds an application, hosts it on Github, and deploys it to Github Pages

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

Set the following environment variables in a `.env` file before running the app:

- `API_SECRET` - secret used to authorize `POST /build` requests.
- `GITHUB_TOKEN` - personal access token used to **read/write** to github repos .
- `OPEN_API_KEY` - secret used to **query** OpenAI models

## Install and run locally

Create and activate a virtual environment and install the dependencies using uv:

```bash
uv init
uv add -r requirements.txt
```

Run the server with uvicorn:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive Swagger UI at: http://127.0.0.1:8000/docs

## POST /build — endpoint

This endpoint accepts a JSON payload describing the build request. The exact Pydantic model lives in `app/models.py` (commonly named `Payload`) and will contain fields like `secret`, `round`, and `brief`.

Example request (curl):

```bash
curl -X POST http://127.0.0.1:8000/build \
	-H "Content-Type: application/json" \
	-d '{
		"email": "22f2001238@ds.study.iitm.ac.in",
		"secret": "tds-secret",
		"task": "markdown-to-html-ab12",
		"round": 1,
		"nonce": "ab12",
		"brief": "Publish a static page that converts input.md from attachments to HTML with marked, renders it inside",
		"checks": [
			"!!document.querySelector(\"script[src*='marked']\")",
			"!!document.querySelector(\"script[src*='highlight.js']\")",
			"document.querySelector(\"#markdown-output\").innerHTML.includes(\"<h\")"
		],
		"evaluation_url": "http://localhost:5000",
		"attachments": [
			{ "name": "input.md", "url": "data:text/markdown; {base64 code}" }
		]
	}'
```

Expected responses:

- 200 OK - request accepted; returns a JSON body (for example echoing `round` and `brief` or a build result).
- 401 Unauthorized access - when the provided `secret` does not match `API_SECRET`.

Notes: The route has been implemented to explicitly return HTTP 200 on success and raise HTTP 401 on secret mismatch.

## Docker

Build and run the container:

```bash
docker build -t app-builder .
docker run -e .env -p 8000:8000 app-builder
```
