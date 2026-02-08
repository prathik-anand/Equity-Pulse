# EquityPulse Setup & Testing Guide 🚀

This guide provides step-by-step instructions to set up **EquityPulse** locally.

## 📋 Prerequisites

*   **Python 3.11+**
*   **Node.js 18+**
*   **Supabase Account** (Free Tier)
*   **Google Gemini API Key** (Must have access to Gemini 3.0 Preview)
*   *(Optional)* **Docker** (Only if you want Langfuse Tracing)

---

## 🛠️ Step 1: Infrastructure Setup

### 1. Supabase (Database & Storage)
EquityPulse uses Supabase for the PostgreSQL database and image storage.

1.  **Create a New Project** on [Supabase](https://supabase.com/).
2.  **Database Connection String**:
    *   Go to **Settings > Database**.
    *   Copy the **Connection String (URI)**.
    *   *Format*: `postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:5432/postgres`
3.  **Storage Bucket**:
    *   Go to **Storage** in the sidebar.
    *   Create a new **Public** bucket named `chat-images`. (Must be Public).
4.  **API Keys**:
    *   Go to **Settings > API**.
    *   Copy the `Project URL` and `anon` public key.

### 2. Langfuse (Optional Tracing)
*If you don't want to use Langfuse, you can skip this step and leave the ENV keys blank.*

1.  Ensure Docker Desktop is running.
2.  Run `bash backend/start_langfuse.sh` to start the local instance.

---

## 🔑 Step 2: Environment Configuration

### Backend (`/backend/.env`)

1.  **Copy the example**: `cp backend/.env.example backend/.env`
2.  **Edit `.env`**:
    ```ini
    # Database (From Supabase)
    DATABASE_URL=postgresql+asyncpg://postgres......

    # AI Model (Gemini 3.0 Preview)
    # Note: If looking for "Gemini 3.4", use these preview strings
    GEMINI_MODEL_NAME=gemini-3-pro-preview
    GOOGLE_API_KEY=your_google_api_key_here

    # Langfuse (Leave commented out to disable)
    # LANGFUSE_SECRET_KEY=sk-lf-...
    # LANGFUSE_PUBLIC_KEY=pk-lf-...
    # LANGFUSE_HOST=http://localhost:3000
    ```

### Frontend (`/frontend/.env`)

1.  **Copy the example**: `cp frontend/.env.example frontend/.env`
2.  **Edit `.env`**:
    ```ini
    # Voice (Gemini 3.0 Flash Preview)
    VITE_GEMINI_API_KEY=your_google_api_key
    VITE_GEMINI_MODEL_NAME=gemini-3-flash-preview

    # Supabase
    VITE_SUPABASE_URL=https://your-project.supabase.co
    VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
    VITE_SUPABASE_BUCKET=chat-images
    ```

---

## 📦 Step 3: Installation & Migrations

1.  **Install Backend**:
    ```bash
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install uv && uv sync
    ```

2.  **Run Migrations (CRITICAL)**:
    ```bash
    alembic upgrade head
    ```

3.  **Install Frontend**:
    ```bash
    cd ../frontend
    npm install
    ```

---

## 🚀 Step 4: Running the App

### Option A: Quick Start script
```bash
chmod +x start.sh
./start.sh
```

### Option B: Manual Start
*   **Backend**: `uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload`
*   **Frontend**: `npm run dev`

---

## 🧪 Testing Instructions

1.  **Health Check**: [http://localhost:8001/health](http://localhost:8001/health) -> `{"status": "ok"}`
2.  **Frontend**: Load [http://localhost:5173](http://localhost:5173).
3.  **Test Voice**: Click Mic -> Speak -> Verify transcription.
4.  **Test Analysis**: Search `GOOGL`. Verify standard log output in terminal.
