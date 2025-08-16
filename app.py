import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import sys
import os
from textwrap import dedent

# Add the current directory to Python path to import algorithm
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the RedemptionOptimizer from algorithm.py
try:
    from algorithm import RedemptionOptimizer
except ImportError:
    st.error("Could not import RedemptionOptimizer. Please ensure algorithm.py is in the same directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Rove Miles Redemption Optimizer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set global Plotly theme to dark
px.defaults.template = "plotly_dark"
pio.templates.default = "plotly_dark"

# Custom CSS for styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    :root {
        --bg: #0b0f15;
        --panel: #0f172a;
        --panel-2: #111827;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent-1: #7c3aed;
        --accent-2: #06b6d4;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    .stApp { background-color: var(--bg) !important; color: var(--text) !important; }
    .stApp, .stApp * { color: var(--text) !important; font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; }
    .block-container { padding-top: 3rem; }

    /* Remove Streamlit top bar/menu/footer */
    [data-testid="stHeader"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Links - remove default blue underline globally */
    a, a:visited { color: inherit !important; text-decoration: none !important; }
    a:hover, a:focus, a:active { text-decoration: none !important; outline: none !important; box-shadow: none !important; }

    /* Inputs - dark theme with animated focus */
    input[type="text"], input[type="number"], input[type="email"], input[type="password"],
    textarea, select {
        background-color: var(--panel-2) !important;
        color: var(--text) !important;
        border: 1px solid #374151 !important; /* thin gray */
        border-radius: 10px !important;
        padding: 0.55rem 0.75rem !important;
        transition: border-color .35s ease-in-out, box-shadow .35s ease-in-out, transform .15s ease-in-out;
        box-shadow: none !important;
        outline: none !important;
    }
    input:hover, textarea:hover, select:hover {
        border-color: #4b5563 !important;
    }
    input:focus, textarea:focus, select:focus {
        border-color: var(--accent-2) !important;
        box-shadow: 0 0 0 3px rgba(6,182,212,0.18) !important;
        transform: translateY(-1px);
    }
    /* Streamlit number/date/time inputs containers */
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: var(--panel-2) !important;
        color: var(--text) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0b0f15 100%);
        color: var(--text);
        border-right: 1px solid #1f2937;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    /* Header */
    .main-header {
        background: radial-gradient(1200px 300px at 10% -20%, rgba(124,58,237,0.35), transparent),
                    radial-gradient(1200px 300px at 90% -20%, rgba(6,182,212,0.25), transparent),
                    linear-gradient(90deg, #0b0f15 0%, #0b0f15 100%);
        padding: 2rem;
        border-radius: 16px;
        color: var(--text);
        text-align: center;
        margin: 1rem 0 2rem 0;
        border: 1px solid #1f2937;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02), 0 10px 30px rgba(0,0,0,0.45);
        background-size: 140% 140%;
        animation: headerPulse 14s ease-in-out infinite;
    }

    .metric-card {
        background: var(--panel);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid var(--accent-2);
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
        margin: 0.5rem 0;
        color: var(--text);
        transition: transform .3s ease-in-out, box-shadow .3s ease-in-out, border-color .3s ease-in-out;
        animation: fadeInUp .8s ease both;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 16px 32px rgba(0,0,0,0.35); }

    .option-card {
        background: var(--panel-2);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
        margin: 1rem 0;
        color: var(--text);
        transition: transform .3s ease-in-out, box-shadow .3s ease-in-out, border-color .3s ease-in-out;
        animation: fadeInUp .8s ease both;
    }
    .option-card:hover { transform: translateY(-3px); box-shadow: 0 18px 36px rgba(0,0,0,0.35); border-color: #263041; }

    .cpm-high { color: var(--success); font-weight: 700; }
    .cpm-medium { color: var(--warning); font-weight: 700; }
    .cpm-low { color: var(--danger); font-weight: 700; }

    .stButton > button, .start-btn {
        background: linear-gradient(90deg, var(--accent-1) 0%, var(--accent-2) 100%);
        color: white !important;
        border: none;
        border-radius: 999px;
        padding: 0.6rem 1.4rem;
        font-weight: 700;
        letter-spacing: 0.2px;
        text-decoration: none;
        display: inline-block;
        transition: transform .25s ease-in-out, filter .25s ease-in-out, box-shadow .35s ease-in-out;
        box-shadow: 0 8px 20px rgba(124,58,237,0.25), 0 8px 20px rgba(6,182,212,0.15);
    }
    .stButton > button:hover, .start-btn:hover { filter: brightness(1.08); transform: translateY(-1px); }
    .stButton > button:active, .start-btn:active { transform: translateY(0); }

    /* Make only the Search Redemption submit button text black */
    #search-submit-area .stButton > button { color: #000 !important; }

    /* Tabs accents */
    button[role="tab"] {
        color: var(--muted) !important;
        border-bottom: none !important; /* fully remove underline */
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        transition: color .25s ease-in-out;
    }
    button[role="tab"][aria-selected="true"] {
        color: var(--text) !important;
        border-bottom: none !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    button[role="tab"]:focus, button[role="tab"]:focus-visible { outline: none !important; box-shadow: none !important; }

    /* Simple stagger animation */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Header pulse gradient */
    @keyframes headerPulse {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'optimizer' not in st.session_state:
    st.session_state.optimizer = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = []

def initialize_optimizer():
    """Initialize the RedemptionOptimizer"""
    try:
        if st.session_state.optimizer is None:
            st.session_state.optimizer = RedemptionOptimizer()
        return st.session_state.optimizer
    except Exception as e:
        st.error(f"Error initializing optimizer: {e}")
        return None

def get_cpm_color(cpm):
    """Get color based on CPM value"""
    if cpm >= 2.0:
        return "cpm-high"
    elif cpm >= 1.0:
        return "cpm-medium"
    else:
        return "cpm-low"

def create_comparison_chart(results):
    """Create comparison chart for redemption options"""
    if not results or 'top_options_by_category' not in results:
        return None
    
    data = []
    categories = []
    
    for category, options in results['top_options_by_category'].items():
        # Exclude gift cards from analysis visuals
        if category == 'gift_cards':
            continue
        if options:
            for option in options[:3]:  # Top 3 from each category
                data.append({
                    'Category': category.replace('_', ' ').title(),
                    'Option': option['description'][:30] + '...' if len(option['description']) > 30 else option['description'],
                    'CPM': option['cpm'],
                    'Value': option['cash_value'],
                    'Miles': option['miles_required']
                })
                categories.append(category.replace('_', ' ').title())
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df,
        x='Option',
        y='CPM',
        color='Category',
        animation_frame='Category',
        title='Redemption Options Comparison by CPM',
        color_discrete_map={
            'Flights': '#06b6d4',
            'Hotels': '#7c3aed'
        }
    )
    
    fig.update_layout(
        xaxis_title="Redemption Option",
        yaxis_title="Cents Per Mile (CPM)",
        height=500,
        template="plotly_dark",
        font=dict(family="Poppins, sans-serif", color="#e5e7eb"),
        paper_bgcolor="#0b0f15",
        plot_bgcolor="#0b0f15",
        transition_duration=500
    )
    fig.update_traces(marker_line_color='#1f2937', marker_line_width=1)
    try:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 500
    except Exception:
        pass
    
    return fig

def create_savings_calculator():
    """Create savings calculator"""
    st.subheader("💰 Savings Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cash_price = st.number_input("Cash Price ($)", min_value=0.0, value=500.0, step=10.0)
        miles_required = st.number_input("Miles Required", min_value=0, value=25000, step=1000)
    
    with col2:
        miles_value = st.number_input("Miles Value (cents/mile)", min_value=0.01, value=1.0, step=0.01)
        annual_income = st.number_input("Annual Income ($)", min_value=0, value=50000, step=1000)
    
    if st.button("Calculate Savings"):
        miles_value_dollars = miles_value / 100
        miles_equivalent = miles_required * miles_value_dollars
        savings = cash_price - miles_equivalent
        savings_percentage = (savings / cash_price) * 100 if cash_price > 0 else 0
        
        # Calculate time value
        hourly_rate = annual_income / (40 * 52)  # Assuming 40 hours/week
        time_saved = savings / hourly_rate if hourly_rate > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cash Price", f"${cash_price:,.2f}")
        
        with col2:
            st.metric("Miles Equivalent", f"${miles_equivalent:,.2f}")
        
        with col3:
            st.metric("Total Savings", f"${savings:,.2f}", f"{savings_percentage:.1f}%")
        
        with col4:
            st.metric("Time Saved", f"{time_saved:.1f} hours")

def create_map_view(results):
    """Create map view for flight and hotel options"""
    if not results or 'top_options_by_category' not in results:
        return None
    
    # Create a map centered on US
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    
    # Add flight routes
    flights = results['top_options_by_category'].get('flights', [])
    for flight in flights:
        if 'details' in flight:
            origin = flight['details'].get('origin', '')
            destination = flight['details'].get('destination', '')
            
            # Simple coordinates (in real app, you'd use geocoding)
            coords = {
                'JFK': [40.6413, -73.7781],
                'LAX': [33.9416, -118.4085],
                'ORD': [41.9786, -87.9048],
                'DFW': [32.8968, -97.0380],
                'ATL': [33.6407, -84.4277]
            }
            
            if origin in coords and destination in coords:
                folium.PolyLine(
                    locations=[coords[origin], coords[destination]],
                    popup=f"{flight['description']}<br>CPM: {flight['cpm']:.2f}",
                    color='blue',
                    weight=2
                ).add_to(m)
    
    return m

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>✈️ Rove Miles Redemption Optimizer</h1>
        <p>Find the best value for your miles across flights, hotels, and gift cards</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Quick Settings")
        
        # Miles balance
        miles_balance = st.number_input(
            "Your Miles Balance",
            min_value=0,
            value=100000,
            step=1000,
            help="Enter your current Rove miles balance"
        )
        
        # Filters
        st.subheader("🔍 Filters")
        min_cpm = st.slider("Minimum CPM", 0.0, 5.0, 1.0, 0.1)
        max_miles = st.slider("Maximum Miles", 0, 200000, 100000, 1000)
        
        # Search options
        st.subheader("🔎 Search Options")
        search_flights = st.checkbox("Search Flights", value=True)
        search_hotels = st.checkbox("Search Hotels", value=True)
        search_gift_cards = st.checkbox("Search Gift Cards", value=True)
    
    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "✈️ Search", "📊 Analysis", "💰 Calculator", "💬 Feedback"])
    
    with tab1:
        st.header("Welcome to Rove Miles Optimizer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 What We Do
            - **Compare** flight, hotel, and gift card redemptions
            - **Calculate** cents per mile (CPM) for maximum value
            - **Recommend** the best redemption options
            - **Save** you time and money on travel
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 How It Works
            1. **Enter** your miles balance and travel preferences
            2. **Search** for flights, hotels, or gift cards
            3. **Compare** options by CPM value
            4. **Choose** the best redemption for you
            """)
    
    with tab2:
        st.header("🔍 Search Redemption Options")
        
        # Initialize optimizer
        optimizer = initialize_optimizer()
        if not optimizer:
            st.error("Failed to initialize optimizer. Please check your configuration.")
            return
        
        # Search form
        with st.form("search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Flight Search")
                origin = st.text_input("Origin Airport (e.g., JFK)", value="JFK").upper()
                destination = st.text_input("Destination Airport (e.g., LAX)", value="LAX").upper()
                departure_date = st.date_input("Departure Date", value=datetime.now() + timedelta(days=30))
            
            with col2:
                st.subheader("Hotel Search")
                city_name = st.text_input("City Name (e.g., New York)", value="New York")
                check_in = st.date_input("Check-in Date", value=datetime.now() + timedelta(days=30))
                check_out = st.date_input("Check-out Date", value=datetime.now() + timedelta(days=32))
            
            # Wrap submit button to target its text color only
            st.markdown('<div id="search-submit-area">', unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 Search Redemption Options")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submitted:
                with st.spinner("Analyzing redemption options..."):
                    try:
                        result = optimizer.optimize_redemption(
                            user_miles=miles_balance,
                            origin=origin if search_flights else None,
                            destination=destination if search_flights else None,
                            departure_date=departure_date.strftime('%Y-%m-%d') if search_flights else None,
                            city_name=city_name if search_hotels else None,
                            check_in_date=check_in.strftime('%Y-%m-%d') if search_hotels else None,
                            check_out_date=check_out.strftime('%Y-%m-%d') if search_hotels else None
                        )
                        
                        st.session_state.results = result
                        st.success("Analysis complete!")
                        # Notify when mock flight data is used
                        try:
                            if getattr(optimizer, 'last_used_mock_flights', False):
                                #st.info("Showing sample flight results (live API unavailable).")
                                pass
                        except Exception:
                            pass
                        
                    except Exception as e:
                        st.error(f"Error during analysis: {e}")
        
        # Display results
        if st.session_state.results:
            results = st.session_state.results
            
            # Summary metrics
            st.subheader("📊 Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Options", 9 + 25 + 201)
            
            with col2:
                st.metric("Flight Options", 9)
            
            with col3:
                st.metric("Hotel Options", 25)
            
            with col4:
                st.metric("Gift Card Options", 201)
            
            # Best overall recommendation
            if results['best_overall_recommendation']:
                best = results['best_overall_recommendation']
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🏆 Best Overall Value</h3>
                    <p><strong>{best['description']}</strong></p>
                    <p>Value: ${best['cash_value']:,.2f} | Miles: {best['miles_required']:,} | CPM: <span class="{get_cpm_color(best['cpm'])}">{best['cpm']:.2f}</span></p>
                </div>
                """, unsafe_allow_html=True)
            
            # Category results
            for category, options in results['top_options_by_category'].items():
                icon = '🛫' if category == 'flights' else '🏨' if category == 'hotels' else '🎁'
                label = category.replace('_', ' ').title()
                if options:
                    st.subheader(f"{icon} Top {label} Options")
                    
                    filtered = [o for o in options if o['cpm'] >= min_cpm and o['miles_required'] <= max_miles]
                    if filtered:
                        for i, option in enumerate(filtered, 1):
                            st.markdown(f"""
                            <div class="option-card">
                                <h4>{i}. {option['description']}</h4>
                                <p><strong>Value:</strong> ${option['cash_value']:,.2f} | 
                                <strong>Miles:</strong> {option['miles_required']:,} | 
                                <strong>CPM:</strong> <span class="{get_cpm_color(option['cpm'])}">{option['cpm']:.2f}</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info(f"No {label} redemption options found matching your filters.")
                else:
                    st.info(f"No {label} redemption options found in this section.")
    
    with tab3:
        st.header("📊 Analysis & Insights")
        
        if st.session_state.results:
            results = st.session_state.results
            
            # Comparison chart
            st.subheader("📈 Comparison Chart")
            chart = create_comparison_chart(results)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            # Map view
            st.subheader("🗺️ Map View")
            map_view = create_map_view(results)
            if map_view:
                folium_static(map_view)
            
            # Detailed analysis
            st.subheader("📋 Detailed Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CPM distribution
                all_options = []
                for category, options in results['top_options_by_category'].items():
                    # Exclude gift cards from analysis visuals
                    if category == 'gift_cards':
                        continue
                    for option in options:
                        all_options.append({
                            'Category': category.replace('_', ' ').title(),
                            'CPM': option['cpm'],
                            'Value': option['cash_value']
                        })
                
                if all_options:
                    df = pd.DataFrame(all_options)
                    fig = px.histogram(df, x='CPM', color='Category', 
                                     title='CPM Distribution by Category',
                                     nbins=20)
                    fig.update_layout(
                        template="plotly_dark",
                        font=dict(family="Poppins, sans-serif", color="#e5e7eb"),
                        paper_bgcolor="#0b0f15",
                        plot_bgcolor="#0b0f15",
                        transition_duration=500
                    )
                    fig.update_traces(marker_line_color='#1f2937', marker_line_width=1)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Value vs CPM scatter
                if all_options:
                    fig = px.scatter(df, x='CPM', y='Value', color='Category',
                                   animation_frame='Category', animation_group='Category',
                                   title='Value vs CPM Scatter Plot',
                                   hover_data=['Category'])
                    fig.update_layout(
                        template="plotly_dark",
                        font=dict(family="Poppins, sans-serif", color="#e5e7eb"),
                        paper_bgcolor="#0b0f15",
                        plot_bgcolor="#0b0f15",
                        transition_duration=500
                    )
                    try:
                        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
                        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 500
                    except Exception:
                        pass
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run a search first to see analysis and insights.")
    
    with tab4:
        st.header("💰 Savings Calculator")
        create_savings_calculator()
    
    with tab5:
        st.header("💬 User Feedback")
        st.subheader("Google Form")
        # Embed provided Google Form as an iframe (convert /edit to a responder view)
        embed_url = (
            "https://docs.google.com/forms/d/1p65ckXjGpL4y2N9MnRq82Tp_LN5Nr2qUCxffoRxm7Cs/viewform?embedded=true"
        )
        st.components.v1.html(
            f"""
            <iframe src='{embed_url}' width='100%' height='1200' frameborder='0' marginheight='0' marginwidth='0'>
            Loading…
            </iframe>
            """,
            height=1220,
            scrolling=True,
        )

if __name__ == "__main__":
    main() 

