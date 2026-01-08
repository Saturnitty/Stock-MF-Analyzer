import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Equity & Mutual Fund Analyzer",
    layout="wide"
)

st.title("📊 Equity & Mutual Fund Analyzer")

# =================================================
# ASSET TYPE SELECTOR
# =================================================
asset_type = st.radio(
    "Select Asset Type",
    ["Equity Stock", "Mutual Fund"],
    horizontal=True
)

# =================================================
# ================= EQUITY STOCK ANALYSIS ==========
# =================================================
if asset_type == "Equity Stock":

    # ---------------- METRIC DEFINITIONS ----------------
    METRIC_INFO = {
        "pe": {
            "label": "P/E Ratio",
            "inverse": True,
            "range": "<15 Cheap | 15–25 Fair | >25 Expensive",
        },
        "roe": {
            "label": "ROE",
            "inverse": False,
            "range": "<10% Weak | 10–15% Avg | >15% Strong",
        },
        "margin": {
            "label": "Operating Margin",
            "inverse": False,
            "range": "<10% Weak | 10–20% Healthy | >20% Strong",
        },
        "rev_growth": {
            "label": "Revenue Growth",
            "inverse": False,
            "range": "<5% Low | 5–12% Moderate | >12% High",
        },
        "de": {
            "label": "Debt / Equity",
            "inverse": True,
            "range": "<0.5 Safe | 0.5–1 Acceptable | >1 Risky",
        },
    }

    # ---------------- COMPLETE SECTOR PEERS (INDIA) ----------------
    SECTOR_PEERS = {
        "Information Technology": [
            "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"
        ],
        "Financial Services": [
            "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS",
            "SBIN.NS", "KOTAKBANK.NS"
        ],
        "Consumer Defensive": [
            "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS",
            "DABUR.NS", "BRITANNIA.NS"
        ],
        "Consumer Cyclical": [
            "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS",
            "BAJAJ-AUTO.NS", "EICHERMOT.NS"
        ],
        "Healthcare": [
            "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS",
            "DIVISLAB.NS", "APOLLOHOSP.NS"
        ],
        "Metals & Mining": [
            "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS",
            "NMDC.NS", "COALINDIA.NS"
        ],
        "Energy": [
            "RELIANCE.NS", "ONGC.NS", "BPCL.NS",
            "IOC.NS", "GAIL.NS"
        ],
        "Industrials": [
            "LT.NS", "SIEMENS.NS", "ABB.NS",
            "CUMMINSIND.NS", "BHEL.NS"
        ],
        "Utilities": [
            "NTPC.NS", "POWERGRID.NS", "ADANIPOWER.NS"
        ],
        "Communication Services": [
            "BHARTIARTL.NS", "TATACOMM.NS"
        ],
        "Real Estate": [
            "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS"
        ],
    }

    # ---------------- FUNCTIONS ----------------
    @st.cache_data
    def get_stock_data(ticker):
        t = yf.Ticker(ticker)
        return t.info, t.history(period="1y")

    def extract_metrics(info):
        return {
            "pe": info.get("trailingPE"),
            "roe": info.get("returnOnEquity"),
            "margin": info.get("operatingMargins"),
            "rev_growth": info.get("revenueGrowth"),
            "de": info.get("debtToEquity"),
        }

    @st.cache_data
    def sector_averages(peers):
        rows = []
        for p in peers:
            i = yf.Ticker(p).info
            rows.append({
                "pe": i.get("trailingPE"),
                "roe": i.get("returnOnEquity"),
                "margin": i.get("operatingMargins"),
                "rev_growth": i.get("revenueGrowth"),
                "de": i.get("debtToEquity"),
            })
        return pd.DataFrame(rows).mean(numeric_only=True)

    def build_comparison(stock, sector):
        rows = []
        for k, meta in METRIC_INFO.items():
            s, sec = stock.get(k), sector.get(k)
            if s is None or sec is None:
                verdict = "—"
            else:
                better = s < sec if meta["inverse"] else s > sec
                verdict = "Better" if better else "Worse"

            rows.append({
                "Metric": meta["label"],
                "Stock": s,
                "Sector Avg": sec,
                "Interpretation": meta["range"],
                "Verdict": verdict,
            })
        return pd.DataFrame(rows)
    

    def why_this_stock(stock, sector):
        positives, negatives = [], []
        for k, meta in METRIC_INFO.items():
            s, sec = stock.get(k), sector.get(k)
            if s is None or sec is None:
                continue
            better = s < sec if meta["inverse"] else s > sec
            (positives if better else negatives).append(meta["label"])

        if not positives and not negatives:
            return "The stock performs broadly in line with sector peers."

        text = []
        if positives:
            text.append(f"Strengths: {', '.join(positives)}.")
        if negatives:
            text.append(f"Weaknesses: {', '.join(negatives)}.")
        return " ".join(text)

    # ---------------- UI ----------------
    symbol = st.text_input("Stock Symbol (e.g. RELIANCE, TCS)", "RELIANCE")
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    ticker = symbol.upper() + (".NS" if exchange == "NSE" else ".BO")

    if st.button("Analyze Stock"):
        info, hist = get_stock_data(ticker)

        if not info or "sector" not in info:
            st.error("Unable to fetch stock data.")
            st.stop()

        sector = info.get("sector")
        industry = info.get("industry")

        st.subheader("🏷 Company Classification")
        st.table(pd.DataFrame({
            "Category": ["Sector", "Industry"],
            "Value": [sector, industry],
        }))

        stock_metrics = extract_metrics(info)

        if sector in SECTOR_PEERS:
            sector_avg = sector_averages(SECTOR_PEERS[sector])
            comparison = build_comparison(stock_metrics, sector_avg)

            st.subheader("📊 Stock vs Sector Comparison")
            st.dataframe(comparison, use_container_width=True)

            st.subheader("🧠 Why this stock?")
            st.write(why_this_stock(stock_metrics, sector_avg))
        else:
            st.info(
                f"Sector benchmarking is not available for **{sector}** yet. "
                "Raw metrics are shown without peer comparison."
            )
        # ---------------- EXPECTED RETURN (INDICATIVE) ----------------
        rev = stock_metrics.get("rev_growth") or 0
        roe = stock_metrics.get("roe") or 0
        de = stock_metrics.get("de") or 0

        roe_bonus = 0.03 if roe > 0.15 else 0
        de_penalty = 0.02 if de > 1 else 0

        expected_return_stock = rev + roe_bonus - de_penalty

        st.subheader("🎯 Expected Return (Indicative)")
        st.write(
        f"**Expected annual return:** **{expected_return_stock*100:.2f}%**\n\n"
        "Based on revenue growth, profitability (ROE), and leverage risk.\n"
        "This is an estimate for comparison, not a prediction."
        )
        st.subheader("📉 1-Year Price Trend")
        st.line_chart(hist["Close"])

