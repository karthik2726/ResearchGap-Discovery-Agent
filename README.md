# ResearchGap Discovery Agent

An AI-powered research assistant that helps analyze academic papers, discover research gaps, and generate intelligent research insights using LLMs, vector search, and agent-based workflows.

## Project Overview

ResearchGap Discovery Agent is a full-stack AI research intelligence platform designed to support students, researchers, and innovators in identifying unexplored areas in academic literature.

The system allows users to upload research papers, process document content, extract meaningful insights, perform semantic search, and generate possible research gaps using AI agents.

## Tech Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* React Router DOM
* Recharts
* Lucide React

### Backend

* Python
* FastAPI
* ChromaDB
* SQLite
* PyMuPDF
* pdfplumber
* Sentence Transformers
* Groq / OpenAI / Ollama support

## Features

* Upload and process research papers
* Extract text from PDF documents
* Semantic search using vector embeddings
* AI-powered research gap discovery
* Agent-based research analysis workflow
* Support for multiple LLM providers
* Interactive frontend dashboard
* Research insights and visualization
* Docker-based setup support

## Folder Structure

```bash
ResearchGap-Discovery-Agent/
│
├── backend/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── tools/
│   ├── uploads/
│   ├── vector_store/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── setup.bat
├── run.bat
└── .gitignore
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/karthik2726/ResearchGap-Discovery-Agent.git
cd ResearchGap-Discovery-Agent
```

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder:

```env
LLM_PROVIDER=groq

GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

DATABASE_URL=sqlite:///./researchiq.db
CHROMA_PERSIST_DIR=./vector_store/chromadb_data
```

Run the backend server:

```bash
uvicorn main:app --reload --port 8000
```

Backend will run on:

```bash
http://localhost:8000
```

## Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on:

```bash
http://localhost:5173
```

## Docker Setup

You can also run the full project using Docker:

```bash
docker-compose up --build
```

This will start:

```bash
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

## How It Works

1. User uploads research papers.
2. Backend extracts and processes document text.
3. Text is converted into embeddings.
4. Embeddings are stored in ChromaDB.
5. AI agents analyze the content.
6. The system identifies possible research gaps.
7. Results are displayed through the frontend dashboard.

## Use Cases

* Academic research gap identification
* Literature review assistance
* Final-year project idea discovery
* Research proposal preparation
* Paper analysis and summarization
* AI-powered academic exploration

## Future Enhancements

* Citation-based answer generation
* Multi-document comparison
* Research paper recommendation system
* Export reports as PDF
* User authentication
* Saved research history
* Collaboration workspace
* Advanced analytics dashboard

## Author

**Karthik B**

GitHub: [karthik2726](https://github.com/karthik2726)

## License

This project is open-source and available for learning, academic, and research purposes.
