# EquityPulse: The 50+ Parameter Analysis Engine 🧠

EquityPulse is not a simple "summary bot". It is a **Reasoning Engine** that orchestrates 5 specialized agents to analyze over 50 specific financial, technical, and macroeconomic parameters.

This document outlines the exact data points and logical checks performed by each agent during a single analysis session.

---

## 1. 🏰 The Fundamental Analyst (Buffett Style)
**Goal:** Determine Intrinsic Value and Moat Durability.
**Data Sources:** 10-K/10-Q, Balance Sheet, Income Statement, Cash Flow Statement.

### Key Metrics Tracked:
*   **ROIC (Return on Invested Capital)**: The primary litmus test for a "Moat". (>15% is good).
*   **FCF Yield (Free Cash Flow)**: The true earnings yield of the business.
*   **WACC (Weighted Average Cost of Capital)**: Compared against ROIC to measure value creation.
*   **Debt/Equity Ratio**: Solvency check.
*   **Interest Coverage Ratio**: Can they survive a rate hike?
*   **Gross Margin Trend**: Is pricing power increasing or decreasing?
*   **Operating Margin**: Efficiency check.
*   **Revenue CAGR (3yr/5yr)**: Sustainable top-line growth.
*   **Net Income CAGR**: Bottom-line execution.
*   **Share Buyback Yield**: Is management cannibalizing shares or diluting shareholders?
*   **Book Value Per Share**: Asset growth.

---

## 2. 🔢 The Quant Analyst (Jim Simons Style)
**Goal:** Mathematical scoring of "Smart Money" flows and Fraud Detection.
**Data Sources:** Insider Filings (Form 4), Institutional 13F, Price Volume Data.

### Key Metrics Tracked:
*   **Altman Z-Score**: A bankruptcy prediction model. (<1.8 = Distress).
*   **Beneish M-Score**: A forensic accounting model to detect earnings manipulation/fraud.
*   **Insider Net Buying/Selling**: Are executives buying with their own money?
*   **Insider Cluster Buys**: Did multiple executives buy at once? (High conviction signal).
*   **Institutional Ownership %**: "Smart Money" sponsorship.
*   **PEG Ratio**: Valuation adjusted for growth. (>2.0 = Overvalued).
*   **Short Float %**: Is the smart money betting against it? (>15% = Squeeze Potential or Fraud).
*   **Price/Sales Ratio**: Valuation against revenue.
*   **EV/EBITDA**: The "Acquirer's Multiple".

---

## 3. 🐻 The Risk Manager (The "Bear")
**Goal:** "Kill the Trade". Identify downside, geopolitical, and structural risks.
**Data Sources:** Global News, Macro Reports, Litigation Filings, Supply Chain Data.

### Key Metrics & Qualitative Checks:
*   **Geopolitical Exposure**: Revenue % from high-conflict regions (e.g., China/Taiwan risk).
*   **Supply Chain Concentration**: Dependence on single suppliers (e.g., ASML, TSMC).
*   **Litigation Risk**: Active lawsuits, patent cliffs, or regulatory probes.
*   **Executive Turnover**: Sudden CFO/CEO departures (often a red flag).
*   **Regulatory Headwinds**: Antitrust actions, tariff impact, or environmental regulations.
*   **Macro Sensitivity**: Analysis of sensitivity to Interest Rate Hikes or Inflation.
*   **Bear Case Probability**: A 0-100% calculated probability of the stock dropping.

---

## 4. 🌍 The Sector Strategist (Global Macro)
**Goal:** Analyze the Business Cycle and Sector Rotation.
**Data Sources:** Sector ETFS, Fed Reports, Commodity Prices.

### Key Metrics & Checks:
*   **Business Cycle Stage**: Early, Mid, Late, or Recession?
*   **Sector Rotation Flows**: Is money flowing INTO or OUT of this industry?
*   **Relative Strength (RS)**: Performance vs S&P 500.
*   **Rate Sensitivity**: Impact of Fed policy on this specific sector.
*   **Tailwinds**: Secular trends (e.g., AI Capex, Green Energy Subsidies).
*   **Headwinds**: Structural decline, commoditization.
*   **Competitor Analysis**: Market share battles and pricing wars.

---

## 5. 📊 The Technical Analyst (The "Trader")
**Goal:** Time the Entry/Exit. Optimize Risk/Reward.
**Data Sources:** Price Action, Volume Profile, Moving Averages.

### Key Metrics Tracked:
*   **RSI (Relative Strength Index)**: Overbought (>70) or Oversold (<30).
*   **MACD (Moving Average Convergence Divergence)**: Momentum trend and crossovers.
*   **Bollinger Bands**: Volatility analysis.
*   **Volume Weighted Average Price (VWAP)**: Institutional support levels.
*   **Simple Moving Averages (20/50/200)**: Trend identification (Golden Cross/Death Cross).
*   **Support/Resistance Levels**: Key price zones to watch.
*   **Market Structure**: Higher Highs/Lower Lows analysis.

---

## 🧠 The Reasoning Engine (Gemini 3.0 Pro)

All of the above parameters are not just calculated; they are **debated**. The **Portfolio Manager** node takes these 5 conflicting reports and synthesizes them into a final verdict, weighing the "Headwinds" against the "Tailwinds" using Gemini 3.0 Pro's infinite context window.