# =================================================
# ================= MUTUAL FUND ANALYSIS ===========
# =================================================
else:
    st.subheader("📈 Mutual Fund Analysis (India – MFAPI)")

    scheme_code = st.text_input(
        "Mutual Fund Scheme Code (from https://www.mfapi.in/)",
        "118834"
    )

    def mf_verdict(metric, value):
        if metric in ["1Y CAGR", "3Y CAGR"]:
            if value > 0.12:
                return "✅ Good"
            elif value >= 0.08:
                return "🟡 Average"
            else:
                return "🔴 Poor"

        if metric == "Volatility":
            if value < 0.15:
                return "✅ Good"
            elif value <= 0.20:
                return "🟡 Average"
            else:
                return "🔴 Poor"

        if metric == "Sharpe Ratio":
            if value > 1:
                return "✅ Good"
            elif value >= 0.5:
                return "🟡 Average"
            else:
                return "🔴 Poor"

        if metric == "Max Drawdown":
            if value > -0.25:
                return "✅ Good"
            elif value >= -0.40:
                return "🟡 Average"
            else:
                return "🔴 Poor"

    if st.button("Analyze Mutual Fund"):
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        response = requests.get(url)

        if response.status_code != 200:
            st.error("Unable to fetch mutual fund data.")
            st.stop()

        data = response.json()

        nav_df = pd.DataFrame(data["data"])
        nav_df["date"] = pd.to_datetime(nav_df["date"], dayfirst=True)
        nav_df["nav"] = nav_df["nav"].astype(float)
        nav_df = nav_df.sort_values("date")

        nav_df["returns"] = nav_df["nav"].pct_change()

        nav_1y = nav_df[nav_df["date"] >= nav_df["date"].max() - pd.DateOffset(years=1)]
        nav_3y = nav_df[nav_df["date"] >= nav_df["date"].max() - pd.DateOffset(years=3)]

        cagr_1y = (nav_1y["nav"].iloc[-1] / nav_1y["nav"].iloc[0]) - 1
        cagr_3y = (nav_3y["nav"].iloc[-1] / nav_3y["nav"].iloc[0]) ** (1/3) - 1

        volatility = nav_df["returns"].std() * np.sqrt(252)
        sharpe = (nav_df["returns"].mean() * 252) / volatility
        max_dd = (nav_df["nav"] / nav_df["nav"].cummax() - 1).min()

        # ---------------- EXPECTED RETURN ----------------
        sharpe_adj = min(max(sharpe, 0.5), 1.2)
        expected_return_mf = cagr_3y * sharpe_adj

        st.subheader(data["meta"]["scheme_name"])

        mf_metrics = pd.DataFrame([
            {
                "Metric": "1Y CAGR",
                "Value": f"{cagr_1y*100:.2f}%",
                "Benchmark": ">12% Good | 8–12% Avg | <8% Poor",
                "Verdict": mf_verdict("1Y CAGR", cagr_1y),
            },
            {
                "Metric": "3Y CAGR",
                "Value": f"{cagr_3y*100:.2f}%",
                "Benchmark": ">12% Good | 8–12% Avg | <8% Poor",
                "Verdict": mf_verdict("3Y CAGR", cagr_3y),
            },
            {
                "Metric": "Volatility",
                "Value": f"{volatility*100:.2f}%",
                "Benchmark": "<15% Good | 15–20% Avg | >20% Poor",
                "Verdict": mf_verdict("Volatility", volatility),
            },
            {
                "Metric": "Sharpe Ratio",
                "Value": round(sharpe, 2),
                "Benchmark": ">1 Good | 0.5–1 Avg | <0.5 Poor",
                "Verdict": mf_verdict("Sharpe Ratio", sharpe),
            },
            {
                "Metric": "Max Drawdown",
                "Value": f"{max_dd*100:.2f}%",
                "Benchmark": ">-25% Good | -25–40% Avg | <-40% Poor",
                "Verdict": mf_verdict("Max Drawdown", max_dd),
            },
        ])

        st.subheader("📊 Mutual Fund Performance Evaluation")
        st.table(mf_metrics)

        st.subheader("🎯 Expected Return (Indicative)")
        st.write(
            f"**Expected annual return:** **{expected_return_mf*100:.2f}%**\n\n"
            "Based on long-term CAGR adjusted for risk (Sharpe ratio)."
        )

        st.subheader("📉 NAV Trend")
        st.line_chart(nav_df.set_index("date")["nav"])

        st.caption(
            "Benchmarks are generalized for equity mutual funds. "
            "Expected return is not a prediction and should be used for comparison only."
        )
