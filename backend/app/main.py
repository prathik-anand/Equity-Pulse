from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.endpoints import analysis, tickers

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware (Allow all for MVP ease, restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}", tags=["analysis"])
app.include_router(tickers.router, prefix=f"{settings.API_V1_STR}", tags=["tickers"])

@app.get("/")
async def root():
    return {"message": "EquityPulse Backend is Running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Programmatic uvicorn config - run with: python -m app.main
if __name__ == "__main__":
    import uvicorn
    import logging.config
    
    # Load logging config
    logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["**/logs/**", "**/*.log", "**/*.db", "**/__pycache__/**"],
        log_config="logging.conf"
    )
