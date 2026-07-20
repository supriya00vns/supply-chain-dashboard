import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page Configuration
st.set_page_config(
    page_title="Nassau Candy - Factory & Profitability Dashboard",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== FACTORY DATA ====================

FACTORY_COORDINATES = {
    "Lot's O' Nuts": {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's": {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack": {"lat": 48.11914, "lon": -96.18115},
    "Secret Factory": {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory": {"lat": 35.1175, "lon": -89.971107}
}

PRODUCT_FACTORY_MAP = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar - Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

# Factory color mapping
FACTORY_COLORS = {
    "Lot's O' Nuts": "#FF6B6B",
    "Wicked Choccy's": "#4ECDC4",
    "Sugar Shack": "#45B7D1",
    "Secret Factory": "#96CEB4",
    "The Other Factory": "#FFEAA7"
}

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #8B4513;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5D4037;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #FFF8F0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #8B4513;
    }
    .factory-card {
        background-color: #F0F7FF;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #CBD5E1;
    }
    .warning-card {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F59E0B;
    }
    .danger-card {
        background-color: #FEE2E2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #EF4444;
    }
    .success-card {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">🏭 Nassau Candy - Factory & Profitability Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Wonka Product Line Analysis | Factory Performance & Supply Chain Insights</p>', unsafe_allow_html=True)
st.markdown("---")

# ==================== DATA LOADING & CLEANING ====================

@st.cache_data
def load_and_clean_data(uploaded_file):
    """Load and clean the Nassau Candy dataset"""
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.warning("Please upload the CSV file to begin analysis")
        return None
    
    # Data Cleaning
    df = df.copy()
    
    # Remove zero sales or invalid records
    df = df[df['Sales'] > 0]
    df = df[df['Gross Profit'] > 0]
    
    # Handle missing values
    df['Units'] = df['Units'].fillna(df['Units'].median())
    
    # Calculate additional metrics
    df['Gross Margin (%)'] = (df['Gross Profit'] / df['Sales']) * 100
    df['Profit per Unit'] = df['Gross Profit'] / df['Units']
    df['Cost per Unit'] = df['Cost'] / df['Units']
    
    # Date handling - DD-MM-YYYY format
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y')
    df['Month'] = df['Order Date'].dt.month
    df['Year'] = df['Order Date'].dt.year
    df['Quarter'] = df['Order Date'].dt.quarter
    
    # Product name cleaning - extract base product
    df['Product Base'] = df['Product Name'].str.replace('Wonka Bar - ', '').str.strip()
    
    # Add Factory mapping
    df['Factory'] = df['Product Name'].map(PRODUCT_FACTORY_MAP)
    df['Factory'] = df['Factory'].fillna('Unknown')
    
    # Add Factory Coordinates
    df['Factory_Lat'] = df['Factory'].map(lambda x: FACTORY_COORDINATES.get(x, {}).get('lat', None))
    df['Factory_Lon'] = df['Factory'].map(lambda x: FACTORY_COORDINATES.get(x, {}).get('lon', None))
    
    return df

# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("📂 Data Source")
    
    uploaded_file = st.file_uploader("Upload Nassau Candy CSV", type=['csv'])
    
    if uploaded_file is None:
        st.info("Please upload the Nassau Candy Distributor CSV file")
        st.stop()
    
    st.markdown("---")
    st.header("🔍 Filters")
    
    # Load data
    df = load_and_clean_data(uploaded_file)
    
    if df is None:
        st.stop()
    
    # Date Range Filter
    if 'Order Date' in df.columns:
        min_date = df['Order Date'].min().date()
        max_date = df['Order Date'].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            mask = (df['Order Date'] >= pd.to_datetime(date_range[0])) & \
                   (df['Order Date'] <= pd.to_datetime(date_range[1]))
            df = df[mask]
    
    # Factory Filter
    factories = ['All'] + sorted(df['Factory'].unique().tolist())
    selected_factory = st.selectbox("Factory", factories)
    if selected_factory != 'All':
        df = df[df['Factory'] == selected_factory]
    
    # Division Filter
    divisions = ['All'] + sorted(df['Division'].unique().tolist())
    selected_division = st.selectbox("Division", divisions)
    if selected_division != 'All':
        df = df[df['Division'] == selected_division]
    
    # Product Filter
    products = ['All'] + sorted(df['Product Base'].unique().tolist())
    selected_product = st.selectbox("Product", products)
    if selected_product != 'All':
        df = df[df['Product Base'] == selected_product]
    
    # Margin Threshold
    margin_threshold = st.slider(
        "Minimum Margin Threshold (%)",
        min_value=0,
        max_value=100,
        value=30,
        step=5
    )
    
    st.markdown("---")
    st.caption(f"Showing {len(df)} records")

# ==================== TOP KPIs ====================

st.subheader("📈 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_revenue = df['Sales'].sum()
    st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")

with col2:
    total_profit = df['Gross Profit'].sum()
    st.metric("📈 Total Profit", f"${total_profit:,.2f}")

with col3:
    avg_margin = df['Gross Margin (%)'].mean()
    st.metric("🎯 Avg Gross Margin", f"{avg_margin:.1f}%")

with col4:
    total_units = df['Units'].sum()
    st.metric("📦 Total Units", f"{total_units:,.0f}")

with col5:
    profit_per_unit = total_profit / total_units if total_units > 0 else 0
    st.metric("💵 Profit/Unit", f"${profit_per_unit:.2f}")

st.markdown("---")

# ==================== TABS ====================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏭 Factory Overview",
    "📊 Product Profitability",
    "🏢 Division Performance",
    "📉 Cost vs Margin",
    "🎯 Profit Concentration",
    "📍 Geographic Analysis"
])

# ==================== TAB 1: FACTORY OVERVIEW ====================

with tab1:
    st.subheader("🏭 Factory Performance Overview")
    
    # Factory metrics
    factory_metrics = df.groupby('Factory').agg({
        'Sales': 'sum',
        'Gross Profit': 'sum',
        'Units': 'sum',
        'Gross Margin (%)': 'mean',
        'Profit per Unit': 'mean'
    }).reset_index()
    
    factory_metrics['Revenue Share (%)'] = (factory_metrics['Sales'] / factory_metrics['Sales'].sum()) * 100
    factory_metrics['Profit Share (%)'] = (factory_metrics['Gross Profit'] / factory_metrics['Gross Profit'].sum()) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Factory Performance Chart
        fig = make_subplots()
        fig.add_trace(go.Bar(
            name='Revenue',
            x=factory_metrics['Factory'],
            y=factory_metrics['Sales'],
            marker_color='#3B82F6',
            text=factory_metrics['Revenue Share (%)'].round(1).astype(str) + '%',
            textposition='outside'
        ))
        fig.add_trace(go.Bar(
            name='Profit',
            x=factory_metrics['Factory'],
            y=factory_metrics['Gross Profit'],
            marker_color='#10B981',
            text=factory_metrics['Profit Share (%)'].round(1).astype(str) + '%',
            textposition='outside'
        ))
        fig.update_layout(title="Revenue vs Profit by Factory",
                         height=400,
                         barmode='group',
                         yaxis_title="Amount ($)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Factory Margin Comparison
        fig = px.bar(factory_metrics,
                     x='Factory',
                     y='Gross Margin (%)',
                     color='Gross Margin (%)',
                     color_continuous_scale='RdYlGn',
                     title="Average Gross Margin by Factory",
                     text_auto='.1f')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Factory Details Table
    st.subheader("📊 Factory Performance Details")
    display_df = factory_metrics.copy()
    display_df['Sales'] = display_df['Sales'].apply(lambda x: f"${x:,.0f}")
    display_df['Gross Profit'] = display_df['Gross Profit'].apply(lambda x: f"${x:,.0f}")
    display_df['Gross Margin (%)'] = display_df['Gross Margin (%)'].round(1).astype(str) + '%'
    display_df['Profit per Unit'] = display_df['Profit per Unit'].apply(lambda x: f"${x:.2f}")
    st.dataframe(display_df, use_container_width=True)
    
    # Factory Product Mix
    st.subheader("📦 Factory Product Mix")
    factory_product = df.groupby(['Factory', 'Product Base']).agg({
        'Sales': 'sum'
    }).reset_index()
    
    fig = px.treemap(factory_product,
                     path=['Factory', 'Product Base'],
                     values='Sales',
                     color='Sales',
                     color_continuous_scale='Blues',
                     title="Product Sales Distribution by Factory")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 2: PRODUCT PROFITABILITY ====================

with tab2:
    st.subheader("📊 Product Profitability Overview")
    
    # Product Metrics
    product_metrics = df.groupby('Product Base').agg({
        'Sales': 'sum',
        'Gross Profit': 'sum',
        'Units': 'sum',
        'Gross Margin (%)': 'mean',
        'Profit per Unit': 'mean',
        'Cost': 'sum',
        'Factory': 'first'
    }).reset_index()
    
    product_metrics['Revenue Contribution (%)'] = (product_metrics['Sales'] / product_metrics['Sales'].sum()) * 100
    product_metrics['Profit Contribution (%)'] = (product_metrics['Gross Profit'] / product_metrics['Gross Profit'].sum()) * 100
    product_metrics['Avg Cost per Unit'] = product_metrics['Cost'] / product_metrics['Units']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Products by Profit with Factory Color
        top_profit = product_metrics.nlargest(10, 'Gross Profit')
        fig = px.bar(top_profit, 
                     x='Product Base', 
                     y='Gross Profit',
                     color='Factory',
                     color_discrete_map=FACTORY_COLORS,
                     title="Top 10 Products by Gross Profit",
                     labels={'Gross Profit': 'Gross Profit ($)', 'Product Base': 'Product'},
                     text_auto='.2s')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top Products by Margin
        top_margin = product_metrics.nlargest(10, 'Gross Margin (%)')
        fig = px.bar(top_margin, 
                     x='Product Base', 
                     y='Gross Margin (%)',
                     color='Factory',
                     color_discrete_map=FACTORY_COLORS,
                     title="Top 10 Products by Gross Margin",
                     labels={'Gross Margin (%)': 'Gross Margin (%)', 'Product Base': 'Product'},
                     text_auto='.1f')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Product Classification Matrix
    st.subheader("📊 Product Classification Matrix")
    
    product_metrics['Classification'] = 'Balanced'
    product_metrics.loc[(product_metrics['Sales'] > product_metrics['Sales'].median()) & 
                       (product_metrics['Gross Margin (%)'] < margin_threshold), 'Classification'] = 'High Sales, Low Margin ⚠️'
    product_metrics.loc[(product_metrics['Sales'] < product_metrics['Sales'].median()) & 
                       (product_metrics['Gross Margin (%)'] < margin_threshold), 'Classification'] = 'Low Sales, Low Margin ❌'
    product_metrics.loc[(product_metrics['Sales'] > product_metrics['Sales'].median()) & 
                       (product_metrics['Gross Margin (%)'] > margin_threshold), 'Classification'] = 'High Sales, High Margin ✅'
    product_metrics.loc[(product_metrics['Sales'] < product_metrics['Sales'].median()) & 
                       (product_metrics['Gross Margin (%)'] > margin_threshold), 'Classification'] = 'Low Sales, High Margin 📈'
    
    classification_counts = product_metrics['Classification'].value_counts()
    fig = px.pie(values=classification_counts.values, 
                 names=classification_counts.index,
                 title="Product Classification Distribution",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk products table
    st.subheader("⚠️ Margin Risk Products")
    risk_products = product_metrics[product_metrics['Gross Margin (%)'] < margin_threshold].nlargest(20, 'Sales')
    if not risk_products.empty:
        st.dataframe(
            risk_products[['Product Base', 'Factory', 'Sales', 'Gross Profit', 'Gross Margin (%)', 'Classification']],
            use_container_width=True
        )
        st.warning(f"⚠️ {len(risk_products)} products are below the {margin_threshold}% margin threshold")
    else:
        st.success("✅ No products below the margin threshold!")

# ==================== TAB 3: DIVISION PERFORMANCE ====================

with tab3:
    st.subheader("🏢 Division Performance Dashboard")
    
    division_metrics = df.groupby('Division').agg({
        'Sales': 'sum',
        'Gross Profit': 'sum',
        'Units': 'sum',
        'Gross Margin (%)': 'mean',
        'Profit per Unit': 'mean'
    }).reset_index()
    
    division_metrics['Revenue Share (%)'] = (division_metrics['Sales'] / division_metrics['Sales'].sum()) * 100
    division_metrics['Profit Share (%)'] = (division_metrics['Gross Profit'] / division_metrics['Gross Profit'].sum()) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = make_subplots()
        fig.add_trace(go.Bar(
            name='Revenue',
            x=division_metrics['Division'],
            y=division_metrics['Sales'],
            marker_color='#3B82F6',
            text=division_metrics['Revenue Share (%)'].round(1).astype(str) + '%',
            textposition='outside'
        ))
        fig.add_trace(go.Bar(
            name='Profit',
            x=division_metrics['Division'],
            y=division_metrics['Gross Profit'],
            marker_color='#10B981',
            text=division_metrics['Profit Share (%)'].round(1).astype(str) + '%',
            textposition='outside'
        ))
        fig.update_layout(title="Revenue vs Profit by Division",
                         height=400,
                         barmode='group',
                         yaxis_title="Amount ($)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.box(df, x='Division', y='Gross Margin (%)', 
                     title="Gross Margin Distribution by Division",
                     color='Division',
                     points="all")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(
        division_metrics.style.format({
            'Sales': '${:,.0f}',
            'Gross Profit': '${:,.0f}',
            'Gross Margin (%)': '{:.1f}%',
            'Profit per Unit': '${:.2f}'
        }),
        use_container_width=True
    )

# ==================== TAB 4: COST VS MARGIN ====================

with tab4:
    st.subheader("📉 Cost vs Margin Diagnostics")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        df['Margin Category'] = pd.cut(df['Gross Margin (%)'], 
                                       bins=[0, 20, 40, 100], 
                                       labels=['Low Margin', 'Medium Margin', 'High Margin'])
        
        fig = px.scatter(df, 
                        x='Cost', 
                        y='Sales',
                        color='Factory',
                        size='Gross Profit',
                        hover_data=['Product Name', 'Division', 'Gross Margin (%)'],
                        title="Cost vs Sales with Factory Indicators",
                        labels={'Cost': 'Cost ($)', 'Sales': 'Sales ($)'},
                        color_discrete_map=FACTORY_COLORS)
        
        fig.add_trace(go.Scatter(
            x=[df['Cost'].min(), df['Cost'].max()],
            y=[df['Cost'].min(), df['Cost'].max()],
            mode='lines',
            name='Break-even Line',
            line=dict(dash='dash', color='red')
        ))
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Margin Risk Flags")
        
        df['Risk Level'] = 'Low Risk'
        df.loc[(df['Gross Margin (%)'] < 20) & (df['Sales'] > df['Sales'].mean()), 'Risk Level'] = 'High Risk 🔴'
        df.loc[(df['Gross Margin (%)'] < 20) & (df['Sales'] <= df['Sales'].mean()), 'Risk Level'] = 'Medium Risk 🟡'
        df.loc[(df['Gross Margin (%)'] >= 20) & (df['Sales'] > df['Sales'].mean()), 'Risk Level'] = 'Low Risk 🟢'
        df.loc[(df['Gross Margin (%)'] >= 20) & (df['Sales'] <= df['Sales'].mean()), 'Risk Level'] = 'Monitor 📊'
        
        risk_counts = df['Risk Level'].value_counts()
        fig = px.pie(values=risk_counts.values, 
                     names=risk_counts.index,
                     title="Risk Level Distribution")
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: PROFIT CONCENTRATION ====================

with tab5:
    st.subheader("🎯 Profit Concentration Analysis (Pareto)")
    
    product_metrics = df.groupby('Product Base').agg({
        'Sales': 'sum',
        'Gross Profit': 'sum',
        'Factory': 'first'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        sorted_products = product_metrics.sort_values('Sales', ascending=False)
        sorted_products['Cumulative Revenue'] = sorted_products['Sales'].cumsum()
        sorted_products['Cumulative Revenue %'] = (sorted_products['Cumulative Revenue'] / sorted_products['Sales'].sum()) * 100
        sorted_products['Product %'] = (np.arange(len(sorted_products)) + 1) / len(sorted_products) * 100
        
        pct_products_80_revenue = sorted_products[sorted_products['Cumulative Revenue %'] <= 80].shape[0] / len(sorted_products) * 100
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=sorted_products['Product %'],
            y=sorted_products['Cumulative Revenue %'],
            name='Cumulative Revenue',
            line=dict(color='#3B82F6', width=3)
        ), secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=[0, 100],
            y=[80, 80],
            mode='lines',
            name='80% Target',
            line=dict(dash='dash', color='red')
        ), secondary_y=False)
        
        fig.update_layout(
            title=f"Revenue Pareto: {pct_products_80_revenue:.1f}% of products contribute 80% of revenue",
            xaxis_title="Products (%)",
            height=400
        )
        fig.update_yaxes(title_text="Cumulative Revenue (%)", secondary_y=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("Revenue Concentration", f"{pct_products_80_revenue:.1f}%", 
                 delta="Products contributing to 80% revenue")
    
    with col2:
        sorted_profit = product_metrics.sort_values('Gross Profit', ascending=False)
        sorted_profit['Cumulative Profit'] = sorted_profit['Gross Profit'].cumsum()
        sorted_profit['Cumulative Profit %'] = (sorted_profit['Cumulative Profit'] / sorted_profit['Gross Profit'].sum()) * 100
        sorted_profit['Product %'] = (np.arange(len(sorted_profit)) + 1) / len(sorted_profit) * 100
        
        pct_products_80_profit = sorted_profit[sorted_profit['Cumulative Profit %'] <= 80].shape[0] / len(sorted_profit) * 100
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            x=sorted_profit['Product %'],
            y=sorted_profit['Cumulative Profit %'],
            name='Cumulative Profit',
            line=dict(color='#10B981', width=3)
        ), secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=[0, 100],
            y=[80, 80],
            mode='lines',
            name='80% Target',
            line=dict(dash='dash', color='red')
        ), secondary_y=False)
        
        fig.update_layout(
            title=f"Profit Pareto: {pct_products_80_profit:.1f}% of products contribute 80% of profit",
            xaxis_title="Products (%)",
            height=400
        )
        fig.update_yaxes(title_text="Cumulative Profit (%)", secondary_y=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("Profit Concentration", f"{pct_products_80_profit:.1f}%",
                 delta="Products contributing to 80% profit")

# ==================== TAB 6: GEOGRAPHIC ANALYSIS ====================

with tab6:
    st.subheader("📍 Geographic Factory Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Factory Map
        st.subheader("🗺️ Factory Locations")
        
        factory_locations = df.groupby('Factory').agg({
            'Sales': 'sum',
            'Gross Profit': 'sum',
            'Factory_Lat': 'first',
            'Factory_Lon': 'first'
        }).reset_index()
        
        fig = px.scatter_mapbox(
            factory_locations,
            lat='Factory_Lat',
            lon='Factory_Lon',
            size='Sales',
            color='Gross Profit',
            hover_name='Factory',
            hover_data={
                'Sales': ':$,.0f',
                'Gross Profit': ':$,.0f'
            },
            title='Factory Locations with Sales Performance',
            color_continuous_scale='RdYlGn',
            size_max=50,
            zoom=3,
            mapbox_style='open-street-map',
            height=500
        )
        
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Factory Performance Summary
        st.subheader("🏭 Factory Performance Summary")
        
        for factory in factory_locations.iterrows():
            row = factory[1]
            color = FACTORY_COLORS.get(row['Factory'], '#808080')
            st.markdown(f"""
            <div class="factory-card" style="border-left: 4px solid {color};">
                <b>{row['Factory']}</b><br>
                Revenue: ${row['Sales']:,.0f}<br>
                Profit: ${row['Gross Profit']:,.0f}
            </div>
            <br>
            """, unsafe_allow_html=True)
    
    # Product Flow Map
    st.subheader("🚚 Product Flow by Factory")
    
    product_by_factory = df.groupby(['Factory', 'Region']).agg({
        'Sales': 'sum'
    }).reset_index()
    
    fig = px.parallel_categories(
        product_by_factory,
        dimensions=['Factory', 'Region'],
        color='Sales',
        color_continuous_scale='Blues',
        title="Product Flow: Factory → Region",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Factory by Product Mix
    st.subheader("📊 Factory Product Mix")
    
    factory_product_mix = df.groupby(['Factory', 'Product Base']).agg({
        'Sales': 'sum',
        'Gross Margin (%)': 'mean'
    }).reset_index()
    
    fig = px.sunburst(
        factory_product_mix,
        path=['Factory', 'Product Base'],
        values='Sales',
        color='Gross Margin (%)',
        color_continuous_scale='RdYlGn',
        title="Product Mix by Factory (Sunburst)",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# ==================== EXECUTIVE SUMMARY ====================

st.markdown("---")
st.subheader("📋 Executive Summary Dashboard")

product_metrics = df.groupby('Product Base').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum',
    'Gross Margin (%)': 'mean',
    'Factory': 'first'
}).reset_index()

col1, col2 = st.columns(2)

with col1:
    best_factory = df.groupby('Factory')['Gross Margin (%)'].mean().idxmax()
    best_factory_margin = df.groupby('Factory')['Gross Margin (%)'].mean().max()
    
    st.markdown(f"""
    <div class="metric-card">
        <b>📊 Key Findings:</b><br>
        • Best Factory: {best_factory} ({best_factory_margin:.1f}% margin)<br>
        • Top Product: {product_metrics.loc[product_metrics['Sales'].idxmax(), 'Product Base']}<br>
        • Best Margin Product: {product_metrics.loc[product_metrics['Gross Margin (%)'].idxmax(), 'Product Base']} ({product_metrics['Gross Margin (%)'].max():.1f}%)<br>
        • Total Revenue: ${total_revenue:,.2f}<br>
        • Total Profit: ${total_profit:,.2f}<br>
        • Average Margin: {avg_margin:.1f}%
    </div>
    """, unsafe_allow_html=True)

with col2:
    high_risk_count = len(df[df['Risk Level'] == 'High Risk 🔴'])
    risk_products = product_metrics[product_metrics['Gross Margin (%)'] < margin_threshold]
    
    st.markdown(f"""
    <div class="{'danger-card' if high_risk_count > 0 else 'success-card'}">
        <b>⚠️ Risk Summary:</b><br>
        • High Risk Products: {high_risk_count}<br>
        • Products below {margin_threshold}% margin: {len(risk_products)}<br>
        • Most Profitable Factory: {best_factory}<br>
        • Active Factories: {df['Factory'].nunique()}<br>
        • Total Products: {df['Product Base'].nunique()}
    </div>
    """, unsafe_allow_html=True)

# ==================== EXPORT ====================

st.subheader("📥 Export Data")

csv = df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data CSV",
    data=csv,
    file_name="nassau_candy_analysis.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.caption("🏭 Nassau Candy Distributor - Factory & Profitability Analytics Dashboard | Powered by Streamlit")