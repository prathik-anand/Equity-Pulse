# EquityPulse Setup & Testing Guide 🚀

This guide provides step-by-step instructions to set up **EquityPulse** locally for testing and development.

## 📋 Prerequisites

*   **Python 3.11+**
*   **Node.js 18+**
*   **Docker & Docker Compose** (Required for Langfuse Tracing)
*   **Supabase Account** (Free Tier is fine)
*   **Google Gemini API Key** (Access to Gemini 3.0 Pro & Flash)

---

## 🛠️ Step 1: Infrastructure Setup

### 1. Supabase (Database & Storage)
EquityPulse uses Supabase for the PostgreSQL database and image storage.

1.  **Create a New Project** on [Supabase](https://supabase.com/).
2.  **Database Connection String**:
    *   Go to **Settings > Database**.
    *   Copy the **Connection String (URI)**.
    *   *Format*: `postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:5432/postgres`
    *   (Note: If you use the Transaction pooler port 6543, ensure your client supports prepared statements or disable them).
3.  **Storage Bucket**:
    *   Go to **Storage** in the sidebar.
    *   Create a new **Public** bucket named `chat-images`. (Must be Public for frontend access).
4.  **API Keys**:
    *   Go to **Settings > API**.
    *   Copy the `Project URL` and `anon` public key.

### 2. Langfuse (Tracing)
We use Langfuse to trace agent reasoning steps. It runs locally via Docker.

1.  Ensure Docker Desktop is running.
2.  Navigate to the backend folder:
    ```bash
    cd backend
    ```
3.  Start Langfuse:
    ```bash
    bash start_langfuse.sh
    ```
    *   This will pull the Docker image and start it at `http://localhost:3000`.
    *   (You don't need to log in to Langfuse for basic local tracing if using the provided config, or signs up locally).

---

## 🔑 Step 2: Environment Configuration

You need to configure both the Backend and Frontend variables.

### Backend (`/backend/.env`)

1.  **Copy the example file**:
    ```bash
    cd backend
    cp .env.example .env
    ```
2.  **Edit `.env`**:
    ```ini
    # Database (From Supabase Step 1)
    DATABASE_URL=postgresql+asyncpg://postgres......

    # AI Model (MUST be Gemini 3.0 Pro)
    GEMINI_MODEL_NAME=gemini-3-pro
    GOOGLE_API_KEY=your_google_api_key_here

    # Langfuse (Local Docker)
    LANGFUSE_SECRET_KEY=sk-lf-...  # Get these from http://localhost:3000 if needed
    LANGFUSE_PUBLIC_KEY=pk-lf-...
    LANGFUSE_HOST=http://localhost:3000
    ```

### Frontend (`/frontend/.env`)

1.  **Copy the example file**:
    ```bash
    cd ../frontend
    cp .env.example .env
    ```
2.  **Edit `.env`**:
    ```ini
    # Voice (MUST be Gemini 3.0 Flash)
    VITE_GEMINI_API_KEY=your_google_api_key
    VITE_GEMINI_MODEL_NAME=gemini-3-flash

    # Supabase (From Step 1)
    VITE_SUPABASE_URL=https://your-project.supabase.co
    VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
    VITE_SUPABASE_BUCKET=chat-images
    ```

---

## 📦 Step 3: Backend Installation & Migrations

1.  **Install Dependencies**:
    ```bash
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install uv && uv sync
    # Or: pip install -r requirements.txt
    ```

2.  **Run Database Migrations (CRITICAL)**:
    Setup the database schema in Supabase.
    ```bash
    alembic upgrade head
    ```

---

## 🚀 Step 4: Running the App

### Option A: Quick Start (Linux/Mac)
From the root directory:
```bash
chmod +x start.sh
./start.sh
```
*   Starts Langfuse (Docker), Backend (Port 8001), and Frontend (Port 5173).

### Option B: Manual Start

**Terminal 1 (Backend):**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing Instructions

1.  **Health Check**: Open [http://localhost:8001/health](http://localhost:8001/health) to confirm backend is running (`{"status": "ok"}`).
2.  **Frontend**: Open [http://localhost:5173](http://localhost:5173).
3.  **Run a Test Analysis**:
    *   Search: `TSLA` (Tesla).
    *   Check Terminal/Langfuse: Verify logs appear showing "Fundamental Agent", "Quant Agent" etc.
4.  **Test Voice (Flash)**:
    *   Click Mic -> Speak -> Verify accurate text transcription.
5.  **Test Upload (Supabase)**:
    *   Upload an image.
    *   Verify it appears in your Supabase `chat-images` bucket dashboard.
