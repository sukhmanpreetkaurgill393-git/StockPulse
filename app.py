import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import os

st.set_page_config(
    page_title="StockPulse | AI Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual styling ----------
st.markdown("""
<style>
:root { color-scheme: dark; }

.stApp {
    background: radial-gradient(circle at 10% 0%, #12243b 0, #09111f 35%, #070c15 100%);
    color: #eef4ff;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101c2e 0%, #0a1220 100%);
    border-right: 1px solid rgba(148,163,184,.18);
}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

h1, h2, h3 { color: #f4f8ff !important; }

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(22,39,61,.96), rgba(13,25,42,.96));
    border: 1px solid rgba(148,163,184,.20);
    padding: 18px 18px 14px 18px;
    border-radius: 16px;
    box-shadow: 0 8px 28px rgba(0,0,0,.16);
}

div[data-testid="stMetricLabel"] { color: #a9bbd3; }
div[data-testid="stMetricValue"] { color: #f6fbff; }
div[data-testid="stMetricDelta"] { font-weight: 600; }

.stButton > button {
    border-radius: 10px;
    border: 1px solid #2dd4a7;
    background: #12a982;
    color: #041510;
    font-weight: 700;
}

.stButton > button:hover {
    background: #2dd4a7;
    color: #041510;
    border-color: #2dd4a7;
}

div[data-testid="stAlert"] { border-radius: 12px; }

.small-muted {
    color: #9db0c8;
    font-size: .92rem;
}

.hero {
    padding: 1.35rem 1.5rem;
    border-radius: 20px;
    margin-bottom: 1.1rem;
    background: linear-gradient(115deg, rgba(20,49,73,.95), rgba(13,27,45,.95));
    border: 1px solid rgba(45,212,167,.24);
}

.hero-kicker {
    color: #45e0b5;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-size: .76rem;
    font-weight: 800;
}

.hero-title {
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 800;
    color: #f4f8ff;
    margin: .35rem 0;
}

.hero-copy { color: #b8c8dc; margin: 0; }

.section-card {
    background: rgba(16,29,47,.76);
    border: 1px solid rgba(148,163,184,.18);
    padding: 1rem 1.1rem;
    border-radius: 16px;
    margin-bottom: .8rem;
}
</style>
""", unsafe_allow_html=True)


# ---------- Data helpers ----------

@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data(ticker: str, period: str) -> pd.DataFrame:
    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if data is None or data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.rename_axis("Date").reset_index()

    needed = ["Date", "Open", "High", "Low", "Close", "Volume"]

    return data[[c for c in needed if c in data.columns]].dropna(
        subset=["Close"]
    )


def money(value):
    return "—" if pd.isna(value) else f"${value:,.2f}"


def build_price_chart(data, ticker, show_average=True):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Close"],
        name="Close price",
        mode="lines",
        line=dict(color="#35d6a4", width=2.6),
        fill="tozeroy",
        fillcolor="rgba(53,214,164,0.08)"
    ))

    if show_average and len(data) >= 7:
        ma = data["Close"].rolling(7).mean()

        fig.add_trace(go.Scatter(
            x=data["Date"],
            y=ma,
            name="7-day average",
            mode="lines",
            line=dict(color="#80aaff", width=1.8, dash="dot")
        ))

    fig.update_layout(
        template="plotly_dark",
        height=390,
        margin=dict(l=8, r=8, t=30, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.08, x=0),
        xaxis_title="",
        yaxis_title="Price (USD)",
        hovermode="x unified"
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.12)")

    return fig


def get_change(data):
    first = data["Close"].iloc[0]
    last = data["Close"].iloc[-1]

    if hasattr(first, "item"):
        first = first.item()

    if hasattr(last, "item"):
        last = last.item()

    first = float(first)
    last = float(last)

    if first == 0:
        return 0.0

    return ((last - first) / first) * 100


