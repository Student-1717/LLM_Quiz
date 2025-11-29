# LLM Quiz Solver Service

This repository contains a Python-based service that automatically solves LLM-based quizzes for data sourcing, analysis, and visualization tasks. The service uses FastAPI as the backend and Playwright for headless browser rendering.

---

## Features

* Receives POST requests with quiz URLs.
* Loads JavaScript-rendered pages using Playwright.
* Downloads files (PDF, CSV) and extracts relevant data.
* Uses LLM agents to compute answers.
* Submits answers to the quiz endpoint automatically.
* Handles multiple-step quizzes with retries and timeouts.
* Production-ready JSON response under 1MB payload.

---

## Project Structure

```
LLM_Quiz/
├─ server.py                  # FastAPI entrypoint
├─ requirements.txt           # Python dependencies
├─ README.md
├─ solver/                    # Quiz-solving logic
│  ├─ __init__.py
│  ├─ browser.py
│  ├─ llm_agent.py
│  └─ quiz_solver.py
├─ utils/                     # Helper utilities
│  ├─ __init__.py
│  ├─ fetch.py
│  ├─ pdf_tools.py
│  └─ file_tools.py
├─ .gitignore
└─ .env.example               # Example environment variables (no secrets)
```

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Student-1717/LLM_Quiz.git
cd LLM_Quiz
```

2. Create a Python virtual environment:

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:

```bash
python -m playwright install
```

5. Create a `.env` file (do **not** commit it) with your secret:

```
QUIZ_SECRET=your_secret_here
```

---

## Running Locally

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Send a test POST request:

```json
POST http://127.0.0.1:8000/
Content-Type: application/json

{
  "email": "you@example.com",
  "secret": "your_secret_here",
  "url": "https://tds-llm-analysis.s-anand.net/demo"
}
```

---

## Deployment (Render.com)

1. Create a new Web Service on Render.
2. Connect your GitHub repository.
3. Set the **Environment** to Python 3.11+.
4. Add an **Environment Variable** `QUIZ_SECRET`.
5. Set the **Start Command**:

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

6. Deploy and test your endpoint.

---

## Notes

* Keep `.env` local. Do **not** push secrets to GitHub.
* Test your endpoint using `test.py` locally before deployment.
* Ensure payloads are under 1MB.
* Supports multi-step quizzes with automatic retries.

---

## License

MIT License

---

This service is part of the **LLM Analysis Quiz Project**.
