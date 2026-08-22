# AI Code Sandbox

**AI-Powered Code Execution & Autonomous Debugging**

AI Code Sandbox is a full-stack, developer-grade online code execution and autonomous AI debugging environment. It allows developers to write code, execute it inside an isolated sandbox, capture output and runtime errors, automatically analyze root causes using AI agents, apply structured code patches, re-verify execution results, and track session history.

---

## 🌟 Key Features

* **Monaco Code Editor**: Professional dark-themed code editor with syntax highlighting, line numbers, and error indicators.
* **Isolated Sandbox Execution**: Safe execution inside isolated temporary filesystem contexts with process timeout limits (`SANDBOX_TIMEOUT=10s`).
* **Autonomous AI Debugging Loop**: Detects runtime exceptions, sends error tracebacks to Google Gemini AI agents (or built-in AST fallback engine), parses structured fixes, applies diff patches, and re-executes code up to 3 times to verify success.
* **Persistent Session History**: Stores execution logs, original vs. fixed code, diffs, stderr, stdout, and error metrics in SQLite.
* **Analytics Dashboard**: Real-time stats showing total executions, bugs detected, bugs fixed, and success rates.
* **In-App Documentation & Settings**: Interactive reference guide and configurable execution settings.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React SPA)                           │
│  Monaco Editor  │  Dashboard  │  AI Debugger Panel  │  Terminal Output      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST API Calls
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              BACKEND (FastAPI)                              │
│                                                                             │
│  ┌───────────────────────┐   ┌──────────────────────┐   ┌─────────────────┐ │
│  │   Sandbox Executor    │   │  AI Debugger Service │   │ History Service │ │
│  │  (Process Isolation)  │   │   (Gemini + AST)     │   │ (SQLite Engine) │ │
│  └───────────┬───────────┘   └───────────┬──────────┘   └────────┬────────┘ │
└──────────────┼───────────────────────────┼───────────────────────┼──────────┘
               │                           │                       │
      ┌────────▼─────────┐        ┌────────▼─────────┐    ┌────────▼────────┐
      │  Temp Filesystem │        │  Google Gemini   │    │ SQLite Database │
      │  (Python / Node) │        │     API / SDK    │    │  (sandbox.db)   │
      └──────────────────┘        └──────────────────┘    └─────────────────┘
```

---

## 🚀 Quick Start

### 1. Requirements

* Python 3.10+
* Node.js (Optional for JS execution support)

### 2. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your Google Gemini API Key in `.env` (Optional: If absent, the application gracefully uses its built-in rule & AST fallback engine):

```env
AI_API_KEY=your_gemini_api_key_here
SANDBOX_TIMEOUT=10
MAX_DEBUG_ATTEMPTS=3
```

### 3. Install Dependencies & Start Application

```bash
pip install -r backend/requirements.txt
python backend/main.py
```

Or run with Uvicorn:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 Running Automated Tests

Execute the backend test suite:

```bash
python -m pytest
```

---

## 🐳 Docker Setup

Run using Docker Compose:

```bash
docker compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check & AI engine status |
| `POST` | `/api/run` | Execute code safely in isolated sandbox |
| `POST` | `/api/debug` | Run autonomous AI debugging loop |
| `GET` | `/api/history` | List all past execution sessions |
| `GET` | `/api/history/{id}` | Get details for specific session |
| `DELETE` | `/api/history/{id}` | Delete a history session |
| `DELETE` | `/api/history` | Clear all history sessions |
| `GET` | `/api/stats` | Get dashboard analytics |
| `GET` | `/api/settings` | Get system configuration |
