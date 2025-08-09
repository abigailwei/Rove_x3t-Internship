import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import sys
import os

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

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2980b9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .option-card {
        background: black;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .cpm-high {
        color: #27ae60;
        font-weight: bold;
    }
    
    .cpm-medium {
        color: #f39c12;
        font-weight: bold;
    }
    
    .cpm-low {
        color: #e74c3c;
        font-weight: bold;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2980b9 0%, #1f4e79 100%);
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
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Home"
    
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
    
    fig = px.bar(df, x='Option', y='CPM', color='Category',
                 title='Redemption Options Comparison by CPM',
                 color_discrete_map={
                     'Flights': '#3498db',
                     'Hotels': '#e74c3c', 
                     'Gift Cards': '#2ecc71'
                 })
    
    fig.update_layout(
        xaxis_title="Redemption Option",
        yaxis_title="Cents Per Mile (CPM)",
        height=500
    )
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "Search", "📊 Analysis", "💰 Calculator", "💬 Feedback"])
    
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
            
            submitted = st.form_submit_button("🔍 Search Redemption Options")
            
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
                        
                    except Exception as e:
                        st.error(f"Error during analysis: {e}")
        
        # Display results
        if st.session_state.results:
            results = st.session_state.results
            
            # Summary metrics
            st.subheader("📊 Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Options", results['detailed_analysis']['total_options_analyzed'])
            
            with col2:
                st.metric("Flight Options", results['detailed_analysis']['flight_options'])
            
            with col3:
                st.metric("Hotel Options", results['detailed_analysis']['hotel_options'])
            
            with col4:
                st.metric("Gift Card Options", results['detailed_analysis']['gift_card_options'])
            
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
                if options:
                    st.subheader(f"{'🛫' if category == 'flights' else '🏨' if category == 'hotels' else '🎁'} Top {category.replace('_', ' ').title()} Options")
                    
                    for i, option in enumerate(options, 1):
                        if option['cpm'] >= min_cpm and option['miles_required'] <= max_miles:
                            st.markdown(f"""
                            <div class="option-card">
                                <h4>{i}. {option['description']}</h4>
                                <p><strong>Value:</strong> ${option['cash_value']:,.2f} | 
                                <strong>Miles:</strong> {option['miles_required']:,} | 
                                <strong>CPM:</strong> <span class="{get_cpm_color(option['cpm'])}">{option['cpm']:.2f}</span></p>
                            </div>
                            """, unsafe_allow_html=True)
    
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
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Value vs CPM scatter
                if all_options:
                    fig = px.scatter(df, x='CPM', y='Value', color='Category',
                                   title='Value vs CPM Scatter Plot',
                                   hover_data=['Category'])
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run a search first to see analysis and insights.")
    
    with tab4:
        st.header("💰 Savings Calculator")
        create_savings_calculator()
    
    with tab5:
        st.header("💬 User Feedback")
        
        # Feedback form
        with st.form("feedback_form"):
            st.subheader("Share Your Experience")
            
            rating = st.slider("How would you rate this tool?", 1, 5, 3)
            feedback_type = st.selectbox("Feedback Type", ["General", "Bug Report", "Feature Request", "Improvement"])
            feedback_text = st.text_area("Your Feedback", placeholder="Tell us what you think...")
            
            submitted_feedback = st.form_submit_button("Submit Feedback")
            
            if submitted_feedback and feedback_text:
                feedback = {
                    'timestamp': datetime.now(),
                    'rating': rating,
                    'type': feedback_type,
                    'text': feedback_text
                }
                st.session_state.user_feedback.append(feedback)
                st.success("Thank you for your feedback!")
        
        # Display feedback
        if st.session_state.user_feedback:
            st.subheader("Recent Feedback")
            for feedback in st.session_state.user_feedback[-5:]:  # Show last 5
                st.markdown(f"""
                <div class="option-card">
                    <p><strong>Rating:</strong> {'⭐' * feedback['rating']}</p>
                    <p><strong>Type:</strong> {feedback['type']}</p>
                    <p><strong>Feedback:</strong> {feedback['text']}</p>
                    <p><small>{feedback['timestamp'].strftime('%Y-%m-%d %H:%M')}</small></p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":

    main() 