def get_risk_label(data):
    if data is None or "Close" not in data.columns:
        return "Insufficient data", float("nan")

    close = pd.to_numeric(
        data["Close"], errors="coerce"
    ).dropna()

    returns = close.pct_change().dropna()

    if len(returns) < 5:
        return "Insufficient data", float("nan")

    volatility = returns.std() * (252 ** 0.5) * 100

    if pd.isna(volatility):
        return "Insufficient data", float("nan")

    annualized_vol = float(volatility)

    if annualized_vol < 20:
        risk = "Low"
    elif annualized_vol < 40:
        risk = "Moderate"
    else:
        risk = "High"

    return risk, annualized_vol


def get_demo_trend(data):
    if data is None or len(data) < 10:
        return "Insufficient data"

    close = pd.to_numeric(
        data["Close"], errors="coerce"
    ).dropna()

    if len(close) < 10:
        return "Insufficient data"

    recent = float(close.tail(5).mean())
    previous = float(close.iloc[-10:-5].mean())

    if previous <= 0:
        return "Insufficient data"

    gap = ((recent - previous) / previous) * 100

    if gap > 0.5:
        return "UP"
    elif gap < -0.5:
        return "DOWN"
    else:
        return "STABLE"


def get_support_resistance(data):
    window = data.tail(min(30, len(data)))

    if window.empty:
        return None, None

    return (
        float(window["Low"].min()),
        float(window["High"].max())
    )


def load_or_warn(ticker, period):
    with st.spinner(f"Loading {ticker} market data…"):
        data = load_stock_data(ticker, period)

    if data.empty:
        st.error(
            "Market data could not be loaded. Check the ticker symbol "
            "and internet connection, then try again."
        )

        st.info(
            "Examples: AAPL, MSFT, TSLA, RELIANCE.NS, TCS.NS."
        )

        return None

    return data


# ---------- Sidebar ----------

with st.sidebar:

    st.markdown("## 📈 StockPulse")
    st.caption("AI Stock Analytics")
    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Stock Analysis",
            "Compare Stocks",
            "Support & Resistance",
            "Risk Analysis",
            "AI Prediction & Reports",
            "About Project"
        ],
        label_visibility="visible",
    )

    st.markdown("---")
    st.markdown("**Market data**")

    primary_ticker = st.selectbox(
        "Choose a stock",
        [
            "AAPL", "MSFT", "TSLA", "NVDA",
            "AMZN", "GOOGL", "RELIANCE.NS",
            "TCS.NS", "INFY.NS"
        ],
        index=0,
        help="US ticker symbols and selected NSE symbols are supported."
    )

    period_label = st.selectbox(
        "History period",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"],
        index=2
    )

    period_map = {
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y"
    }

    period = period_map[period_label]

    st.markdown(
        "<p class='small-muted'>Market data is provided for learning and demonstration.</p>",
        unsafe_allow_html=True
    )


# ---------- Main header ----------

