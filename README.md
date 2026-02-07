# RepoPilot AI

A multi-agent RAG system for deep repository intelligence.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- pnpm 8+

### Setup

1. **Clone and install dependencies**
   ```bash
   pnpm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Setup Python backend**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run development servers**
   ```bash
   # Terminal 1: Frontend
   pnpm dev:web

   # Terminal 2: Backend
   pnpm dev:api
   ```

## 📁 Project Structure

```
repopilot-ai/
├── apps/
│   ├── web/          # Next.js 15 Frontend
│   └── api/          # FastAPI Backend
├── packages/         # Shared code
└── turbo.json        # Turborepo config
```

## 🎯 Features

- 🧠 AST-powered code understanding (Tree-sitter)
- 💬 Natural language chatbot with source citations
- 🤖 Multi-agent reasoning (LangGraph)
- ⚡ Ultra-fast inference (Groq LPU)
- 📊 Repository visualization
- 🔐 JWT authentication

## 📝 License

MIT
