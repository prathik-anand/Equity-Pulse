# EquityPulse

**AI-Powered Investment Intelligence Platform**

EquityPulse is a sophisticated multi-agent system designed to analyze stock market data. It orchestrates a team of specialized AI agents to perform Technical, Fundamental, Sector, and Management analysis, aggregating their insights into a comprehensive investment report with a clear Buy/Hold/Sell signal.

![Dashboard Preview](https://github.com/user-attachments/assets/placeholder-image.png)

## 🚀 Features

*   **Multi-Agent Architecture**: Uses **LangGraph** to coordinate specialized agents.
    *   **Technical Analyst**: Analyzes price action and momentum (RSI, MACD).
    *   **Fundamental Analyst**: Evaluates financial health (Balance Sheets, Income Statements).
    *   **Sector Analyst**: Assesses industry trends and peer performance.
    *   **Management Analyst**: Investigates governance, news, and leadership stability.
*   **Real-Time Transparency**: Watch agent "thoughts" and logs stream in real-time on the dashboard.
*   **Live Ticker Discovery**: Dynamically fetches the S&P 500 list for instant autocomplete search.
*   **Premium UI**: Built with **React** and **Tailwind CSS**, featuring glassmorphism and smooth animations.
*   **Robust Backend**: Powered by **FastAPI**, **PostgreSQL** (Async), and **Alembic**.

## 🛠️ Tech Stack

*   **Backend**: Python 3.11+, FastAPI, LangGraph, SQLAlchemy (Async), Alembic, Pydantic.
*   **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v3.4, Framer Motion.
*   **Database**: PostgreSQL (Supabase compatible).
*   **Data Sources**: Yahoo Finance (`yfinance`), Wikipedia (S&P 500).

## ⚡ Getting Started

### Prerequisites
*   Python 3.11+
*   Node.js 18+
*   PostgreSQL Database

### 1. Clone the Repository
```bash
git clone https://github.com/prathik-anand/EquityPulse.git
cd EquityPulse
```

### 2. Backend Setup
```bash
cd backend

# Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies (using uv or pip)
pip install uv
uv sync

# Configure Environment
cp .env.example .env

# Edit .env and set your secrets
# - GOOGLE_API_KEY

# Run Database Migrations
alembic upgrade head

# Start Server
uvicorn app.main:app --reload
```
*Backend runs on `http://localhost:8000`*

### 3. Frontend Setup
```bash
cd frontend

# Install Dependencies
npm install

# Start Dev Server
npm run dev
```
*Frontend runs on `http://localhost:5173`*

## 📖 Usage

1.  Open the frontend application.
2.  Type a ticker symbol (e.g., `NVDA`, `AAPL`) in the search bar.
3.  Click **Analyze**.
4.  Watch the "Live Logs" to see agents working in real-time.
5.  Review the final Executive Summary and detailed breakdown tabs.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

MIT License.
