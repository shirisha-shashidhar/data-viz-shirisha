
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
# @st.cache_data: Streamlit reruns the entire script on every widget interaction.
# Without caching, the CSV is read from disk on every interaction — slow and wasteful.
# cache_data stores the result after the first run and reuses it until the file changes.
@st.cache_data
def load_data():
    # .resolve() turns __file__ into an absolute path first — without it,
    # running via a relative command (e.g. `streamlit run lecture10_exercise.py`
    # from inside week10/) leaves __file__ relative, and .parent.parent can't
    # climb up two real directories, silently collapsing to just 'data/...'
    path = Path(__file__).resolve().parent.parent / 'data' / 'co2_emissions.csv'
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-01-01')
    return df

df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")

# ── TASK 1: Sidebar with 5 widgets ────────────────────────────────────────────
#   a) st.selectbox for Region (with 'All')
#   b) st.multiselect for Countries (updates based on region — chained)
#   c) st.date_input for date range (two-handle; convert years to Jan-1 dates)
#   d) st.radio for Metric: "Total CO2 (Mt)" vs "CO2 per capita"
#   e) st.checkbox labelled "Show only top emitter highlighted"
#
# Guards:
#   - empty countries → st.warning + st.stop()
#   - incomplete date_input → st.warning + st.stop()
# Convert date_input result to pd.Timestamp before filtering.
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    # a) Region — chained filter that narrows the country list below
    regions = ['All'] + sorted(df['Region'].unique())
    selected_region = st.selectbox("Region", regions)

    if selected_region == 'All':
        country_options = sorted(df['Country'].unique())
    else:
        country_options = sorted(df[df['Region'] == selected_region]['Country'].unique())

    # b) Countries — options depend on the region chosen above (chained filter)
    selected_countries = st.multiselect(
        "Countries", country_options, default=country_options[:5]
    )

    # c) Date range — two-handle calendar picker
    date_range = st.date_input(
        "Date range",
        value=(datetime.date(2005, 1, 1), datetime.date(2020, 1, 1)),
        min_value=datetime.date(int(df['Year'].min()), 1, 1),
        max_value=datetime.date(int(df['Year'].max()), 1, 1),
        format="YYYY-MM-DD"
    )

    st.divider()

    # d) Metric — 2 mutually exclusive options; radio is clearer than selectbox here
    metric = st.radio("Metric", ["Total CO2 (Mt)", "CO2 per capita"])

    # e) Highlight toggle
    highlight_top = st.checkbox("Show only top emitter highlighted")

# Guard: user may have only picked a start date, not an end date yet
if len(date_range) != 2:
    st.warning("👆 Select a start AND end date.")
    st.stop()

# Guard: nothing sensible to show if no countries are selected
if not selected_countries:
    st.warning("👆 Select at least one country.")
    st.stop()

# Always convert date_input's datetime.date output to pd.Timestamp before
# comparing against the Date column (pandas stores that as datetime64)
start_ts, end_ts = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])

filtered = df[
    df['Country'].isin(selected_countries) &
    (df['Date'] >= start_ts) &
    (df['Date'] <= end_ts)
]

if filtered.empty:
    st.warning("No data in this date range for the selected countries.")
    st.stop()

y_col = 'CO2_Mt' if metric == "Total CO2 (Mt)" else 'CO2_per_capita'
y_label = 'CO2 Emissions (Mt)' if y_col == 'CO2_Mt' else 'CO2 per Capita (t)'


# ── TASK 2: Filter summary caption ────────────────────────────────────────────
# Show: "X countries | Region | Date range | Metric"
# BBD rule: always show users how many records match current filters
# ─────────────────────────────────────────────────────────────────────────────
st.caption(
    f"{len(selected_countries)} countries | {selected_region} | "
    f"{date_range[0].strftime('%d %b %Y')} – {date_range[1].strftime('%d %b %Y')} | "
    f"{metric} | {len(filtered)} data points"
)


# ── EXTENSION: KPI row above the charts ───────────────────────────────────────
#   - Total CO2 in last year of selected range (sum across selected countries)
#   - % change from first to last year
#   - Country with highest emissions in last year
# BBD: big numbers at the top, readable in 5 seconds
# ─────────────────────────────────────────────────────────────────────────────
first_year, last_year = filtered['Year'].min(), filtered['Year'].max()
total_last = filtered[filtered['Year'] == last_year][y_col].sum()
total_first = filtered[filtered['Year'] == first_year][y_col].sum()
pct_change = ((total_last - total_first) / total_first * 100) if total_first else 0
top_emitter_last = (
    filtered[filtered['Year'] == last_year]
    .sort_values(y_col, ascending=False).iloc[0]['Country']
)

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(f"Total {metric} ({last_year})", f"{total_last:,.1f}")
kpi2.metric(f"Change since {first_year}", f"{pct_change:+.1f}%")
kpi3.metric(f"Top emitter ({last_year})", top_emitter_last)

st.divider()


# ── TASK 3: Two charts reacting to ALL filters ────────────────────────────────
#   Left: line chart — selected metric over time, one line per country
#         If "Show only top emitter highlighted" checkbox is on:
#           - grey all lines except the highest emitter in the date range
#           - label that country at the end of its line (SWD grey-and-highlight)
#   Right: bar chart — ranking for the last year in selected date range
#
# BBD colour requirement: name the colour type in a comment next to each chart
# SWD requirements: white background, insight title, width='stretch'
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    if highlight_top:
        # Highlight colour: one accent colour for the single series that needs
        # to stand out (BBD "highlight" type), everything else pushed to grey
        # so the eye goes straight to the top emitter (SWD grey-and-highlight)
        top_country = (
            filtered.groupby('Country')[y_col].max()
            .sort_values(ascending=False).index[0]
        )

        fig1 = go.Figure()
        for country in filtered['Country'].unique():
            country_data = filtered[filtered['Country'] == country].sort_values('Date')
            is_top = country == top_country
            fig1.add_trace(go.Scatter(
                x=country_data['Date'], y=country_data[y_col],
                mode='lines+text' if is_top else 'lines',
                name=country,
                line=dict(color='#E63946' if is_top else '#D9D9D9',
                          width=3 if is_top else 1.5),
                text=[country if i == len(country_data) - 1 else ''
                      for i in range(len(country_data))],
                textposition='middle right',
                showlegend=False,
            ))
        fig1.update_layout(
            title=f'{metric} over time — {top_country} highlighted',
            plot_bgcolor='white', paper_bgcolor='white', font=dict(family='Arial'),
            yaxis_title=y_label, xaxis_title='',
        )
    else:
        # Categorical colour — one unordered colour per country
        fig1 = px.line(filtered, x='Date', y=y_col, color='Country',
                        labels={y_col: y_label, 'Date': ''},
                        title=f'{metric} over time')
        fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                            font=dict(family='Arial'))
    st.plotly_chart(fig1, width='stretch')

with col_right:
    latest = filtered[filtered['Year'] == last_year].sort_values(y_col)

    # Sequential blue — bars are ordered by value, not unordered categories
    fig2 = px.bar(latest, x=y_col, y='Country', orientation='h',
                  color=y_col, color_continuous_scale='Blues',
                  labels={y_col: y_label, 'Country': ''},
                  title=f'{last_year} ranking')
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        font=dict(family='Arial'), coloraxis_showscale=False,
                        xaxis=dict(range=[0, latest[y_col].max() * 1.15]))
    fig2.update_traces(marker_line_width=0)
    st.plotly_chart(fig2, width='stretch')
