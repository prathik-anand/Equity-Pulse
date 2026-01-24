import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_quality_check(ticker="AAPL"):
    print(f"Triggering analysis for {ticker}...")
    try:
        # Start Analysis
        response = requests.post(f"{BASE_URL}/analysis", json={"ticker": ticker})
        response.raise_for_status()
        session_id = response.json()["session_id"]
        print(f"Analysis started. Session ID: {session_id}")
        
        # Poll for completion
        while True:
            status_res = requests.get(f"{BASE_URL}/analysis/{session_id}")
            status_res.raise_for_status()
            data = status_res.json()
            status = data["status"]
            
            print(f"Status: {status}...")
            
            if status == "completed":
                print("\n=== FINAL REPORT ===")
                report = data.get("report")
                if report:
                    print(json.dumps(report, indent=2))
                else:
                    print("Error: Report not found in data")
                    print(data)
                break
            elif status == "failed":
                print("\n=== ANALYSIS FAILED ===")
                print(data)
                break
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run_quality_check(ticker)
