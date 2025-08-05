# Banking AI Hackathon

An intelligent banking system that leverages multi-agent AI for behavioral analysis, financial recommendations, and risk assessment.

## 🚀 Features

- **Behavioral Analysis**: AI-powered analysis of customer transaction patterns
- **Multi-Model LLM Orchestration**: Intelligent switching between GPT-4, Claude, and local models
- **Personalized Recommendations**: Tailored financial advice based on user behavior
- **Risk Assessment**: Advanced risk modeling for banking operations
- **Secure & Scalable**: Built with security and scalability in mind

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **AI/ML**: OpenAI GPT-4, Anthropic Claude, Local LLMs
- **Orchestration**: LangChain, LangGraph
- **Vector Database**: Qdrant
- **Document Store**: MongoDB
- **Authentication**: JWT, OAuth2

## 🏗️ Project Structure

```
banking-ai-hackathon/
├── app/
│   ├── api/                  # API routes
│   ├── core/                 # Core application logic
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   ├── db/                   # Database connections
│   ├── agents/               # AI agents
│   └── config/               # Configuration
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
└── notebooks/                # Jupyter notebooks
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Poetry (recommended) or pip
- MongoDB (for document storage)
- Qdrant (for vector search)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd banking-ai-hackathon
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or with Poetry:
   ```bash
   poetry install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
