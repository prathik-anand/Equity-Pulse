"""
Tools for the EquityPulse analysis agents.
Each tool has:
- args_schema: Pydantic model for input validation
- Return type: Pydantic model for output structure
- Detailed docstring for LLM tool selection
"""

from langchain.tools import tool
import yfinance as yf
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List, Dict, Any, Optional
import json

from app.graph.schemas.tool_inputs import (
    FinancialsInput,
    CompanyNewsInput,
    GovernanceSearchInput,
    MarketTrendsSearchInput,
    ParallelSearchInput,
    InsiderTradesInput,
    OwnershipDataInput,
    AdvancedRatiosInput,
    RiskMetricsInput,
)
from app.graph.schemas.tool_outputs import (
    StockPriceOutput,
    FinancialsOutput,
    CompanyNewsOutput,
    NewsArticle,
    WebSearchOutput,
    InsiderTradesOutput,
    InsiderTransaction,
    OwnershipDataOutput,
    AdvancedRatiosOutput,
    RiskMetricsOutput,
)


@tool(args_schema=FinancialsInput)
def get_financials(ticker: str) -> str:
    """
    Retrieve financial statements for fundamental analysis.

    Returns JSON with:
    - balance_sheet: Total Assets, Total Debt, Cash, Stockholders Equity (last 2 years)
    - income_statement: Total Revenue, Net Income, Operating Income, Gross Profit (last 2 years)

    Use this to calculate:
    - Revenue growth rate (YoY)
    - Net profit margin (Net Income / Revenue)
    - Debt levels and cash position
    - Asset efficiency

    Call this tool for any valuation or financial health assessment.
    """
    try:
        stock = yf.Ticker(ticker)

        if stock.balance_sheet.empty or stock.income_stmt.empty:
            output = FinancialsOutput(
                ticker=ticker, error="No financial data available for this ticker"
            )
            return output.model_dump_json()

        # Get last 2 years of data, convert timestamps to strings for JSON
        balance_sheet = stock.balance_sheet.iloc[:, :2]
        balance_sheet.columns = [str(col.date()) for col in balance_sheet.columns]

        income_stmt = stock.income_stmt.iloc[:, :2]
        income_stmt.columns = [str(col.date()) for col in income_stmt.columns]

        output = FinancialsOutput(
            ticker=ticker,
            balance_sheet=balance_sheet.to_dict(),
            income_statement=income_stmt.to_dict(),
        )
        return output.model_dump_json()

    except Exception as e:
        output = FinancialsOutput(
            ticker=ticker, error=f"Error fetching financials: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=CompanyNewsInput)
def get_company_news(ticker: str) -> str:
    """
    Get the 5 most recent news articles about a company from Yahoo Finance.

    Returns JSON with articles containing:
    - title: Headline of the news article
    - publisher: News source (e.g., Reuters, Bloomberg)
    - link: URL to full article
    - providerPublishTime: Unix timestamp of publication

    Use this for:
    - Recent developments affecting the stock
    - Sentiment analysis
    - Catalyst identification
    - Management/governance news
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            output = CompanyNewsOutput(
                ticker=ticker, articles=[], error="No recent news found"
            )
            return output.model_dump_json()

        # Parse news into NewsArticle models
        articles = []
        for item in news[:5]:
            article = NewsArticle(
                title=item.get("title", ""),
                publisher=item.get("publisher"),
                link=item.get("link"),
                providerPublishTime=item.get("providerPublishTime"),
                type=item.get("type"),
                uuid=item.get("uuid"),
                thumbnail=item.get("thumbnail"),
                relatedTickers=item.get("relatedTickers"),
            )
            articles.append(article)

        output = CompanyNewsOutput(
            ticker=ticker,
            articles=articles,
        )
        return output.model_dump_json()

    except Exception as e:
        output = CompanyNewsOutput(
            ticker=ticker, articles=[], error=f"Error fetching news: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=GovernanceSearchInput)
def search_governance_issues(query: str) -> str:
    """
    Search the web for corporate governance information, controversies, and management track record.

    Best search queries include:
    - "[Company] SEC enforcement actions"
    - "[Company] executive compensation controversy"
    - "[Company] board of directors independence"
    - "[Company] shareholder lawsuits settlements"
    - "[Company] CEO CFO turnover departures"
    - "[Company] accounting irregularities audit"

    Returns: Text summary of search results from DuckDuckGo.

    Use this for Management Analyst to assess leadership quality and governance risks.
    """
    try:
        max_retries = 3
        for i in range(max_retries):
            try:
                from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

                wrapper = DuckDuckGoSearchAPIWrapper(
                    region="us-en", time="y", max_results=5
                )
                search = DuckDuckGoSearchRun(api_wrapper=wrapper)
                results = search.run(query)
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                import time

                time.sleep(2)

        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()

    except Exception as e:
        output = WebSearchOutput(
            query=query, results="", error=f"Search error after retries: {str(e)}"
        )
        return output.model_dump_json()


@tool
def get_price_history_stats(ticker: str) -> str:
    """
    Get ONLY historical price performance (CAGR) and volatility.
    Use this to analyze long-term stock momentum (1y, 3y, 5y, 10y).
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch max history
        hist = stock.history(period="10y")
        price_cagr = {}

        if not hist.empty:
            current = float(hist["Close"].iloc[-1])

            def calc_cagr(years):
                days = years * 252
                if len(hist) > days:
                    start_price = float(hist["Close"].iloc[-(days + 1)])
                    if start_price > 0:
                        cagr = (current / start_price) ** (1 / years) - 1
                        return round(cagr * 100, 2)
                return None

            price_cagr["cagr_1y"] = calc_cagr(1)
            price_cagr["cagr_3y"] = calc_cagr(3)
            price_cagr["cagr_5y"] = calc_cagr(5)
            price_cagr["cagr_10y"] = calc_cagr(10)

            price_stats = {
                "current_price": round(current, 2),
                "52w_high": round(float(hist["High"].tail(252).max()), 2),
                "52w_low": round(float(hist["Low"].tail(252).min()), 2),
                "volatility_30d": round(
                    float(hist["Close"].pct_change().std() * (252**0.5) * 100), 2
                ),
                "growth_cagr_percent": price_cagr,
            }

            return json.dumps(price_stats, default=str)
        return json.dumps({"error": "No price history found"})
    except Exception as e:
        return f"Error: {e}"


@tool
def get_fundamental_growth_stats(ticker: str) -> str:
    """
    Get ONLY fundamental growth rates (CAGR) for Revenue, Net Income, Operating Income.
    Data limited to last 3-4 years.
    """
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        fund_cagr = {}

        if not financials.empty:
            fin_sorted = financials.T.sort_index()

            def get_series_cagr(row_name):
                try:
                    if row_name in fin_sorted.columns:
                        series = fin_sorted[row_name].dropna()
                        if len(series) >= 2:
                            start_val = series.iloc[0]
                            end_val = series.iloc[-1]
                            years = (series.index[-1] - series.index[0]).days / 365.25
                            if years >= 1 and start_val > 0 and end_val > 0:
                                cagr = (end_val / start_val) ** (1 / years) - 1
                                return round(cagr * 100, 2)
                except:
                    pass
                return None

            fund_cagr["revenue_cagr_3y"] = get_series_cagr("Total Revenue")
            fund_cagr["net_income_cagr_3y"] = get_series_cagr("Net Income")
            fund_cagr["operating_income_cagr_3y"] = get_series_cagr("Operating Income")

            return json.dumps(fund_cagr, default=str)
        return json.dumps({"error": "No financials found"})
    except Exception as e:
        return f"Error: {e}"


@tool
def get_valuation_ratios(ticker: str) -> str:
    """
    Get ONLY deep investment ratios: Valuation, Profitability, Financial Health, Dividends.
    Does NOT include price history or growth rates.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Helper to safely get and normalize percentage values that YF returns as 0-100
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
            # YF returns Debt/Eq as percentage (e.g. 9.1 for 9.1%), convert to ratio (0.091)
            debt_to_equity = round(debt_to_equity / 100.0, 4)

        peg_ratio = info.get("pegRatio")
        if peg_ratio is None:
            peg_ratio = info.get("trailingPegRatio")

        dividend_yield = info.get("dividendYield")
        if dividend_yield is not None:
            # YF returns Dividend Yield as percentage number (e.g. 7.02 for 7.02%)
            # We want to keep it as percentage number for consistency with other % metrics
            pass

        # Helper to convert decimal to percentage
        def to_pct(val):
            return round(val * 100.0, 2) if val is not None else None

        metrics = {
            "valuation": {
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": peg_ratio,
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            },
            "profitability": {
                "roe": to_pct(info.get("returnOnEquity")),
                "roa": to_pct(info.get("returnOnAssets")),
                "gross_margins": to_pct(info.get("grossMargins")),
                "operating_margins": to_pct(info.get("operatingMargins")),
                "profit_margins": to_pct(info.get("profitMargins")),
            },
            "financial_health": {
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "debt_to_equity": debt_to_equity,
                "free_cashflow": info.get("freeCashflow"),
            },
            "dividends": {
                "yield": dividend_yield,
                "payout_ratio": to_pct(info.get("payoutRatio")),
            },
        }

        return json.dumps(metrics, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_price_action(ticker: str) -> str:
    """
    Get pure Price Action data: OHLC, 52-week Range, and Volatility.
    Use this to identify Support/Resistance levels.
    """
    try:
        stock = yf.Ticker(ticker)
        # We need recent intraday data for accurate OHLC
        info = stock.info
        hist = stock.history(
            period="1y"
        )  # Need at least 1y for 52w calc verification or volatility

        # Fallback to history if info is missing
        current = info.get("currentPrice") or (
            float(hist["Close"].iloc[-1]) if not hist.empty else None
        )

        output = {
            "ticker": ticker,
            "price": {
                "current": current,
                "previous_close": info.get("previousClose"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
            },
            "range_52w": {
                "high": info.get("fiftyTwoWeekHigh"),
                "low": info.get("fiftyTwoWeekLow"),
            },
            "volatility": {
                "beta": info.get("beta"),
                # Calculate 30d realized volatility
                "historical_volatility_30d": round(
                    float(hist["Close"].pct_change().std() * (252**0.5) * 100), 2
                )
                if not hist.empty
                else None,
            },
            "profile": {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            },
        }

        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_technical_indicators(ticker: str) -> str:
    """
    Get Technical Indicators: SMAs (20, 50, 200) and RSI (14).
    Use this to determine Trend Direction (Bull/Bear) and Momentum (Overbought/Oversold).
    """
    try:
        stock = yf.Ticker(ticker)
        # Need ~200 days for SMA200 + buffer for RSI calc
        hist = stock.history(period="1y")

        if hist.empty:
            return json.dumps({"error": "No history found"})

        # Calculate SMAs
        closes = hist["Close"]
        sma_20 = float(closes.tail(20).mean()) if len(closes) >= 20 else None
        sma_50 = float(closes.tail(50).mean()) if len(closes) >= 50 else None
        sma_200 = float(closes.tail(200).mean()) if len(closes) >= 200 else None

        # Calculate RSI (14)
        def calc_rsi(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        rsi = calc_rsi(closes)
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else None

        # Determine Trend State (Simple logic for helper)
        trend = "Neutral"
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                trend = "Bullish (Golden Cross/Uptrend)"
            else:
                trend = "Bearish (Death Cross/Downtrend)"

        output = {
            "ticker": ticker,
            "trend_indicators": {
                "sma_20": round(sma_20, 2) if sma_20 else None,
                "sma_50": round(sma_50, 2) if sma_50 else None,
                "sma_200": round(sma_200, 2) if sma_200 else None,
                "trend_signal": trend,
            },
            "momentum_indicators": {
                "rsi_14": round(current_rsi, 2) if current_rsi else None,
                "rsi_condition": "Overbought"
                if current_rsi > 70
                else "Oversold"
                if current_rsi < 30
                else "Neutral",
            },
        }

        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_volume_analysis(ticker: str) -> str:
    """
    Get Volume Analysis: Current vs Average and Relative Volume (RVOL).
    Use this to confirm the strength of price moves.
    """
    try:
        stock = yf.Ticker(ticker)
        # Need recent history
        hist = stock.history(period="3mo")
        info = stock.info

        if hist.empty:
            return json.dumps({"error": "No history found"})

        current_vol = info.get("volume")
        if not current_vol and not hist.empty:
            current_vol = int(hist["Volume"].iloc[-1])

        avg_vol_10d = float(hist["Volume"].tail(10).mean()) if len(hist) >= 10 else None
        avg_vol_3mo = float(hist["Volume"].mean())  # 3mo period

        rvol = (
            round(current_vol / avg_vol_3mo, 2) if avg_vol_3mo and current_vol else None
        )

        output = {
            "ticker": ticker,
            "volume_stats": {
                "current_volume": current_vol,
                "avg_volume_10d": int(avg_vol_10d) if avg_vol_10d else None,
                "avg_volume_3mo": int(avg_vol_3mo) if avg_vol_3mo else None,
            },
            "relative_volume": {
                "rvol": rvol,
                "interpretation": "High Interest"
                if rvol and rvol > 1.2
                else "Low Interest",
            },
        }

        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=MarketTrendsSearchInput)
def search_market_trends(query: str) -> str:
    """
    Search the web for market trends, sector analysis, and competitive landscape.

    Best search queries include:
    - "[Sector] market trends 2024 2025 outlook"
    - "[Company] vs [Competitor] market share comparison"
    - "[Industry] regulatory changes impact"
    - "[Company] analyst upgrades downgrades price target"
    - "[Sector] AI adoption digital transformation"
    - "macro trends affecting [industry] interest rates inflation"

    Returns: Text summary of search results from DuckDuckGo.

    Use this for:
    - Sector Analyst: Industry positioning and competitive dynamics
    - Technical Analyst: Market sentiment and analyst opinions
    - Fundamental Analyst: Growth drivers and headwinds
    """
    try:
        max_retries = 3
        for i in range(max_retries):
            try:
                from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

                wrapper = DuckDuckGoSearchAPIWrapper(
                    region="us-en", time="y", max_results=5
                )
                search = DuckDuckGoSearchRun(api_wrapper=wrapper)
                results = search.run(query)
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                import time

                time.sleep(2)

        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()

    except Exception as e:
        output = WebSearchOutput(
            query=query, results="", error=f"Search error after retries: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=ParallelSearchInput)
def parallel_search_market_trends(queries: List[str]) -> str:
    """
    Run multiple market trend searches in parallel to gather diverse data at once.

    Use this when:
    - You need to check multiple competitors, trends, or regulatory updates simultaneously.
    - Providing a list of 3-5 distinct search queries will result in a richer dataset.

    Returns: Combined text summary of all search results.
    """
    try:
        from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
        from langchain_community.tools import DuckDuckGoSearchRun
        import concurrent.futures

        # Helper to run a single query with retries
        def run_single_search(query):
            try:
                wrapper = DuckDuckGoSearchAPIWrapper(
                    region="us-en", time="y", max_results=4
                )
                search = DuckDuckGoSearchRun(api_wrapper=wrapper)
                return f"### Results for '{query}':\n{search.run(query)}\n"
            except Exception as e:
                return f"### Results for '{query}':\n(Search failed: {str(e)})\n"

        # unique queries only
        unique_queries = list(set(queries))
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_query = {
                executor.submit(run_single_search, q): q for q in unique_queries
            }
            for future in concurrent.futures.as_completed(future_to_query):
                results.append(future.result())

        combined_results = "\n".join(results)

        output = WebSearchOutput(
            query=" | ".join(unique_queries),
            results=combined_results,
        )
        return output.model_dump_json()

    except Exception as e:
        output = WebSearchOutput(
            query=str(queries),
            results="",
            error=f"Parallel search error: {str(e)}",
        )
        return output.model_dump_json()


@tool(args_schema=InsiderTradesInput)
def get_insider_trades(ticker: str) -> str:
    """
    Get recent insider transactions to analyze 'Smart Money' flow.
    Look for:
    - Cluster Buying: Multiple insiders buying at open market prices (Bullish).
    - Heavy Selling: Significant liquidation by key execs (Bearish).

    Returns: List of transactions with Date, Insider Name, Type (Buy/Sell), and Value.
    """
    try:
        stock = yf.Ticker(ticker)
        # insider_transactions returns a DataFrame
        trades_df = stock.insider_transactions

        if trades_df is None or trades_df.empty:
            output = InsiderTradesOutput(
                ticker=ticker, transactions=[], error="No insider trades data found"
            )
            return output.model_dump_json()

        # Sort by date descending and take top 10
        trades_df = trades_df.sort_index(ascending=False).head(10)

        transactions = []
        buy_count = 0
        sell_count = 0

        # columns usually: ['Shares', 'Value', 'Text', 'Start Date', 'Owner Name', 'Transaction Date']
        # The index is rarely the date, usually need to check columns

        for index, row in trades_df.iterrows():
            # Simplify date to string
            date_val = str(index)
            if "Date" in row:
                date_val = str(row["Date"])

            # Map fields safely
            t_type = row.get("Text", "")
            if not t_type:
                # Attempt to infer from other columns if 'Text' is missing or ambiguous
                pass

            # Simple sentiment tagging
            if "Purchase" in t_type or "Buy" in t_type:
                buy_count += 1
            elif "Sale" in t_type or "Sell" in t_type:
                sell_count += 1

            transactions.append(
                InsiderTransaction(
                    date=str(row.get("Start Date", date_val)),
                    insider=str(row.get("Owner Name", "Unknown")),
                    position=str(
                        row.get("Title", "")
                    ),  # 'Title' not always distinct in YF df
                    transaction=str(row.get("Text", "Unknown")),
                    shares=int(row.get("Shares", 0)) if row.get("Shares") else 0,
                    value=float(row.get("Value", 0.0)) if row.get("Value") else 0.0,
                )
            )

        summary = "Neutral"
        if buy_count > sell_count:
            summary = "Net Buying (Positive Sentiment)"
        elif sell_count > buy_count:
            summary = "Net Selling (Negative Sentiment)"

        output = InsiderTradesOutput(
            ticker=ticker, transactions=transactions, summary=summary
        )
        return output.model_dump_json()

    except Exception as e:
        output = InsiderTradesOutput(
            ticker=ticker, error=f"Error processing insider trades: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=OwnershipDataInput)
def get_ownership_data(ticker: str) -> str:
    """
    Get Institutional Ownership and Short Interest data.
    Use this to identify:
    - Institutional Sponsorship: Are big funds buying? (High % is good).
    - Short Squeeze Risk: Is Short % of Float > 15-20%? (High risk/reward).
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Major Holders (returns a DF usually, or check .major_holders)
        # Using .info is safer for specific metrics

        inst_own = info.get("heldPercentInstitutions")
        insider_own = info.get("heldPercentInsiders")
        short_ratio = info.get("shortRatio")
        short_percent_of_float = info.get("shortPercentOfFloat")

        # Collect top holders if available via .major_holders or .institutional_holders
        # Keeping it simple with .info metrics first for reasoning

        output = OwnershipDataOutput(
            ticker=ticker,
            institutional_ownership_pct=inst_own,
            insider_ownership_pct=insider_own,
            short_ratio=short_ratio,
            short_percent_of_float=short_percent_of_float,
            major_holders={},  # Can expand to pull top 5 names later if needed
        )
        return output.model_dump_json()

    except Exception as e:
        output = OwnershipDataOutput(
            ticker=ticker, error=f"Error fetching ownership data: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=AdvancedRatiosInput)
def get_advanced_ratios(ticker: str) -> str:
    """
    Get Advanced Operational Efficiency and Capital Allocation metrics.
    Use this for 'Moat' verification:
    - ROIC (Return on Invested Capital): Approximate match for quality.
    - ROCE (Return on Capital Employed): Efficiency of capital usage.
    - FCF Yield: True valuation.
    - Payout Ratio: Dividend sustainability.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Calculate/Fetch advanced metrics
        # ROIC is not always direct in info, using returnOnEquity or returnOnAssets as proxies if needed,
        # but pure ROIC might need manual calculation. We supply what we can.

        # Free Cash Flow Yield = Free Cash Flow / Market Cap
        fcf = info.get("freeCashflow")
        mkt_cap = info.get("marketCap")
        fcf_yield = None
        if fcf and mkt_cap:
            # Return as decimal (e.g. 0.015 for 1.5%) for consistency with other pct fields
            fcf_yield = round(fcf / mkt_cap, 4)

        # Calculate ROCE = EBIT / (Total Assets - Current Liabilities)
        roce = None
        try:
            # Need financials for EBIT and Balance Sheet for Capital Employed
            income_stmt = stock.income_stmt
            balance_sheet = stock.balance_sheet

            # Capital Employed Component (Total Assets - Current Liabilities)
            # We use the latest available Balance Sheet (Annual usually)
            capital_employed = None
            if not balance_sheet.empty:
                latest_date_bs = balance_sheet.columns[0]
                total_assets = None
                current_liabilities = None

                if "Total Assets" in balance_sheet.index:
                    total_assets = balance_sheet.loc["Total Assets", latest_date_bs]

                if "Total Current Liabilities" in balance_sheet.index:
                    current_liabilities = balance_sheet.loc[
                        "Total Current Liabilities", latest_date_bs
                    ]
                elif "Current Liabilities" in balance_sheet.index:  # Fallback key
                    current_liabilities = balance_sheet.loc[
                        "Current Liabilities", latest_date_bs
                    ]

                if total_assets is not None and current_liabilities is not None:
                    capital_employed = total_assets - current_liabilities

            # EBIT Component
            # Prefer TTM EBIT for up-to-date efficiency metric
            ebit = None
            revenue_ttm = info.get("totalRevenue")
            op_margin_ttm = info.get("operatingMargins")

            if revenue_ttm is not None and op_margin_ttm is not None:
                ebit = revenue_ttm * op_margin_ttm
            elif not income_stmt.empty:
                # Fallbck to Annual EBIT if TTM info missing
                latest_date_inc = income_stmt.columns[0]
                if "Operating Income" in income_stmt.index:
                    ebit = income_stmt.loc["Operating Income", latest_date_inc]
                elif "EBIT" in income_stmt.index:
                    ebit = income_stmt.loc["EBIT", latest_date_inc]

            if (
                ebit is not None
                and capital_employed is not None
                and capital_employed > 0
            ):
                roce = round(ebit / capital_employed, 4)  # Return as decimal

        except Exception as e:
            # ROCE calculation failed, but don't fail the whole tool
            print(f"ROCE calc failed: {e}")
            pass

        metrics = AdvancedRatiosOutput(
            ticker=ticker,
            return_on_capital=info.get(
                "returnOnEquity"
            ),  # Using ROE as closest proxy available in std info
            return_on_capital_employed=roce,
            fcf_yield=fcf_yield,
            price_to_fcf=None,  # Derived from yield
            payout_ratio=info.get("payoutRatio"),
            revenue_per_share=info.get("revenuePerShare"),
            net_income_per_share=info.get("trailingEps"),
            buyback_yield=None,  # Hard to get directly without parsing CF statement history
        )

        if metrics.fcf_yield:
            # Price/FCF is inverse of yield (if yield is decimal, 1/yield)
            metrics.price_to_fcf = round(1 / metrics.fcf_yield, 2)

        return metrics.model_dump_json()

    except Exception as e:
        output = AdvancedRatiosOutput(
            ticker=ticker, error=f"Error fetching advanced ratios: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=RiskMetricsInput)
def get_risk_metrics(ticker: str) -> str:
    """
    Get Risk and Financial Distress metrics.
    Calculates:
    - Altman Z-Score: Bankruptcy prediction.
    - Beneish M-Score: Earnings manipulation detection.
    - Financial Distress: Interest Coverage, Current Ratio.
    - Inventory Risk: Days Sales in Inventory (DSI).
    """
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet

        if income_stmt.empty or balance_sheet.empty:
            return RiskMetricsOutput(
                ticker=ticker, error="Insufficient financial data"
            ).model_dump_json()

        # Get latest year and previous year dates
        dates = income_stmt.columns
        if len(dates) < 2:
            return RiskMetricsOutput(
                ticker=ticker, error="Need at least 2 years of data for M-Score"
            ).model_dump_json()

        t = dates[0]  # Current Year (Latest)
        t_minus_1 = dates[1]  # Previous Year

        # --- Helper for safe retrieval ---
        def get_val(df, key, date, default=0.0):
            try:
                if key in df.index:
                    return float(df.loc[key, date])
                # Fallback searches
                for idx in df.index:
                    if key.lower() in str(idx).lower():
                        return float(df.loc[idx, date])
                return default
            except:
                return default

        # --- 1. Altman Z-Score Components ---
        # Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
        # A = Working Capital / Total Assets
        # B = Retained Earnings / Total Assets
        # C = EBIT / Total Assets
        # D = Market Value of Equity / Total Liabilities
        # E = Sales / Total Assets

        total_assets = get_val(balance_sheet, "Total Assets", t)
        current_assets = get_val(balance_sheet, "Total Current Assets", t)
        current_liabilities = get_val(balance_sheet, "Total Current Liabilities", t)
        working_capital = current_assets - current_liabilities

        retained_earnings = get_val(balance_sheet, "Retained Earnings", t)
        ebit = get_val(income_stmt, "EBIT", t)
        if ebit == 0:
            ebit = get_val(income_stmt, "Operating Income", t)

        total_liabilities = get_val(
            balance_sheet, "Total Liabilities Net Minority Interest", t
        )
        if total_liabilities == 0:
            total_liabilities = get_val(balance_sheet, "Total Liabilities", t)

        total_revenue = get_val(income_stmt, "Total Revenue", t)

        market_cap = stock.info.get("marketCap", 0)

        z_score = None
        if total_assets > 0 and total_liabilities > 0:
            A = working_capital / total_assets
            B = retained_earnings / total_assets
            C = ebit / total_assets
            D = market_cap / total_liabilities
            E = total_revenue / total_assets
            z_score = round(1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E, 2)

        # --- 2. Beneish M-Score Components ---
        # DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA

        # Sales
        sales_t = get_val(income_stmt, "Total Revenue", t)
        sales_t1 = get_val(income_stmt, "Total Revenue", t_minus_1)

        # Receivables
        receivables_t = get_val(balance_sheet, "Net Receivables", t)
        receivables_t1 = get_val(balance_sheet, "Net Receivables", t_minus_1)
        # If Net Receivables missing, try "Accounts Receivable"
        if receivables_t == 0:
            receivables_t = get_val(balance_sheet, "Accounts Receivable", t)
        if receivables_t1 == 0:
            receivables_t1 = get_val(balance_sheet, "Accounts Receivable", t_minus_1)

        # Gross Profit (for GMI)
        gross_profit_t = get_val(income_stmt, "Gross Profit", t)
        gross_profit_t1 = get_val(income_stmt, "Gross Profit", t_minus_1)

        # Assets (for AQI, LVGI, TATA)
        assets_t = get_val(balance_sheet, "Total Assets", t)
        assets_t1 = get_val(balance_sheet, "Total Assets", t_minus_1)

        # PPE & Securities (for AQI) - Simplified to Non-Current Assets
        # AQI = (Non-Current Assets_t / Assets_t) / ...
        curr_assets_t = get_val(balance_sheet, "Total Current Assets", t)
        # curr_assets_t1 unused
        ppe_t = get_val(balance_sheet, "Net PPE", t)  # Plant Property Equipment
        if ppe_t == 0:
            ppe_t = get_val(balance_sheet, "Net Tangible Assets", t)  # Fallback

        # Depreciation (for DEPI)
        dep_t = get_val(
            income_stmt, "Reconciled Depreciation", t
        )  # specific to yfinance
        dep_t1 = get_val(income_stmt, "Reconciled Depreciation", t_minus_1)

        # SGA (for SGAI)
        sga_t = get_val(income_stmt, "Selling General And Administration", t)
        sga_t1 = get_val(income_stmt, "Selling General And Administration", t_minus_1)

        # Liabilities (for LVGI)
        liab_t = total_liabilities  # Already fetched
        liab_t1 = get_val(
            balance_sheet, "Total Liabilities Net Minority Interest", t_minus_1
        )

        # Net Income & CFO (for TATA)
        net_income_t = get_val(income_stmt, "Net Income", t)
        cfo_t = (
            0  # Need cash flow stmt for this, skip TATA complexity for now or fetch CF
        )
        # Fetch CF for TATA
        try:
            cf = stock.cashflow
            cfo_t = get_val(cf, "Operating Cash Flow", t)
        except Exception:
            pass

        m_score = None
        dsi_change = None
        dsi_current = None

        try:
            # DSRI: Days Sales in Receivables Index
            dsri = (
                (receivables_t / sales_t) / (receivables_t1 / sales_t1)
                if sales_t and sales_t1 and receivables_t1
                else 1.0
            )

            # GMI: Gross Margin Index
            gm_t = gross_profit_t / sales_t if sales_t else 0
            gm_t1 = gross_profit_t1 / sales_t1 if sales_t1 else 0
            gmi = gm_t1 / gm_t if gm_t > 0 else 1.0

            # AQI: Asset Quality Index
            # Asset Quality = 1 - ((Current Assets + PPE) / Total Assets)
            # aq_t = 1 - ((curr_assets_t + ppe_t) / assets_t) if assets_t else 0
            # Simplify AQI Calculation if data is messy, or default to 1.0
            aqi = 1.0

            # SGI: Sales Growth Index
            sgi = sales_t / sales_t1 if sales_t1 else 1.0

            # DEPI: Depreciation Index
            # DEPI = (Dep_t-1 / (Dep_t-1 + PPE_t-1)) / (Dep_t / (Dep_t + PPE_t))
            # Simplified: Rate of depreciation. If Dep rate slows, DEPI > 1
            dep_rate_t = dep_t / (dep_t + ppe_t) if (dep_t + ppe_t) > 0 else 0
            dep_rate_t1 = (
                dep_t1 / (dep_t1 + ppe_t) if (dep_t1 + ppe_t) > 0 else 0
            )  # Approximation using current PPE if prev missing
            depi = dep_rate_t1 / dep_rate_t if dep_rate_t > 0 else 1.0

            # SGAI: SG&A Index
            sgai = (
                (sga_t / sales_t) / (sga_t1 / sales_t1)
                if sales_t and sales_t1 and sga_t1
                else 1.0
            )

            # LVGI: Leverage Index
            lev_t = liab_t / assets_t if assets_t else 0
            lev_t1 = liab_t1 / assets_t1 if assets_t1 else 0
            lvgi = lev_t / lev_t1 if lev_t1 > 0 else 1.0

            # TATA: Total Accruals to Total Assets
            tata = (net_income_t - cfo_t) / assets_t if assets_t else 0

            # Beneish M-Score Formula
            m_score = (
                -4.84
                + 0.92 * dsri
                + 0.528 * gmi
                + 0.404 * aqi
                + 0.892 * sgi
                + 0.115 * depi
                - 0.172 * sgai
                + 4.679 * tata
                - 0.327 * lvgi
            )
            m_score = round(m_score, 2)

        except Exception as e:
            # print(f"M-Score calc error: {e}")
            pass

        # --- 3. Inventory Risk (DSI) ---
        # DSI = (Average Inventory / COGS) * 365
        inventory_t = get_val(balance_sheet, "Inventory", t)
        inventory_t1 = get_val(balance_sheet, "Inventory", t_minus_1)
        cogs_t = get_val(income_stmt, "Cost Of Revenue", t)

        if cogs_t > 0:
            avg_inv = (inventory_t + inventory_t1) / 2
            dsi_current = (avg_inv / cogs_t) * 365

            # Previous DSI for trend
            cogs_t1 = get_val(income_stmt, "Cost Of Revenue", t_minus_1)
            inventory_t2 = (
                get_val(balance_sheet, "Inventory", dates[2])
                if len(dates) > 2
                else inventory_t1
            )

            if cogs_t1 > 0:
                avg_inv_prev = (inventory_t1 + inventory_t2) / 2
                dsi_prev = (avg_inv_prev / cogs_t1) * 365
                dsi_change = (
                    (dsi_current - dsi_prev) / dsi_prev if dsi_prev > 0 else 0.0
                )

        # --- 4. Other Distress Metrics ---
        interest_expense = get_val(income_stmt, "Interest Expense", t)
        interest_coverage = None
        if interest_expense > 0:
            # Note: Interest Expense is usually negative in yfinance, so abs()
            interest_coverage = round(ebit / abs(interest_expense), 2)

        current_ratio = (
            round(current_assets / current_liabilities, 2)
            if current_liabilities > 0
            else None
        )

        output = RiskMetricsOutput(
            ticker=ticker,
            altman_z_score=z_score,
            beneish_m_score=m_score,
            piotroski_f_score=None,  # TODO: Add later if needed
            days_sales_in_inventory=round(dsi_current, 2) if dsi_current else None,
            dsi_change_pct=round(dsi_change, 4) if dsi_change else None,
            interest_coverage_ratio=interest_coverage,
            current_ratio=current_ratio,
        )
        return output.model_dump_json()

    except Exception as e:
        return RiskMetricsOutput(
            ticker=ticker, error=f"Error calculating risk metrics: {str(e)}"
        ).model_dump_json()
