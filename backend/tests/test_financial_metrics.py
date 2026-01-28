import unittest
import json
from unittest.mock import patch, MagicMock
from app.graph.tools import get_valuation_ratios

class TestFinancialMetrics(unittest.TestCase):
    
    def setUp(self):
        self.mock_yfinance_info = {
            "trailingPE": 45.0,
            "forwardPE": 25.0,
            "pegRatio": None,
            "trailingPegRatio": 0.75,
            "priceToBook": 39.0,
            "priceToSalesTrailing12Months": 24.0,
            "enterpriseToEbitda": 40.0,
            "returnOnEquity": 1.07,  # 107%
            "returnOnAssets": 0.53,  # 53%
            "grossMargins": 0.70,     # 70%
            "operatingMargins": 0.63, # 63%
            "profitMargins": 0.53,    # 53%
            "currentRatio": 4.4,
            "quickRatio": 3.6,
            "debtToEquity": 9.1,     # 9.1% -> Should be normalized to 0.091
            "freeCashflow": 50000000000,
            "dividendYield": 7.02,   # 7.02% -> Should remain 7.02 (Percent Number)
            "payoutRatio": 0.58      # 58% -> Should be scaled to 58.0
        }

    @patch('yfinance.Ticker')
    def test_get_valuation_ratios_transformations(self, mock_ticker_class):
        """
        Verifies that get_valuation_ratios correctly transforms raw YFinance data:
        1. Debt/Equity (Percentage -> Decimal Ratio)
        2. Margins/ROE (Decimal -> Percentage)
        3. Dividend Yield (Pass through as Percentage Number)
        4. PEG Ratio (Fallback logic)
        """
        # Setup Mock
        mock_instance = MagicMock()
        mock_instance.info = self.mock_yfinance_info
        mock_ticker_class.return_value = mock_instance

        # Execute Tool
        result_json = get_valuation_ratios.invoke("TEST")
        data = json.loads(result_json)

        # --- ASSERTIONS ---

        # 1. PEG Ratio Fallback
        # Input: pegRatio=None, trailingPegRatio=0.75
        self.assertEqual(data['valuation']['peg_ratio'], 0.75)
        
        # 2. Profitability Scaling (Decimal -> x100)
        # Input: profitMargins=0.53 -> Output: 53.0
        self.assertEqual(data['profitability']['profit_margins'], 53.0)
        # Input: returnOnEquity=1.07 -> Output: 107.0
        self.assertEqual(data['profitability']['roe'], 107.0)
        
        # 3. dividend Yield (Pass through)
        # Input: dividendYield=7.02 -> Output: 7.02
        self.assertEqual(data['dividends']['yield'], 7.02)
        
        # 4. Payout Ratio Scaling (Decimal -> x100)
        # Input: payoutRatio=0.58 -> Output: 58.0
        self.assertEqual(data['dividends']['payout_ratio'], 58.0)
        
        # 5. Debt/Equity Normalization (Percentage -> /100)
        # Input: debtToEquity=9.1 -> Output: 0.091
        self.assertEqual(data['financial_health']['debt_to_equity'], 0.091)

    @patch('yfinance.Ticker')
    def test_get_valuation_ratios_missing_data(self, mock_ticker_class):
        """Verifies behavior when partial data is missing."""
        mock_instance = MagicMock()
        mock_instance.info = {} # Empty info
        mock_ticker_class.return_value = mock_instance

        result_json = get_valuation_ratios.invoke("EMPTY")
        data = json.loads(result_json)

        self.assertIsNone(data['valuation']['peg_ratio'])
        self.assertIsNone(data['financial_health']['debt_to_equity'])
        self.assertIsNone(data['profitability']['profit_margins'])

if __name__ == '__main__':
    unittest.main()
