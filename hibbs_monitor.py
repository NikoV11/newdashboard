import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION & STYLING ---
# Professional Color Palette
COLOR_PRIMARY = "#002F6C"  # Deep Navy (for main headers/lines)
COLOR_ACCENT = "#CB6015"   # Rust Orange (for secondary highlights)
COLOR_BG = "#FFFFFF"       # White

st.set_page_config(
    page_title="Hibbs Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enforce the specific color scheme and professional typography
st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: {COLOR_BG};
    }}
    /* Headers */
    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    /* Metric Cards */
    div[data-testid="stMetricValue"] {{
        color: {COLOR_ACCENT} !important;
    }}
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- TRACKER CONFIGURATION (Add more series here) ---
# To add a new tracker, just find the Series ID on FRED website and add it here.
TRACKERS = [
    {
        "id": "GDPC1",
        "name": "Real Gross Domestic Product (rGDP)",
        "frequency": "Quarterly",
        "units": "Billions of Chained 2012 Dollars",
        "color": COLOR_PRIMARY,
        "type": "line"
    },
    {
        "id": "CPIAUCSL",
        "name": "Consumer Price Index (CPI-U)",
        "frequency": "Monthly",
        "units": "Index 1982-1984=100",
        "color": COLOR_ACCENT,
        "type": "line"
    },
    # EXAMPLE: Uncomment the lines below to add Unemployment Rate easily
    # {
    #     "id": "UNRATE",
    #     "name": "Unemployment Rate",
    #     "frequency": "Monthly",
    #     "units": "Percent",
    #     "color": COLOR_PRIMARY,
    #     "type": "line"
    # },
]

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to improve performance
def fetch_fred_data(api_key, series_id, start_date):
    """Fetches series data from FRED API with error handling."""
    try:
        fred = Fred(api_key=api_key)
        # Fetch data
        data = fred.get_series(series_id, observation_start=start_date)
        
        # Fetch metadata (title, units, etc.)
        info = fred.get_series_info(series_id)
        
        df = pd.DataFrame(data, columns=['Value'])
        df.index.name = 'Date'
        return df, info
    except Exception as e:
        return None, str(e)

def calculate_yoy_growth(df):
    """Calculates Year-Over-Year growth rate."""
    # Frequency handling: if monthly (12 periods), if quarterly (4 periods)
    # We infer frequency roughly by index gap, default to 4 (Quarterly) for safety or 12 for CPI
    periods = 4
    if len(df) > 1:
        days_diff = (df.index[1] - df.index[0]).days
        if days_diff < 40: # Likely monthly
            periods = 12
    
    df['YoY %'] = df['Value'].pct_change(periods=periods) * 100
    return df

# --- UI COMPONENTS ---
def plot_professional_chart(df, info, config):
    """Creates an economist-grade Plotly chart."""
    
    # Create figure
    fig = go.Figure()

    # Add Main Trace
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Value'],
        mode='lines',
        name=config['name'],
        line=dict(color=config['color'], width=2.5),
        hovertemplate='%{x|%b %Y}: <b>%{y:,.1f}</b><extra></extra>'
    ))

    # Professional Layout
    fig.update_layout(
        title=dict(
            text=f"<b>{config['name']}</b>",
            font=dict(size=18, color=COLOR_PRIMARY),
            x=0,
            xanchor='left'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0),
        height=350,
        hovermode="x unified",
        xaxis=dict(
            showgrid=True, 
            gridcolor='#e6e6e6',
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#e6e6e6', 
            gridwidth=1,
            title=dict(text=info.get('units', ''), font=dict(size=12, color='#666'))
        )
    )
    return fig

# --- MAIN APP LAYOUT ---

def main():
    # Sidebar: Controls
    st.sidebar.title("⚙️ Monitor Settings")
    
    # API Key Input (Secure) - Use secrets in production, fallback to input
    try:
        api_key = st.secrets["FRED_API_KEY"]
    except:
        api_key = st.sidebar.text_input(
            "Enter FRED API Key", 
            type="password", 
            help="Get your key from https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    # Date Filter
    st.sidebar.subheader("Time Horizon")
    start_year = st.sidebar.slider("Start Year", 1950, datetime.now().year, 2000)
    start_date = f"{start_year}-01-01"

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Hibbs Monitor v1.0**")
    st.sidebar.markdown(f"Designed for Economic Analysis")

    # Main Page Header
    st.title("Hibbs Monitor")
    st.markdown(f"**Real-Time Economic Tracker** | Data Source: Federal Reserve Bank of St. Louis")
    st.markdown("---")

    if not api_key:
        st.warning("⚠️ Please enter your FRED API Key in the sidebar to load the dashboard.")
        st.info("Don't have a key? [Click here to request one free](https://fred.stlouisfed.org/docs/api/api_key.html).")
        return

    # Loop through trackers and render
    for tracker in TRACKERS:
        
        # Create a container for each metric to keep it organized
        with st.container():
            df, info = fetch_fred_data(api_key, tracker['id'], start_date)

            if df is not None and not df.empty:
                # Layout: Metrics on left, Chart on right? Or Top/Bottom? 
                # Professional layout: KPI Card on top, Chart below.
                
                # Calculate latest stats
                latest_value = df['Value'].iloc[-1]
                prev_value = df['Value'].iloc[-2]
                delta = latest_value - prev_value
                delta_percent = (delta / prev_value) * 100
                last_date = df.index[-1].strftime('%b %Y')

                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"### {tracker['name']}")
                    st.metric(
                        label=f"Latest Reading ({last_date})",
                        value=f"{latest_value:,.2f}",
                        delta=f"{delta_percent:.2f}% (Period Change)"
                    )
                    st.caption(f"**ID:** {tracker['id']} | **Freq:** {tracker['frequency']}")
                    
                    # Add a toggle for raw data
                    with st.expander("View Raw Data"):
                        st.dataframe(df.sort_index(ascending=False).head(10), height=150)

                with col2:
                    fig = plot_professional_chart(df, info, tracker)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
            
            else:
                st.error(f"Failed to load data for {tracker['name']}. Error: {info}")

if __name__ == "__main__":
    main()