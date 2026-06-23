# BA Copilot

AI-powered Business Analysis automation.

Converts BRDs, PRDs, meeting notes, or any business text into:

- Functional Requirements (structured, with IDs)
- Agile User Stories + Acceptance Criteria
- Test Cases (positive, negative, boundary)
- Quality Review Findings

---

## Stack

| Layer    | Tech                        |
|----------|-----------------------------|
| Backend  | FastAPI + Uvicorn           |
| AI       | OpenAI GPT-4o-mini          |
| Frontend | Streamlit                   |
| Parsing  | PyMuPDF (PDF), python-docx  |

---

## Setup

Prerequisite: Use Python 3.11, 3.12, or 3.13. Python 3.14 is not supported by all pinned dependencies.

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Edit `backend/.env`:

```
OPENAI_API_KEY=sk-...your-key-here...
```

### 3. Run the backend

```bash
cd backend
python main.py
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

### 4. Run the frontend (new terminal)

```bash
cd frontend
streamlit run app.py
```

Frontend runs at: http://localhost:8501

---

## API Endpoints

| Method | Endpoint  | Description                              |
|--------|-----------|------------------------------------------|
| GET    | /health   | Health check                             |
| POST   | /analyze  | Analyze pasted text `{ document_text }`  |
| POST   | /upload   | Upload a PDF / DOCX / TXT file           |

---

## Project Structure

```
BA/
├── backend/
│   ├── main.py                  # Uvicorn entry point
│   ├── requirements.txt
│   ├── .env                     # OPENAI_API_KEY
│   └── app/
│       ├── main.py              # FastAPI app, routes, CORS
│       ├── agents/
│       │   ├── requirement_agent.py
│       │   ├── story_agent.py
│       │   ├── testcase_agent.py
│       │   └── review_agent.py
│       ├── services/
│       │   ├── openai_service.py
│       │   └── document_parser.py
│       ├── schemas/
│       │   ├── outputs.py
│       │   └── requirements.py
│       └── workflows/
│           └── ba_workflow.py
└── frontend/
    └── app.py                   # Streamlit UI
```
