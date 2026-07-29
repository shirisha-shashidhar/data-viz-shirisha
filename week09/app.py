import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="World Happiness", page_icon="🌍", layout="wide")

df = pd.read_csv('../data/world_happiness_2023.csv')
df.columns = ['Country','Region','Score','GDP','Social_Support',
              'Life_Expectancy','Freedom','Generosity','Corruption']

with st.sidebar:
    st.header("Filters")
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)

filtered = df if selected_region == 'All' else df[df['Region'] == selected_region]

st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# ── KPI row — BBD: big numbers at the top, readable in 5 seconds ──────────
col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean() - df['Score'].mean():+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1, 'Score')['Country'].values[0])

st.divider()

# ── Two-column layout: rankings + score vs GDP ─────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rankings")
    top = filtered.nlargest(top_n, 'Score').sort_values('Score')

    fig1 = px.bar(top, x='Score', y='Country', orientation='h',
                  color_discrete_sequence=['#2E75B6'],
                  labels={'Score': 'Score (0–10)', 'Country': ''})
    fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        xaxis=dict(range=[0, 8.5]), font=dict(family='Arial', size=12),
                        margin=dict(l=10, r=10, t=5, b=10))
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, width='stretch')

with col_right:
    st.subheader("Score vs GDP")
    fig2 = px.scatter(filtered, x='GDP', y='Score', hover_name='Country',
                       color_discrete_sequence=['#E63946'])
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        font=dict(family='Arial', size=12),
                        margin=dict(l=10, r=10, t=5, b=10))
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ── STEP 6: Diverging colour scale — Generosity vs. world average ─────────
st.subheader("Generosity — Above vs. Below the World Average")
st.caption("0 = as generous as expected for a country's GDP; positive = more "
           "generous than expected; negative = less generous than expected.")

# pick the most extreme countries (furthest from 0 in either direction)
# so the diverging effect is actually visible
gen = filtered.reindex(
    filtered['Generosity'].abs().sort_values(ascending=False).index
).head(top_n).sort_values('Generosity')

fig3 = px.bar(
    gen, x='Generosity', y='Country', orientation='h',
    color='Generosity',
    color_continuous_scale='RdBu',     # diverging: red (below) <-> blue (above)
    color_continuous_midpoint=0,       # the meaningful midpoint
    labels={'Generosity': 'Generosity (relative to world average)', 'Country': ''}
)
fig3.update_layout(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Arial', size=12),
    coloraxis_showscale=False,
    margin=dict(l=10, r=20, t=10, b=10),
)
fig3.update_traces(marker_line_width=0)

# label the midpoint, per BBD's guidance on diverging scales
fig3.add_vline(x=0, line_width=1, line_dash='dash', line_color='#666666')
fig3.add_annotation(
    x=0, y=1.06, yref='paper', showarrow=False,
    text="World average", font=dict(size=11, color='#666666')
)
st.plotly_chart(fig3, width='stretch')

st.divider()
st.caption("Built with Streamlit + Plotly")
