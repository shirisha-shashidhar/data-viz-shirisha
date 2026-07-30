# pages/03_demand.py — YOUR new page (BBD squiggle level 3: demand story)
import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, sidebar_filters

# ─────────────────────────────────────────────────────────────────────────────
# Load data + shared sidebar
# One call to sidebar_filters gives you the SAME sidebar as pages 1 and 2 —
# and the filter choices carried over from them, for free.
# Then add a question title + caption.
# ─────────────────────────────────────────────────────────────────────────────
df, p95 = load_data()
filtered = sidebar_filters(df, p95)  # SAME sidebar — choices carried over from pages 1 & 2

st.title('Where is guest demand strongest?')
st.caption('BBD squiggle: from the neighbourhood story to which room type draws the most demand')

# ─────────────────────────────────────────────────────────────────────────────
# A persisted widget of your own
# e.g. a radio or selectbox to focus on one room type, key='sel_room'
#   - initialise the key in session_state once
#   - keep it alive: st.session_state.sel_room = st.session_state.sel_room
#   - GUARD: if the saved value was filtered out, fall back to a valid option
#     BEFORE creating the widget
# TEST: pick a value, visit page 1, change a filter, come back — your choice
# must still be selected (or gracefully replaced if filtered out).
# ─────────────────────────────────────────────────────────────────────────────
if 'sel_room' not in st.session_state:
    st.session_state.sel_room = sorted(filtered['room_type'].unique())[0]
st.session_state.sel_room = st.session_state.sel_room     # keep alive across pages

rooms_avail = sorted(filtered['room_type'].unique())
if st.session_state.sel_room not in rooms_avail:           # guard: filters may have
    st.session_state.sel_room = rooms_avail[0]              # removed the saved choice

st.radio('Focus on a room type', rooms_avail, key='sel_room', horizontal=True)
room = st.session_state.sel_room
room_df = filtered[filtered['room_type'] == room]

# ─────────────────────────────────────────────────────────────────────────────
# KPI row (st.columns(3)) about the focused selection
# e.g. listings, median reviews/month vs filtered market, median price
# 5-second test: the metrics alone should answer the page's question
# ─────────────────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric('Listings', f'{len(room_df):,}')
k2.metric('Median Reviews/Month', f"{room_df['reviews_per_month'].median():.1f}",
          f"{room_df['reviews_per_month'].median() - filtered['reviews_per_month'].median():+.1f} "
          'vs filtered market')
k3.metric('Median Price', f"£{room_df['price'].median():.0f}/night")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# One chart — demand story
# Suggestion: px.scatter of price vs reviews_per_month (reviews as a demand
# proxy), highlight column for your focused selection.
# BBD REQUIREMENTS:
#   - Name the colour type in a comment (highlight: blue vs grey)
#   - No red-green, no pies, no packed bubbles
# SWD REQUIREMENTS:
#   - White background, Arial font, insight title, use_container_width=True
# px REQUIREMENT:
#   - Start from px, highlight column + color_discrete_map — no go.Figure()
# ─────────────────────────────────────────────────────────────────────────────
plot_df = filtered.copy()
plot_df['highlight'] = plot_df['room_type'].apply(
    lambda r: room if r == room else 'Other room types')

# BBD HIGHLIGHT colour: blue for the focused room type, grey for the rest
# BBD CVD: blue vs grey — no red-green combination
fig = px.scatter(plot_df, x='reviews_per_month', y='price', color='highlight',
                 color_discrete_map={room: '#2E75B6', 'Other room types': '#AAAAAA'},
                 category_orders={'highlight': ['Other room types', room]},
                 labels={'reviews_per_month': 'Reviews per Month (demand proxy)',
                         'price': 'Nightly Price (£)'},
                 title=f'{room} listings show the strongest demand signal among London Airbnbs')
fig.update_traces(marker=dict(size=7, opacity=0.7, line=dict(width=0)))
fig.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                  font=dict(family='Arial', size=12), showlegend=False,
                  xaxis=dict(gridcolor='#EEEEEE'), yaxis=dict(gridcolor='#EEEEEE'))
st.plotly_chart(fig, width='stretch')

# TEST for graders: pick a room type, switch to page 1, change a filter,
# come back — both the filters AND this selection must be where you left them.
