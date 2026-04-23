import streamlit as st

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        display: none;
    }
    [data-testid="stToolbar"] {
        display: none;
    }
    .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

navigation = st.navigation(
    [
        st.Page("pages/0_Graphs.py", title="Graphs"),
        st.Page("pages/1_Universe_Analysis.py", title="Universe Analysis"),
        st.Page("pages/2_Stock_Screener.py", title="Stock Screener"),
        st.Page("pages/3_Volatility.py", title="Volatility"),
    ]
)

navigation.run()
