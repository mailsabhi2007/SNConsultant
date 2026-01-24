# ServiceNow Consultant - AI-Powered Solution Architect

An intelligent AI assistant for ServiceNow that provides expert guidance on best practices, troubleshooting, and architecture decisions. Built with Claude (Anthropic), LangGraph, FastAPI, and React.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   TAVILY_API_KEY=your_tavily_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

3. **Start the backend server:**
   ```bash
   python -m uvicorn api.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Access at:** http://localhost:3000

### Production Build

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`.

## Features

- **Intelligent Search:** Searches official ServiceNow documentation via Tavily
- **Knowledge Base:** Upload and query internal documents (PDF, TXT, MD)
- **Live Instance Connection:** Connect to your ServiceNow instance for real-time data
- **Semantic Caching:** Intelligent response caching for faster responses
- **LLM Judge:** Quality evaluation of AI responses
- **User Authentication:** JWT-based auth with secure cookies
- **Admin Dashboard:** User management and system statistics
- **Dark Mode:** Light/dark theme support

## Architecture

```
├── api/                    # FastAPI backend
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   └── models/            # Pydantic models
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── hooks/         # React hooks
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   └── stores/        # Zustand state
│   └── ...
├── agent.py               # LangGraph agent
├── knowledge_base.py      # ChromaDB vector store
├── semantic_cache.py      # Response caching
├── llm_judge.py          # Response quality evaluation
└── ...
```

### Tech Stack

- **AI Model:** Claude Sonnet 4 (Anthropic)
- **Agent Framework:** LangGraph + LangChain
- **Backend:** FastAPI + Uvicorn
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **State Management:** Zustand + React Query
- **Vector DB:** ChromaDB
- **Search:** Tavily API

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user

### Chat
- `POST /api/chat/message` - Send message
- `GET /api/chat/conversations` - List conversations
- `GET /api/chat/conversations/{id}` - Get conversation
- `DELETE /api/chat/conversations/{id}` - Delete conversation

### Knowledge Base
- `POST /api/knowledge-base/upload` - Upload file
- `GET /api/knowledge-base/files` - List files
- `DELETE /api/knowledge-base/files/{id}` - Delete file

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |
| `TAVILY_API_KEY` | Yes | Tavily API key for web search |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT tokens |
| `SN_INSTANCE` | No | ServiceNow instance URL |
| `SN_USER` | No | ServiceNow username |
| `SN_PASSWORD` | No | ServiceNow password |

## Docker Deployment

```bash
docker-compose up -d
```

## Security

- Never commit `.env` file
- Use environment variables or secrets management
- Rotate API keys regularly
- Use least-privilege ServiceNow credentials
- JWT tokens stored in HTTP-only cookies

## License

MIT
