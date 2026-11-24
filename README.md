# Lyftr AI Full-Stack Assignment

A full-stack LLM chatbot built with React, FastAPI, LiteLLM, SQLite, and Docker.

The application supports multi-turn conversations, automatic API-key failover, response caching, per-request token tracking, latency tracking, persistent session history, and simulated provider failures.

---

## 1. Live URLs

Frontend: https://lyftr-ai-frontend-c40u.onrender.com

Backend: https://lyftr-ai-backend-96n2.onrender.com

API Documentation: https://lyftr-ai-backend-96n2.onrender.com/docs

---

## 2. Run locally: with Docker and without

### Prerequisites

- Docker Desktop
- Python 3.9+
- Node.js
- Two Gemini API keys

### Environment Variables

Create `backend/.env`:

```env
LLM_API_KEYS=your_api_key_1,your_api_key_2
DATABASE_URL=sqlite:///./app.db
ENABLE_FAILURE_SIMULATION=true
```

Never commit real API keys to the repository.

### Run with Docker

From the project root:

```bash
make up
```

The application will be available at:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Swagger API Docs: `http://localhost:8000/docs`

Stop the application with:

```bash
make down
```

### Run without Docker

#### Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

#### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## 3. Design decisions: key fallback, caching, SQLite session storage

### Key Fallback

The backend loads a pool containing at least two LLM API keys.

Each key is identified internally as:

```text
key_1
key_2
```

The actual API keys are never returned to the client.

When a provider request fails because of a supported rate-limit or server-side error, the backend automatically attempts the next key.

For example:

```text
key_1 → failure
key_2 → success
```

The response metadata reports:

```json
{
  "key_id": "key_2",
  "fallback_attempts": 1
}
```

If every configured provider key fails, the backend returns:

```json
{
  "detail": "all providers unavailable"
}
```

with HTTP status `503`.

Failed requests are not stored in the conversation history.

### Caching

LiteLLM's built-in cache is enabled.

A newly generated response reports:

```text
LIVE_INFERENCE
```

A cached response reports:

```text
LLM_CACHE
```

The cache is based on the model and complete message list supplied to the LLM, including:

- System prompt
- Previous conversation history
- Current user message

Therefore, the same first message in two new sessions can use the same cached response.

For cache hits:

```text
key_id = null
fallback_attempts = 0
```

Cached responses also preserve the original token usage and are significantly faster than live inference.

### SQLite Session Storage

Conversation history is stored in SQLite.

Messages are associated with a client-generated `session_id`.

The frontend sends only the latest user message. The backend retrieves previous messages from SQLite and reconstructs the complete conversation before calling the LLM.

When running through Docker, the SQLite database is stored at:

```text
/data/app.db
```

A named Docker volume is mounted at `/data`, allowing conversation history to survive container restarts.

---

## 4. Verification: how to see failover, cache hits and per-message token usage

### Health Check

Request:

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "keys_configured": 2,
  "cache_enabled": true
}
```

### Verify Automatic Failover

Failure simulation must be enabled with:

```env
ENABLE_FAILURE_SIMULATION=true
```

Send a `POST /chat` request with:

```text
X-Simulate-Failure: key_1=429
```

The request should succeed using the second key:

```json
{
  "key_id": "key_2",
  "fallback_attempts": 1
}
```

A server failure can also be tested with:

```text
X-Simulate-Failure: key_1=500
```

To simulate failure of every key:

```text
X-Simulate-Failure: *=429
```

Expected response:

```json
{
  "detail": "all providers unavailable"
}
```

with HTTP status `503`.

### Verify Cache Hits

Start a new session and send a message.

The first response should report:

```text
LIVE_INFERENCE
```

Start another new session and send the exact same first message.

The second response should report:

```text
LLM_CACHE
```

The cached response should have significantly lower latency.

### Verify Multi-Turn Memory

Send:

```text
My favorite color is purple.
```

Then, using the same session, send:

```text
What is my favorite color?
```

The assistant should answer that the favorite color is purple.

### Verify Token Usage

Every assistant response contains metadata for that request:

- Resolution source
- Model
- Latency in milliseconds
- Input tokens
- Output tokens
- Key ID
- Fallback attempts

Token values represent the individual request rather than a running conversation total.

### Run Automated Tests

From the backend directory:

```bash
pytest -v
```

The test suite verifies API health, validation, unknown sessions, and simulated provider failure behavior.

---

## 5. Setup Used: your editor and AI tools

The following development tools were used:

- Visual Studio Code
- ChatGPT for step-by-step development guidance, debugging, and implementation assistance
- FastAPI Swagger UI for API testing
- Docker Desktop
- Google AI Studio for Gemini API keys
- LiteLLM for LLM integration, caching, and provider handling

### Technology Stack

**Frontend**
- React
- Vite

**Backend**
- Python
- FastAPI

**AI**
- LiteLLM
- Google Gemini

**Storage**
- SQLite

**Infrastructure**
- Docker
- Docker Compose
- Nginx

---

## 6. Bonus features (if any): what you added beyond the requirements and why

The implementation prioritizes the required functionality, reliability, API-contract compliance, and deployment readiness.

Additional implementation improvements include:

- Responsive chat interface
- Clear loading state while the model is generating
- Human-readable frontend error messages
- Environment-based frontend API configuration
- Persistent Docker volume for SQLite
- Automated backend tests

---

## API Endpoints

### GET /health

Checks application health, configured key count, and caching status.

### POST /chat

Sends a new user message to the active conversation.

Example request:

```json
{
  "session_id": "s-123",
  "message": "What is the capital of India?"
}
```

### GET /sessions/{session_id}/messages

Returns the stored conversation history for a session in chronological order.

---

## Repository Structure

```text
lyftr-ai-assignment/
│
├── backend/
│   ├── tests/
│   │   └── test_api.py
│   ├── database.py
│   ├── llm.py
│   ├── main.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

## Security

Real API keys are stored only in local environment variables and are excluded from Git.

The API never exposes actual provider keys. Responses contain identifiers such as `key_1` and `key_2` only.