st.markdown("""
<div class="hero">
    <div class="hero-kicker">Market intelligence workspace</div>
    <div class="hero-title">
        StockPulse <span style="color:#45e0b5">/</span> AI Stock Analytics
    </div>
    <p class="hero-copy">
        Explore price history, compare stocks, and review trend,
        risk, and technical levels in one workspace.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------- Pages ----------

if page == "Overview":

    st.subheader("Market overview")
    st.caption(f"{primary_ticker} · {period_label}")

    data = load_or_warn(primary_ticker, period)

    if data is not None:

        latest = float(data["Close"].iloc[-1])

        previous = (
            float(data["Close"].iloc[-2])
            if len(data) > 1 else latest
        )

        daily_pct = (
            ((latest - previous) / previous * 100)
            if previous else 0
        )

        total_pct = get_change(data)
        trend = get_demo_trend(data)
        risk, volatility = get_risk_label(data)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Latest price", money(latest), f"{daily_pct:+.2f}% today")
        c2.metric("Period change", f"{total_pct:+.2f}%")
        c3.metric("Trend signal · DEMO", trend)
        c4.metric(
            "Volatility risk · DEMO",
            risk,
            f"{volatility:.1f}% annualized"
            if pd.notna(volatility) else None
        )

        left, right = st.columns([1.8, 1])

        with left:
            st.markdown("### Price performance")

            st.plotly_chart(
                build_price_chart(data, primary_ticker),
                use_container_width=True
            )

        with right:
            st.markdown("### Snapshot")

            st.markdown(
                f"<div class='section-card'><span class='small-muted'>Period high</span><h3>{money(data['High'].max())}</h3></div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='section-card'><span class='small-muted'>Period low</span><h3>{money(data['Low'].min())}</h3></div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='section-card'><span class='small-muted'>Latest volume</span><h3>{float(data['Volume'].iloc[-1]):,.0f}</h3></div>",
                unsafe_allow_html=True
            )


elif page == "Stock Analysis":

    st.subheader("Stock analysis")

    col1, col2 = st.columns([1, 1])

    with col1:
        custom_ticker = st.text_input(
            "Enter ticker symbol",
            value=primary_ticker,
            help="Examples: AAPL, MSFT, RELIANCE.NS"
        )

    with col2:
        show_ma = st.toggle(
            "Show 7-day moving average",
            value=True
        )

    ticker = custom_ticker.strip().upper()

    if ticker:

        data = load_or_warn(ticker, period)

        if data is not None:

            latest = float(data["Close"].iloc[-1])
            change = get_change(data)
            trend = get_demo_trend(data)

            a, b, c = st.columns(3)

            a.metric("Latest close", money(latest))
            b.metric("Period return", f"{change:+.2f}%")
            c.metric("Trend signal · DEMO", trend)

            st.plotly_chart(
                build_price_chart(data, ticker, show_ma),
                use_container_width=True
            )

            with st.expander("View historical data"):
                st.dataframe(
                    data.sort_values("Date", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )


elif page == "Compare Stocks":

    st.subheader("Compare two stocks")
    st.caption("Compare percentage performance across the same selected time period.")

    c1, c2 = st.columns(2)

    stock_options = [
        "AAPL", "MSFT", "TSLA", "NVDA",
        "AMZN", "GOOGL", "RELIANCE.NS",
        "TCS.NS", "INFY.NS"
    ]

    with c1:
        ticker_a = st.selectbox(
            "Stock A", stock_options, index=0
        )

    with c2:
        ticker_b = st.selectbox(
            "Stock B", stock_options, index=1
        )

    if ticker_a == ticker_b:

        st.warning("Choose two different stocks to compare.")

    else:

        with st.spinner("Loading both stocks…"):
            da = load_stock_data(ticker_a, period)
            db = load_stock_data(ticker_b, period)

        if da.empty or db.empty:

            st.error(
                "Could not load one or both stocks. "
                "Check internet connection and ticker symbols."
            )

        else:

            da = da[["Date", "Close"]].dropna().copy()
            db = db[["Date", "Close"]].dropna().copy()

            da["Performance (%)"] = (
                da["Close"] / da["Close"].iloc[0] - 1
            ) * 100

            db["Performance (%)"] = (
                db["Close"] / db["Close"].iloc[0] - 1
            ) * 100

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=da["Date"],
                y=da["Performance (%)"],
                name=ticker_a,
                mode="lines",
                line=dict(width=2.5, color="#35d6a4")
            ))

            fig.add_trace(go.Scatter(
                x=db["Date"],
                y=db["Performance (%)"],
                name=ticker_b,
                mode="lines",
                line=dict(width=2.5, color="#80aaff")
            ))

            fig.update_layout(
                template="plotly_dark",
                height=430,
                hovermode="x unified",
                yaxis_title="Change from period start (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.08, x=0),
                margin=dict(l=8, r=8, t=30, b=8)
            )

            fig.update_yaxes(
                gridcolor="rgba(148,163,184,.12)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            m1, m2 = st.columns(2)

            m1.metric(
                f"{ticker_a} period return",
                f"{float(da['Performance (%)'].iloc[-1]):+.2f}%"
                if len(da) > 1 else "—"
            )

            m2.metric(
                f"{ticker_b} period return",
                f"{float(db['Performance (%)'].iloc[-1]):+.2f}%"
                if len(db) > 1 else "—"
            )


elif page == "Support & Resistance":

    st.subheader("Support & resistance")

    data = load_or_warn(primary_ticker, period)

    if data is not None:

        support, resistance = get_support_resistance(data)

        st.caption(f"Selected stock: {primary_ticker}")

        a, b = st.columns(2)

        a.metric("Demo support level", money(support))
        b.metric("Demo resistance level", money(resistance))

        fig = build_price_chart(
            data, primary_ticker, False
        )

        fig.add_hline(
            y=support,
            line_dash="dash",
            line_color="#35d6a4",
            annotation_text="Demo support"
        )

        fig.add_hline(
            y=resistance,
            line_dash="dash",
            line_color="#ff8c8c",
            annotation_text="Demo resistance"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


elif page == "Risk Analysis":

    st.subheader("Risk & volatility")

    data = load_or_warn(primary_ticker, period)

    if data is not None:

        risk, volatility = get_risk_label(data)

        returns = (
            data["Close"].pct_change().dropna() * 100
        )

        a, b, c = st.columns(3)

        a.metric("Indicative risk band · DEMO", risk)

        b.metric(
            "Annualized volatility · DEMO",
            f"{volatility:.1f}%"
            if pd.notna(volatility) else "—"
        )

        c.metric(
            "Daily return observations",
            f"{len(returns):,}"
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data["Date"].iloc[1:],
            y=returns,
            name="Daily return (%)",
            marker_color=[
                "#35d6a4" if v >= 0 else "#ff7777"
                for v in returns
            ]
        ))

        fig.update_layout(
            template="plotly_dark",
            height=380,
            yaxis_title="Daily return (%)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=25, b=8)
        )

        fig.update_yaxes(
            gridcolor="rgba(148,163,184,.12)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


elif page == "AI Prediction & Reports":

    st.subheader("StockPulse AI Prediction & Research")

    st.caption(
        "Machine Learning Predictions, Technical Analysis "
        "and Risk Reports"
    )

    # FRONTEND INTEGRATION
    st.iframe(
    "https://stock-price-trend-predictor.vercel.app",
    height=1000
)
    


elif page == "About Project":
    st.subheader("About StockPulse")

    st.markdown("""
    <div class="section-card">
        <h3>Project objective</h3>
        <p class="small-muted">
        A student project dashboard for exploring historical stock prices,
        displaying a machine-learning trend prediction, reviewing
        volatility-based risk, mapping support/resistance levels,
        and comparing two stocks.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Team responsibilities")

    team = pd.DataFrame([
        {
            "Member": "Manveer",
            "Module": "Machine Learning & Data",
            "Integration": "Trend prediction and model evaluation"
        },
        {
            "Member": "Arash Pathania",
            "Module": "Risk Analysis",
            "Integration": "Volatility method and agreed risk thresholds"
        },
        {
            "Member": "Vijay",
            "Module": "Support & Resistance",
            "Integration": "Price levels and chart overlays"
        },
        {
            "Member": "Sukhmanpreet Kaur",
            "Module": "Dashboard & Stock Comparison",
            "Integration": "UI, navigation, charts and two-stock comparison"
        },
    ])

    st.dataframe(
        team,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Project disclaimer")

    st.info(
        "This application is an educational prototype, not financial advice. "
        "Demo calculations should be verified against the team's final implementations."
    )

    st.caption("StockPulse · Student project prototype")


# ---------- Footer ----------

st.markdown("---")

st.markdown(
    "<p class='small-muted'>StockPulse is an educational prototype. "
    "Historical market data can be delayed, incomplete, or unavailable. "
    "Nothing on this dashboard is a recommendation to buy or sell securities.</p>",
    unsafe_allow_html=True
)

