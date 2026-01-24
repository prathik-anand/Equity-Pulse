import pandas as pd
import json
from pathlib import Path

def fetch_sp500_tickers():
    print("Fetching S&P 500 tickers from Wikipedia...")
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # Pandas uses urllib/requests internally. If 403, we often need requests with headers.
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, headers=headers)
        tables = pd.read_html(r.text)
        sp500_table = tables[0]
        
        tickers = []
        for index, row in sp500_table.iterrows():
            symbol = row['Symbol']
            name = row['Security']
            tickers.append({"symbol": symbol, "name": name})
            
        print(f"Successfully fetched {len(tickers)} tickers.")
        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {str(e)}")
        return []

def update_tickers_file():
    tickers = fetch_sp500_tickers()
    if tickers:
        file_path = Path(__file__).parent / "data" / "tickers.json"
        with open(file_path, "w") as f:
            json.dump(tickers, f, indent=2)
        print(f"Updated {file_path}")

if __name__ == "__main__":
    update_tickers_file()
