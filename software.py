import streamlit as st
import math
import plotly.express as px
import pandas as pd

# --- Configuration and Styling ---
st.set_page_config(
    page_title="Attendance Lifeline Calculator",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .reportview-container .main {
        padding: 1rem;
    }
    h1 {
        color: #1E40AF;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563EB;
    }
    .result-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #F0F9FF;
        border-left: 5px solid #3B82F6;
        margin-top: 1rem;
    }
    .current-percent {
        font-size: 2.5rem;
        font-weight: 700;
        color: #10B981;
    }
</style>
""", unsafe_allow_html=True)

# --- Core Logic: Required Classes ---
def calculate_required_classes(c_att, c_total, p_req):
    current_percent = (c_att / c_total) * 100.0

    if current_percent >= p_req:
        return 0, current_percent, current_percent
    if p_req == 100:
        return -1, current_percent, 0.0

    R = p_req / 100.0
    numerator = (R * c_total) - c_att
    denominator = 1.0 - R
    x_float = numerator / denominator
    x_min = math.ceil(x_float)
    projected_percent = ((c_att + x_min) / (c_total + x_min)) * 100.0

    return x_min, current_percent, projected_percent

# --- New Feature: Missable Classes Calculator ---
def calculate_max_missable_classes(c_att, c_total, p_req, max_future_classes=50):
    R = p_req / 100.0
    for x in range(1, max_future_classes + 1):
        m = x - ((R * (c_total + x)) - c_att)
        m_int = math.floor(m)
        if m_int >= 0:
            return m_int, x
    return 0, 0

# --- Streamlit UI ---
st.title("The Attendance Lifeline 📚")
st.caption("Calculate the minimum classes needed to meet your attendance goal.")

col1, col2, col3 = st.columns(3)

with col1:
    classes_attended = st.number_input("Classes Attended (Current)", min_value=0, value=10, step=1)
with col2:
    total_classes = st.number_input("Total Classes Conducted", min_value=1, value=15, step=1)
with col3:
    required_percentage = st.number_input("Required Percentage (%)", min_value=0.0, max_value=100.0, value=75.0, step=0.5, format="%.1f")

st.markdown("---")

if st.button("Calculate Attendance Goal"):
    if classes_attended > total_classes:
        st.error("🚨 Error: Classes Attended cannot be greater than Total Classes Conducted.")
    elif total_classes == 0:
        st.error("🚨 Error: Total Classes Conducted must be greater than zero.")
    else:
        x_min, current_percent, projected_percent = calculate_required_classes(
            classes_attended, total_classes, required_percentage
        )

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("Your Current Status")
        st.markdown(f"Your Current Attendance: <span class='current-percent'>{current_percent:.2f}%</span>", unsafe_allow_html=True)

        st.subheader("Action Plan")

        if x_min == 0:
            st.success(f"🎉 Great news! Your current attendance is *{current_percent:.2f}%*, which already meets or exceeds the required *{required_percentage:.1f}%*.")
        elif x_min == -1:
            st.error(f"🛑 IMPOSSIBLE: To achieve *100.00%* attendance, you must have attended all classes conducted. Since your current attendance is *{current_percent:.2f}%*, you cannot reach this target.")
        else:
            st.warning(f"To reach the required *{required_percentage:.1f}%*, you must attend a minimum of **{x_min}** consecutive additional classes. This will bring your attendance to *{projected_percent:.2f}%*.")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Planning Ahead Insight ---
        missable_classes, future_window = calculate_max_missable_classes(
            classes_attended, total_classes, required_percentage
        )

        if missable_classes > 0:
            st.info(f"✨ Planning Ahead: If you attend the next **{future_window}** classes, you can afford to miss up to **{missable_classes}** of them and still maintain *{required_percentage:.1f}%* attendance.")
        else:
            st.info(f"⚠️ Heads-up: For the next few classes, you’ll need perfect attendance to reach your goal. No misses allowed yet!")

        # --- Visualization: Current vs. Target ---
        st.subheader("Visualization: Current vs. Target")

        df = pd.DataFrame({
            'Metric': ['Current Attendance', 'Required Target'],
            'Percentage': [current_percent, required_percentage],
            'Color': ['Current Attendance', 'Required Target']
        })

        df['Percentage'] = df['Percentage'].clip(upper=100)

        fig = px.bar(
            df,
            x='Percentage',
            y='Metric',
            orientation='h',
            color='Metric',
            color_discrete_map={
                'Current Attendance': '#10B981',
                'Required Target': '#FBBF24'
            },
            text='Percentage',
            height=250
        )

        fig.update_layout(
            xaxis=dict(range=[0, 100], title=None, showgrid=False),
            yaxis=dict(title=None),
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            showlegend=False,
            margin=dict(l=20, r=20, t=30, b=0)
        )

        fig.update_traces(texttemplate='%{x:.2f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        # --- New Line Chart: Missable Classes Over Time ---
        st.subheader("How Flexible Can You Be?")
        future_classes_range = list(range(1, 31))
        missable_data = []

        for x in future_classes_range:
            m = x - ((required_percentage / 100.0 * (total_classes + x)) - classes_attended)
            m_int = math.floor(m)
            missable_data.append(max(0, m_int))

        missable_df = pd.DataFrame({
            'Future Classes Planned': future_classes_range,
            'Max Missable Classes': missable_data
        })

        fig_missable = px.line(
            missable_df,
            x='Future Classes Planned',
            y='Max Missable Classes',
            markers=True,
            title="Missable Classes vs. Future Attendance Window",
            labels={
                'Future Classes Planned': 'Future Classes You Plan to Attend',
                'Max Missable Classes': 'Classes You Can Miss'
            },
            height=400
        )

        fig_missable.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig_missable, use_container_width=True)
        st.caption("📈 The more classes you commit to attending, the more flexibility you gain.")

# Footer
st.markdown("---")
st.info(
    "💡 *How the Math Works:* The calculator uses a direct algebraic solution derived from the "
    "inequality $\\frac{C_{att} + x}{C_{total} + x} \\ge \\frac{P_{req}}{100}$, "
    "finding the smallest whole number $x$ that satisfies the condition."
)
