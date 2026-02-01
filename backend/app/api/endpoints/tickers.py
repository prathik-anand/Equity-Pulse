from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

import json
from pathlib import Path

@router.get("/tickers", response_model=List[Dict[str, str]])
async def get_supported_tickers():
    """
    Returns a list of supported tickers for frontend caching.
    Source: app/data/tickers.json
    """
    json_path = Path(__file__).parent.parent.parent / "data" / "tickers.json"
    
    if json_path.exists():
        with open(json_path, "r") as f:
            return json.load(f)
            
    # Fallback if file missing
    return [{"ticker": "AAPL", "company_name": "Apple Inc.", "sector": "Information Technology", "exchange": "NASDAQ"}]
